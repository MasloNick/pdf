"""Court case Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CourtCaseBase(BaseModel):
    case_number: Optional[str] = None
    court_name: Optional[str] = None
    court_region: Optional[str] = None
    judge_name: Optional[str] = None
    filing_date: Optional[date] = None
    proceeding_type: Optional[str] = None
    decision_outcome: Optional[str] = None


class CourtCaseCreate(CourtCaseBase):
    debtor_id: int


class CourtCaseResponse(CourtCaseBase):
    id: int
    debtor_id: int
    case_number_normalized: Optional[str] = None
    opening_ruling_date: Optional[date] = None
    decision_date: Optional[date] = None
    decision_effective_date: Optional[date] = None

    # Claimed
    claimed_principal: Optional[Decimal] = None
    claimed_total: Optional[Decimal] = None

    # Awarded
    awarded_principal: Optional[Decimal] = None
    awarded_total: Optional[Decimal] = None
    award_ratio: Optional[Decimal] = None

    # AI
    ai_confidence: Optional[Decimal] = None
    ai_needs_review: Optional[bool] = None
    verdict_registry_url: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourtCaseListResponse(BaseModel):
    items: list[CourtCaseResponse]
    total: int
    page: int
    page_size: int
