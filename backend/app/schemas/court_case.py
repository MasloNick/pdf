"""Court case schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class CourtCaseCreate(BaseModel):
    debtor_id: int
    portfolio_debtor_link_id: int | None = None
    case_number: str
    court_name: str
    judge_name: str | None = None
    proceeding_type: str
    claim_amount: Decimal | None = None
    court_fee: Decimal | None = None
    filing_date: date | None = None
    notes: str | None = None


class CourtCaseUpdate(BaseModel):
    status: str | None = None
    current_stage: str | None = None
    judge_name: str | None = None
    decision_date: date | None = None
    decision_type: str | None = None
    awarded_amount: Decimal | None = None
    notes: str | None = None


class CourtCaseResponse(BaseModel):
    id: int
    debtor_id: int
    case_number: str
    court_name: str
    judge_name: str | None
    proceeding_type: str
    claim_amount: Decimal | None
    court_fee: Decimal | None
    filing_date: date | None
    status: str
    current_stage: str | None
    decision_date: date | None
    decision_type: str | None
    awarded_amount: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CourtDecisionResponse(BaseModel):
    id: int
    court_case_id: int
    reyestr_id: str | None
    decision_date: date | None
    decision_type: str | None
    outcome: str | None
    awarded_total: Decimal | None
    awarded_principal: Decimal | None
    awarded_interest: Decimal | None
    awarded_penalties: Decimal | None
    awarded_court_fee: Decimal | None
    confidence: float | None
    needs_review: bool
    parse_method: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
