"""
Plain CRUD for complaints:
  POST   /api/complaints            create a new blank draft
  GET    /api/complaints            list all (this is your "QMS Ledger" view)
  GET    /api/complaints/{id}       fetch one
  POST   /api/complaints/{id}/commit   mark as committed to the ledger
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Complaint
from app.schemas import ComplaintOut, ComplaintFields

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def _to_out(c: Complaint) -> ComplaintOut:
    return ComplaintOut(
        id=c.id,
        status=c.status,
        fields=ComplaintFields(**c.as_fields_dict()),
        chat_log=c.chat_log or [],
        created_at=c.created_at,
    )


@router.post("", response_model=ComplaintOut)
def create_complaint(db: Session = Depends(get_db)):
    complaint = Complaint()
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return _to_out(complaint)


@router.get("", response_model=list[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).order_by(Complaint.created_at.desc()).all()
    return [_to_out(c) for c in complaints]


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    return _to_out(complaint)


@router.post("/{complaint_id}/commit", response_model=ComplaintOut)
def commit_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    complaint.status = "committed"
    db.commit()
    db.refresh(complaint)
    return _to_out(complaint)
