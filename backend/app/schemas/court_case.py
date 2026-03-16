"""Court case schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.court_case import CaseStatus, CaseType


class CourtCaseCreate(BaseModel):
    debtor_id: uuid.UUID
    case_number: str = Field(..., max_length=100)
    case_type: CaseType
    court_name: str = Field(..., max_length=500)
    court_code: str | None = None
    judge_name: str | None = None
    claim_amount: Decimal = Field(..., ge=0)
    court_fee_amount: Decimal | None = None
    filing_date: date | None = None
    hearing_date: date | None = None
    party_replacement_needed: bool = False
    notes: str | None = None


class CourtCaseUpdate(BaseModel):
    status: CaseStatus | None = None
    judge_name: str | None = None
    claim_amount: Decimal | None = None
    awarded_amount: Decimal | None = None
    hearing_date: date | None = None
    decision_date: date | None = None
    party_replacement_status: str | None = None
    party_replacement_date: date | None = None
    notes: str | None = None


class CourtCaseOut(BaseModel):
    id: uuid.UUID
    debtor_id: uuid.UUID
    case_number: str
    case_type: CaseType
    status: CaseStatus
    court_name: str
    court_code: str | None
    judge_name: str | None
    claim_amount: Decimal
    court_fee_amount: Decimal | None
    awarded_amount: Decimal | None
    filing_date: date | None
    hearing_date: date | None
    decision_date: date | None
    party_replacement_needed: bool
    party_replacement_status: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
