"""Court case model — judicial proceedings."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String, Numeric, Date, DateTime, Text, Boolean,
    ForeignKey, Index, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CourtCase(Base):
    __tablename__ = "court_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    debtor_id: Mapped[int] = mapped_column(ForeignKey("debtors.id"), nullable=False)

    # Identification
    case_number: Mapped[Optional[str]] = mapped_column(String(100))
    case_number_normalized: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    case_number_source: Mapped[Optional[str]] = mapped_column(String(50))
    court_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courts.id"))
    court_name: Mapped[Optional[str]] = mapped_column(String(255))
    court_region: Mapped[Optional[str]] = mapped_column(String(100))
    judge_id: Mapped[Optional[int]] = mapped_column(ForeignKey("judges.id"))
    judge_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Process dates
    filing_date: Mapped[Optional[date]] = mapped_column(Date)
    opening_ruling_date: Mapped[Optional[date]] = mapped_column(Date)
    first_hearing_date: Mapped[Optional[date]] = mapped_column(Date)
    last_hearing_date: Mapped[Optional[date]] = mapped_column(Date)
    decision_date: Mapped[Optional[date]] = mapped_column(Date)
    decision_effective_date: Mapped[Optional[date]] = mapped_column(Date)

    # Proceeding type
    proceeding_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_default_judgment: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_short_form: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_simplified: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Claimed amounts
    claimed_principal: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_interest: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_penalty: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_3percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_index_625: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_inflation: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_court_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_legal_aid: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_other: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claimed_total_raw: Mapped[Optional[str]] = mapped_column(Text)

    # Awarded amounts (from resolution part only)
    awarded_principal: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_interest: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_penalty: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_3percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_index_625: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_inflation: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_court_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_legal_aid: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_other: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    awarded_total_raw: Mapped[Optional[str]] = mapped_column(Text)

    # Decision analytics
    award_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    decision_outcome: Mapped[Optional[str]] = mapped_column(String(50))
    reduction_reasons: Mapped[Optional[dict]] = mapped_column(JSONB)

    # AI and references
    ai_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100))
    ai_needs_review: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    ai_review_reason: Mapped[Optional[str]] = mapped_column(Text)
    extraction_version: Mapped[Optional[str]] = mapped_column(String(20))
    last_extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verdict_registry_id: Mapped[Optional[str]] = mapped_column(String(50))
    verdict_registry_url: Mapped[Optional[str]] = mapped_column(String(500))
    deanonymized: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    deanonymization_source: Mapped[Optional[str]] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    debtor: Mapped["Debtor"] = relationship(back_populates="court_cases")
    rulings: Mapped[List["CourtRuling"]] = relationship(back_populates="case", lazy="selectin")
    financials_evidence: Mapped[List["CaseFinancialsEvidence"]] = relationship(
        back_populates="case", lazy="selectin"
    )
    enforcement_proceedings: Mapped[List["EnforcementProceeding"]] = relationship(
        back_populates="case", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_court_cases_debtor_id", "debtor_id"),
        Index("ix_court_cases_decision_outcome", "decision_outcome"),
        Index("ix_court_cases_court_name", "court_name"),
    )

    def __repr__(self) -> str:
        return f"<CourtCase(id={self.id}, case='{self.case_number}')>"
