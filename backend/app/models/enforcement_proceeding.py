"""Enforcement proceeding model."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Numeric, Date, DateTime, Text, Boolean,
    ForeignKey, Index, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class EnforcementProceeding(Base):
    __tablename__ = "enforcement_proceedings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("court_cases.id"))
    debtor_id: Mapped[int] = mapped_column(ForeignKey("debtors.id"), nullable=False)

    vp_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    executor_name: Mapped[Optional[str]] = mapped_column(String(255))
    executor_type: Mapped[Optional[str]] = mapped_column(String(20))
    executor_region: Mapped[Optional[str]] = mapped_column(String(100))
    executor_edrpou: Mapped[Optional[str]] = mapped_column(String(10))

    # Dates
    open_date: Mapped[Optional[date]] = mapped_column(Date)
    close_date: Mapped[Optional[date]] = mapped_column(Date)
    execution_date: Mapped[Optional[date]] = mapped_column(Date)
    suspension_date: Mapped[Optional[date]] = mapped_column(Date)

    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), default="active")
    closure_reason: Mapped[Optional[str]] = mapped_column(Text)
    closure_basis_article: Mapped[Optional[str]] = mapped_column(String(100))

    # Party change
    party_change_required: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    party_change_submitted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    party_change_status: Mapped[Optional[str]] = mapped_column(String(50))
    party_change_ruling_date: Mapped[Optional[date]] = mapped_column(Date)
    previous_plaintiff: Mapped[Optional[str]] = mapped_column(String(255))
    new_plaintiff: Mapped[Optional[str]] = mapped_column(String(255))

    # Financials
    vp_claimed_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    vp_recovered_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    vp_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # ASVP sync
    asvp_last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    asvp_data_raw: Mapped[Optional[dict]] = mapped_column(JSONB)

    # ERB match
    erb_entry_confirmed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    erb_amount_match: Mapped[Optional[bool]] = mapped_column(Boolean)
    erb_amount_difference: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    case: Mapped[Optional["CourtCase"]] = relationship(back_populates="enforcement_proceedings")
    debtor: Mapped["Debtor"] = relationship(back_populates="enforcement_proceedings")

    __table_args__ = (
        Index("ix_enforcement_proceedings_debtor_id", "debtor_id"),
        Index("ix_enforcement_proceedings_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<EnforcementProceeding(id={self.id}, vp='{self.vp_number}')>"
