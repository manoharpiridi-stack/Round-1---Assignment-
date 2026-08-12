"""
One table: `complaints`. Every field the AI extracts maps 1:1 to a
column here, and 1:1 to a field in the React form. If you add a field
to FORM_FIELDS in agent.py, add the matching column here too.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


def new_uuid():
    return str(uuid.uuid4())


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)

    # --- 1. Origin & Customer Details ---
    complaint_source = Column(String(120), default="")
    customer_name = Column(String(255), default="")

    # --- 2. Product & Batch Identification ---
    product_name = Column(String(255), default="")
    product_strength = Column(String(120), default="")
    batch_lot_number = Column(String(120), default="")
    affected_quantity = Column(String(120), default="")
    manufacturing_date = Column(String(60), default="")
    expiry_date = Column(String(60), default="")

    # --- 3. Facility & Material Impact ---
    originating_site_block = Column(String(120), default="")
    impacted_npm = Column(String(255), default="")

    # --- 4. Defect Analysis ---
    complaint_category = Column(String(255), default="")
    complaint_description = Column(Text, default="")

    # --- AI Copilot Risk Assessment ---
    severity = Column(String(60), default="")
    suggested_next_action = Column(String(255), default="")
    initial_risk_assessment = Column(Text, default="")

    # --- Bonus AI features (all optional per the assignment) ---
    completeness_note = Column(Text, default="")     # Complaint Completeness Checker
    root_cause_note = Column(Text, default="")        # Root Cause Recommendation
    capa_recommendation = Column(Text, default="")     # CAPA Recommendation
    ai_summary = Column(Text, default="")               # Complaint Summary
    duplicate_warning = Column(Text, default="")         # Duplicate Complaint Detection

    # --- Bookkeeping ---
    status = Column(String(30), default="pending_triage")  # pending_triage | ready_to_commit | committed
    raw_source_text = Column(Text, default="")  # the pasted text / PDF text we extracted from
    chat_log = Column(JSON, default=list)  # [{role: "user"|"assistant", content: "..."}]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def as_fields_dict(self) -> dict:
        """The subset of columns that represent the *form fields* (used
        as the 'existing_fields' the correction step edits)."""
        return {
            "complaint_source": self.complaint_source,
            "customer_name": self.customer_name,
            "product_name": self.product_name,
            "product_strength": self.product_strength,
            "batch_lot_number": self.batch_lot_number,
            "affected_quantity": self.affected_quantity,
            "manufacturing_date": self.manufacturing_date,
            "expiry_date": self.expiry_date,
            "originating_site_block": self.originating_site_block,
            "impacted_npm": self.impacted_npm,
            "complaint_category": self.complaint_category,
            "complaint_description": self.complaint_description,
            "severity": self.severity,
            "suggested_next_action": self.suggested_next_action,
            "initial_risk_assessment": self.initial_risk_assessment,
            "completeness_note": self.completeness_note,
            "root_cause_note": self.root_cause_note,
            "capa_recommendation": self.capa_recommendation,
            "ai_summary": self.ai_summary,
            "duplicate_warning": self.duplicate_warning,
        }
