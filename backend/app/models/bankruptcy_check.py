"""Bankruptcy check model."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Numeric, Date, DateTime, Text, Boolean,
    ForeignKey, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BankruptcyCheck(Base):
    __tablename__ = "bankruptcy_checks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    debtor_id: Mapped[int] = mapped_column(ForeignKey("debtors.id"), unique=True, nullable=False)

    # ЄДРБ (ERB)
    erb_found: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    erb_entry_date: Mapped[Optional[date]] = mapped_column(Date)
    erb_creditor: Mapped[Optional[str]] = mapped_column(String(255))
    erb_amount_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    erb_last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # КУзПБ (Bankruptcy Code)
    bankruptcy_found: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    bankruptcy_case_number: Mapped[Optional[str]] = mapped_column(String(100))
    bankruptcy_court: Mapped[Optional[str]] = mapped_column(String(255))
    bankruptcy_stage: Mapped[Optional[str]] = mapped_column(String(50))
    bankruptcy_open_date: Mapped[Optional[date]] = mapped_column(Date)
    bankruptcy_outcome: Mapped[Optional[str]] = mapped_column(String(50))

    # Impact on FC
    vp_suspended: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    vp_suspension_date: Mapped[Optional[date]] = mapped_column(Date)
    claims_filing_deadline: Mapped[Optional[date]] = mapped_column(Date)
    claims_filed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    claims_amount_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    claims_filing_date: Mapped[Optional[date]] = mapped_column(Date)
    claims_status: Mapped[Optional[str]] = mapped_column(String(50))

    # Alerts
    alert_sent: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    alert_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    alert_type: Mapped[Optional[str]] = mapped_column(String(50))
    needs_manual_review: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    last_sync_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    debtor: Mapped["Debtor"] = relationship(back_populates="bankruptcy_check")

    def __repr__(self) -> str:
        return f"<BankruptcyCheck(id={self.id}, debtor_id={self.debtor_id})>"
