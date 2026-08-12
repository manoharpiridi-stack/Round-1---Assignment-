"""
Pydantic models = the shape of JSON going in/out of the API.
Kept intentionally close to the ORM model in models.py.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ComplaintFields(BaseModel):
    complaint_source: str = ""
    customer_name: str = ""
    product_name: str = ""
    product_strength: str = ""
    batch_lot_number: str = ""
    affected_quantity: str = ""
    manufacturing_date: str = ""
    expiry_date: str = ""
    originating_site_block: str = ""
    impacted_npm: str = ""
    complaint_category: str = ""
    complaint_description: str = ""
    severity: str = ""
    suggested_next_action: str = ""
    initial_risk_assessment: str = ""
    completeness_note: str = ""
    root_cause_note: str = ""
    capa_recommendation: str = ""
    ai_summary: str = ""
    duplicate_warning: str = ""


class ChatMessage(BaseModel):
    role: str
    content: str


class ComplaintOut(BaseModel):
    id: str
    status: str
    fields: ComplaintFields
    chat_log: list[ChatMessage]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExtractRequest(BaseModel):
    """Used for the 'paste text' path. File uploads use multipart form
    data instead (see routers/copilot.py)."""
    complaint_id: str
    text: str


class CorrectRequest(BaseModel):
    complaint_id: str
    message: str


class BonusToolRequest(BaseModel):
    """Used by all five bonus feature endpoints - they only ever need
    to know which complaint to act on."""
    complaint_id: str


class CopilotResponse(BaseModel):
    reply: str
    fields: ComplaintFields
    status: str
    changed_fields: list[str] = []
