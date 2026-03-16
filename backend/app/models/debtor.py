"""Debtor model — central entity table."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String, Numeric, Integer, Date, DateTime, Text, Boolean,
    ForeignKey, Index, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Debtor(Base):
    __tablename__ = "debtors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), nullable=False)

    # Personal data
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    ipn: Mapped[Optional[str]] = mapped_column(String(10), unique=True, index=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    birth_place: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[str]] = mapped_column(String(10))

    # Documents
    passport_series: Mapped[Optional[str]] = mapped_column(String(10))
    passport_number: Mapped[Optional[str]] = mapped_column(String(20))
    passport_issuer: Mapped[Optional[str]] = mapped_column(String(255))
    passport_issue_date: Mapped[Optional[date]] = mapped_column(Date)
    id_card_number: Mapped[Optional[str]] = mapped_column(String(20))
    id_card_issuer: Mapped[Optional[str]] = mapped_column(String(255))
    id_card_expiry: Mapped[Optional[date]] = mapped_column(Date)

    # Addresses
    registration_address_raw: Mapped[Optional[str]] = mapped_column(Text)
    registration_address_normalized: Mapped[Optional[str]] = mapped_column(Text)
    actual_address_raw: Mapped[Optional[str]] = mapped_column(Text)
    actual_address_normalized: Mapped[Optional[str]] = mapped_column(Text)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    settlement: Mapped[Optional[str]] = mapped_column(String(255))
    street: Mapped[Optional[str]] = mapped_column(String(255))
    building: Mapped[Optional[str]] = mapped_column(String(50))
    apartment: Mapped[Optional[str]] = mapped_column(String(50))
    address_norm_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))

    # Contacts
    phone_primary: Mapped[Optional[str]] = mapped_column(String(20))
    phone_secondary: Mapped[Optional[str]] = mapped_column(String(20))
    phone_other: Mapped[Optional[dict]] = mapped_column(JSONB)
    email: Mapped[Optional[str]] = mapped_column(String(255))

    # Credit case
    credit_contract_number: Mapped[Optional[str]] = mapped_column(String(100))
    credit_contract_date: Mapped[Optional[date]] = mapped_column(Date)
    original_creditor: Mapped[Optional[str]] = mapped_column(String(255))
    product_type: Mapped[Optional[str]] = mapped_column(String(100))

    # Financials at purchase
    purchased_principal_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    purchased_interest_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    purchased_penalty_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    purchased_court_fee_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    purchased_other_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    purchased_total_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # Status and registries
    collection_status: Mapped[Optional[str]] = mapped_column(
        String(50), default="active_court"
    )
    responsible_lawyer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    in_erb: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    erb_last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    in_bankruptcy: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    bankruptcy_last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="debtors")
    court_cases: Mapped[List["CourtCase"]] = relationship(back_populates="debtor", lazy="selectin")
    enforcement_proceedings: Mapped[List["EnforcementProceeding"]] = relationship(
        back_populates="debtor", lazy="selectin"
    )
    bankruptcy_check: Mapped[Optional["BankruptcyCheck"]] = relationship(
        back_populates="debtor", uselist=False, lazy="selectin"
    )

    __table_args__ = (
        Index("ix_debtors_portfolio_id", "portfolio_id"),
        Index("ix_debtors_full_name", "full_name"),
        Index("ix_debtors_collection_status", "collection_status"),
    )

    def __repr__(self) -> str:
        return f"<Debtor(id={self.id}, name='{self.full_name}', ipn='{self.ipn}')>"
