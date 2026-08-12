"""
This is the router the "AIVOA Copilot" chat panel talks to.

Main path (matches the demo video):
  POST /api/copilot/extract-text   { complaint_id, text }         -> paste-text path
  POST /api/copilot/extract-file   multipart file + complaint_id  -> PDF upload path
  POST /api/copilot/correct        { complaint_id, message }      -> follow-up correction path

Bonus AI features (all optional per the assignment, all take just
{ complaint_id }):
  POST /api/copilot/check-completeness  -> Complaint Completeness Checker
  POST /api/copilot/root-cause          -> Root Cause Recommendation
  POST /api/copilot/capa                -> CAPA Recommendation
  POST /api/copilot/summary             -> Complaint Summary
  POST /api/copilot/duplicates          -> Duplicate Complaint Detection

Every one of these ends up calling the same compiled LangGraph graph
(app.agent.copilot_graph) with a different `mode`, then saves the
result back onto the Complaint row and appends to its chat_log so the
conversation survives a page refresh.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Complaint
from app.schemas import ExtractRequest, CorrectRequest, BonusToolRequest, CopilotResponse, ComplaintFields
from app.agent import copilot_graph
from app.pdf_utils import extract_text_from_pdf

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

# Which DB column each bonus mode's reply gets saved into.
BONUS_FIELD_MAP = {
    "completeness": "completeness_note",
    "root_cause": "root_cause_note",
    "capa": "capa_recommendation",
    "summary": "ai_summary",
    "duplicate": "duplicate_warning",
}


def _get_complaint_or_404(db: Session, complaint_id: str) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    return complaint


def _log_and_respond(db: Session, complaint: Complaint, reply: str, user_message: str, changed_fields: list) -> CopilotResponse:
    chat_log = list(complaint.chat_log or [])
    if user_message:
        chat_log.append({"role": "user", "content": user_message})
    chat_log.append({"role": "assistant", "content": reply})
    complaint.chat_log = chat_log
    db.commit()
    db.refresh(complaint)

    return CopilotResponse(
        reply=reply,
        fields=ComplaintFields(**complaint.as_fields_dict()),
        status=complaint.status,
        changed_fields=changed_fields,
    )


# ---------------------------------------------------------------------
# Main path: extract / correct
# ---------------------------------------------------------------------

@router.post("/extract-text", response_model=CopilotResponse)
def extract_text(body: ExtractRequest, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, body.complaint_id)
    complaint.raw_source_text = body.text

    result = copilot_graph.invoke({"mode": "extract", "raw_input": body.text})
    for key, value in result["fields"].items():
        setattr(complaint, key, value)
    complaint.status = "ready_to_commit"
    return _log_and_respond(db, complaint, result["reply"], body.text, result.get("changed_fields", []))


@router.post("/extract-file", response_model=CopilotResponse)
async def extract_file(
    complaint_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    complaint = _get_complaint_or_404(db, complaint_id)
    file_bytes = await file.read()
    text = extract_text_from_pdf(file_bytes)
    complaint.raw_source_text = text

    result = copilot_graph.invoke({"mode": "extract", "raw_input": text})
    for key, value in result["fields"].items():
        setattr(complaint, key, value)
    complaint.status = "ready_to_commit"
    return _log_and_respond(db, complaint, result["reply"], f"[Uploaded file: {file.filename}]", result.get("changed_fields", []))


@router.post("/correct", response_model=CopilotResponse)
def correct(body: CorrectRequest, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, body.complaint_id)
    existing_fields = complaint.as_fields_dict()

    result = copilot_graph.invoke(
        {"mode": "correct", "message": body.message, "existing_fields": existing_fields}
    )
    for key, value in result["fields"].items():
        setattr(complaint, key, value)
    complaint.status = "ready_to_commit"
    return _log_and_respond(db, complaint, result["reply"], body.message, result.get("changed_fields", []))


# ---------------------------------------------------------------------
# Bonus AI features - each is a thin wrapper: build the graph state,
# invoke, save the reply into its dedicated column.
# ---------------------------------------------------------------------

def _run_bonus(db: Session, complaint: Complaint, mode: str, action_label: str, extra_state: dict = None) -> CopilotResponse:
    state = {"mode": mode, "fields": complaint.as_fields_dict()}
    if extra_state:
        state.update(extra_state)

    result = copilot_graph.invoke(state)
    column = BONUS_FIELD_MAP[mode]
    setattr(complaint, column, result["reply"])
    return _log_and_respond(db, complaint, result["reply"], action_label, [column])


@router.post("/check-completeness", response_model=CopilotResponse)
def check_completeness(body: BonusToolRequest, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, body.complaint_id)
    return _run_bonus(db, complaint, "completeness", "🔍 Check Completeness")


@router.post("/root-cause", response_model=CopilotResponse)
def root_cause(body: BonusToolRequest, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, body.complaint_id)
    return _run_bonus(db, complaint, "root_cause", "🧭 Suggest Root Cause")


@router.post("/capa", response_model=CopilotResponse)
def capa(body: BonusToolRequest, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, body.complaint_id)
    return _run_bonus(db, complaint, "capa", "🛠️ Recommend CAPA")


@router.post("/summary", response_model=CopilotResponse)
def summary(body: BonusToolRequest, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, body.complaint_id)
    return _run_bonus(db, complaint, "summary", "📝 Summarize Complaint")


@router.post("/duplicates", response_model=CopilotResponse)
def duplicates(body: BonusToolRequest, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, body.complaint_id)
    others = db.query(Complaint).filter(Complaint.id != complaint.id).all()
    other_complaints = [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "batch_lot_number": o.batch_lot_number,
            "product_name": o.product_name,
            "complaint_category": o.complaint_category,
        }
        for o in others
    ]
    return _run_bonus(db, complaint, "duplicate", "🔁 Check Duplicates", extra_state={"other_complaints": other_complaints})
