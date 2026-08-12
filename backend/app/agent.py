                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        `"""
The whole AI Copilot is one LangGraph graph. It has two "main" paths
(extraction and correction, which is what the demo video shows) and
five "bonus" paths — one per optional AI feature from the assignment
brief. All seven share the same compose_reply node at the end.

    START
      |
      +--(mode == "extract")-----> extract_fields -----+
      +--(mode == "correct")-----> apply_correction ----+--> assess_risk --> compose_reply --> END
      |                                                  |
      +--(mode == "completeness")--> check_completeness -+
      +--(mode == "root_cause")----> recommend_root_cause+
      +--(mode == "capa")----------> recommend_capa------+--> compose_reply --> END
      +--(mode == "summary")-------> generate_summary----+
      +--(mode == "duplicate")-----> detect_duplicates---+

Extraction/correction go through assess_risk because severity should
always reflect the latest field values. The five bonus nodes work off
fields that are already finalized, so they skip straight to
compose_reply.

TO ADD A NEW FORM FIELD: add it to FORM_FIELDS below (one line) and
add a matching column in models.py / schemas.py.

TO ADD A NEW BONUS AI FEATURE: write one function with the same shape
as the five bonus_* nodes below (read state, return
{"bonus_fields": {...}}), register it with graph.add_node(...), add it
to the _ROUTES mapping, and add graph.add_edge("your_node",
"compose_reply"). Then teach compose_reply() how to phrase a reply for
it. That's the whole recipe — nothing else in the file needs to change.
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from app.groq_client import chat_json
from app.config import RISK_MODEL, EXTRACTION_MODEL

# key -> plain-English description shown to the LLM
FORM_FIELDS = {
    "complaint_source": "Where the complaint came from, e.g. Pharmacy, Email, Distributor",
    "customer_name": "Name of the customer / company that raised the complaint",
    "product_name": "Name of the pharmaceutical product (API or FDF)",
    "product_strength": "Strength or grade of the product, e.g. '500 mg' or 'IP/BP'",
    "batch_lot_number": "Batch or lot number of the affected product",
    "affected_quantity": "Quantity affected, including units, e.g. '12 capsules' or '25 kg (1 HDPE Drum)'",
    "manufacturing_date": "Manufacturing date as stated",
    "expiry_date": "Expiry date as stated, or 'Not Provided' if missing",
    "originating_site_block": "Which site/block the issue likely originated from: Manufacturing, Packaging, Warehouse, QC, or Distribution",
    "impacted_npm": "Any impacted non-product material, e.g. 'Primary Packaging (Bottle)'",
    "complaint_category": "Short defect category, e.g. 'Product Defect - Discoloration' or 'Foreign Matter Contamination'",
    "complaint_description": "A concise 1-2 sentence formal restatement of the complaint suitable for a QMS record",
}


class AgentState(TypedDict, total=False):
    mode: str                 # "extract" | "correct" | "completeness" | "root_cause" | "capa" | "summary" | "duplicate"
    raw_input: str            # pasted text or PDF-extracted text (extract mode)
    message: str              # user's follow-up chat message (correct mode)
    existing_fields: dict     # current form values (correct mode)
    other_complaints: list    # other complaints in the DB (duplicate mode only)
    fields: dict              # form values, read by every bonus node
    changed_fields: list      # which keys changed (correct mode)
    risk: dict                # {severity, suggested_next_action, initial_risk_assessment}
    bonus_fields: dict        # output of whichever bonus node ran
    reply: str                # chat bubble text to show the user


# =======================================================================
# Main path: extraction / correction / risk assessment
# =======================================================================

def extract_fields(state: AgentState) -> AgentState:
    schema_desc = "\n".join(f'  "{k}": "{v}"' for k, v in FORM_FIELDS.items())
    system_prompt = (
        "You are a data-extraction engine for a pharmaceutical Quality "
        "Management System. Read the complaint text and return ONLY a "
        "JSON object with exactly these keys (use \"\" for anything not "
        f"mentioned):\n{{\n{schema_desc}\n}}"
    )
    result = chat_json(system_prompt, state["raw_input"])
    fields = {k: str(result.get(k, "") or "") for k in FORM_FIELDS}
    return {"fields": fields, "changed_fields": list(FORM_FIELDS.keys())}


def apply_correction(state: AgentState) -> AgentState:
    existing = state["existing_fields"]
    system_prompt = (
        "You are updating a pharmaceutical complaint form based on a "
        "correction message from the user. You will be given the CURRENT "
        "field values as JSON and a correction message. Return ONLY a "
        "JSON object containing JUST the fields that should change, with "
        "their new values. Do not include fields that are not mentioned "
        "in the correction."
    )
    user_prompt = (
        f"Current field values:\n{existing}\n\n"
        f"Correction message: {state['message']}"
    )
    changes = chat_json(system_prompt, user_prompt)
    changes = {k: str(v) for k, v in changes.items() if k in FORM_FIELDS}
    updated = {**existing, **changes}
    return {"fields": updated, "changed_fields": list(changes.keys())}


def assess_risk(state: AgentState) -> AgentState:
    system_prompt = (
        "You are a pharmaceutical QA risk-assessment assistant. Given "
        "the complaint fields as JSON, return ONLY a JSON object with "
        "these keys: \"severity\" (one of Minor, Major, Critical), "
        "\"suggested_next_action\" (a short phrase, e.g. 'Route to QA "
        "Investigation & Issue Replacement'), and \"initial_risk_assessment\" "
        "(1-2 sentences on likely root cause and impact)."
    )
    risk = chat_json(system_prompt, str(state["fields"]), model=RISK_MODEL)
    risk = {
        "severity": risk.get("severity", ""),
        "suggested_next_action": risk.get("suggested_next_action", ""),
        "initial_risk_assessment": risk.get("initial_risk_assessment", ""),
    }
    fields = {**state["fields"], **risk}
    return {"fields": fields, "risk": risk}


# =======================================================================
# Bonus AI features (from the assignment's "Bonus Features" list)
# =======================================================================

def check_completeness(state: AgentState) -> AgentState:
    """Complaint Completeness Checker. Plain Python, no LLM call needed
    - checking for blank fields doesn't require a model, so we don't
    spend a request on it. (A good thing to point out in interview:
    reach for an LLM call only when the task actually needs judgment.)"""
    fields = state.get("fields", {})
    missing = [k for k in FORM_FIELDS if not str(fields.get(k, "")).strip()]
    return {"bonus_fields": {"completeness_missing": missing}}


def recommend_root_cause(state: AgentState) -> AgentState:
    """Root Cause Recommendation - a deeper investigative note than the
    one-liner produced by assess_risk."""
    system_prompt = (
        "You are a pharmaceutical QA investigator. Given the complaint "
        "fields as JSON, write a short root-cause analysis (2-4 "
        "sentences): the most likely cause(s), and what evidence would "
        "confirm it. Return ONLY a JSON object with key "
        "\"root_cause_analysis\"."
    )
    result = chat_json(system_prompt, str(state["fields"]), model=RISK_MODEL)
    return {"bonus_fields": {"root_cause_analysis": result.get("root_cause_analysis", "")}}


def recommend_capa(state: AgentState) -> AgentState:
    """CAPA Recommendation - one corrective action (immediate fix) and
    one preventive action (process change)."""
    system_prompt = (
        "You are a pharmaceutical QA specialist. Given the complaint "
        "fields as JSON, recommend a CAPA (Corrective and Preventive "
        "Action) plan: one corrective action and one preventive action, "
        "2-4 sentences total. Return ONLY a JSON object with key "
        "\"capa_recommendation\"."
    )
    result = chat_json(system_prompt, str(state["fields"]), model=RISK_MODEL)
    return {"bonus_fields": {"capa_recommendation": result.get("capa_recommendation", "")}}


def generate_summary(state: AgentState) -> AgentState:
    """Complaint Summary - a short formal narrative for the QMS record,
    distinct from the raw Complaint Description field."""
    system_prompt = (
        "Write a concise QMS record summary. Given the complaint fields "
        "as JSON, write a 2-3 sentence formal summary suitable for a "
        "quality record. Return ONLY a JSON object with key "
        "\"complaint_summary\"."
    )
    result = chat_json(system_prompt, str(state["fields"]), model=EXTRACTION_MODEL)
    return {"bonus_fields": {"complaint_summary": result.get("complaint_summary", "")}}


def detect_duplicates(state: AgentState) -> AgentState:
    """Duplicate Complaint Detection. Rule-based on purpose: an exact
    batch/lot match against another complaint already in the ledger is
    a hard signal and doesn't need an LLM to spot reliably. A same
    product + same category match is flagged as a softer "worth a
    human look" case. (A production version could add embedding-based
    similarity over complaint_description for fuzzier matches - noted
    here rather than built, to keep this reliable and free to run.)"""
    fields = state.get("fields", {})
    others = state.get("other_complaints", [])

    exact = [
        o for o in others
        if fields.get("batch_lot_number") and o.get("batch_lot_number") == fields.get("batch_lot_number")
    ]
    exact_ids = {o["id"] for o in exact}
    possible = [
        o for o in others
        if o["id"] not in exact_ids
        and fields.get("product_name")
        and o.get("product_name") == fields.get("product_name")
        and o.get("complaint_category") == fields.get("complaint_category")
    ]

    matches = (
        [{"id": o["id"], "customer_name": o.get("customer_name", ""), "reason": "Exact batch/lot match"} for o in exact]
        + [{"id": o["id"], "customer_name": o.get("customer_name", ""), "reason": "Same product & complaint category"} for o in possible]
    )
    return {"bonus_fields": {"duplicate_matches": matches}}


def compose_reply(state: AgentState) -> AgentState:
    """Deterministic, template-based reply for every mode - no extra
    LLM call needed. Keeps responses fast, cheap, and predictable."""
    mode = state["mode"]

    if mode == "extract":
        product = state["fields"].get("product_name") or "the product"
        category = state["fields"].get("complaint_category") or "the issue"
        reply = (
            f"Complaint parsed successfully. I've extracted the details for "
            f"{product} and identified the issue as {category}. "
            f"Suggested severity: {state['risk'].get('severity', 'n/a')}."
        )

    elif mode == "correct":
        changed = state.get("changed_fields", [])
        if changed:
            parts = ", ".join(f'"{c}" to "{state["fields"].get(c, "")}"' for c in changed)
            reply = f"Got it. I've updated {parts} in the form."
        else:
            reply = "I didn't find a field to update from that message - could you rephrase?"

    elif mode == "completeness":
        missing = state["bonus_fields"]["completeness_missing"]
        reply = (
            f"Completeness check: {len(missing)} field(s) still need attention - " + ", ".join(missing) + "."
            if missing else
            "Completeness check: every field is filled in. This complaint is ready for review."
        )

    elif mode == "root_cause":
        reply = "Root cause analysis: " + state["bonus_fields"]["root_cause_analysis"]

    elif mode == "capa":
        reply = "CAPA recommendation: " + state["bonus_fields"]["capa_recommendation"]

    elif mode == "summary":
        reply = state["bonus_fields"]["complaint_summary"]

    elif mode == "duplicate":
        matches = state["bonus_fields"]["duplicate_matches"]
        if matches:
            named = ", ".join(f'{m["customer_name"] or "a complaint"} ({m["reason"]})' for m in matches)
            reply = f"Found {len(matches)} potential duplicate(s) in the ledger: {named}."
        else:
            reply = "No potential duplicates found among existing complaints."

    else:
        reply = "Unrecognized request."

    return {"reply": reply}


# =======================================================================
# Graph wiring
# =======================================================================

_ROUTES = {
    "extract": "extract_fields",
    "correct": "apply_correction",
    "completeness": "check_completeness",
    "root_cause": "recommend_root_cause",
    "capa": "recommend_capa",
    "summary": "generate_summary",
    "duplicate": "detect_duplicates",
}


def _route(state: AgentState) -> str:
    return _ROUTES[state["mode"]]


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("extract_fields", extract_fields)
    graph.add_node("apply_correction", apply_correction)
    graph.add_node("assess_risk", assess_risk)
    graph.add_node("check_completeness", check_completeness)
    graph.add_node("recommend_root_cause", recommend_root_cause)
    graph.add_node("recommend_capa", recommend_capa)
    graph.add_node("generate_summary", generate_summary)
    graph.add_node("detect_duplicates", detect_duplicates)
    graph.add_node("compose_reply", compose_reply)

    # _route() already resolves mode -> node name (via _ROUTES), so the
    # map here just needs to send every possible node name to itself.
    graph.add_conditional_edges(START, _route, {node: node for node in _ROUTES.values()})

    # Main path: both go through risk assessment first.
    graph.add_edge("extract_fields", "assess_risk")
    graph.add_edge("apply_correction", "assess_risk")
    graph.add_edge("assess_risk", "compose_reply")

    # Bonus path: straight to the reply, no risk re-assessment needed.
    for node in ["check_completeness", "recommend_root_cause", "recommend_capa",
                 "generate_summary", "detect_duplicates"]:
        graph.add_edge(node, "compose_reply")

    graph.add_edge("compose_reply", END)
    return graph.compile()


# Compiled once at import time and reused for every request.
copilot_graph = build_graph()
