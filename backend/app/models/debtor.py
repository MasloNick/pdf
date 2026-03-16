"""Debtor model — up to 50,000 records."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DebtorType(StrEnum):
    INDIVIDUAL = "individual"
    LEGAL_ENTITY = "legal_entity"
    ENTREPRENEUR = "entrepreneur"


class DebtorStatus(StrEnum):
    NEW = "new"
    IN_COURT = "in_court"
    JUDGMENT_OBTAINED = "judgment_obtained"
    ENFORCEMENT = "enforcement"
    PARTIALLY_RECOVERED = "partially_recovered"
    FULLY_RECOVERED = "fully_recovered"
    BANKRUPT = "bankrupt"
    WRITTEN_OFF = "written_off"


class Debtor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "debtors"

    # ── Portfolio link ───────────────────────────────────────
    portfolio_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False
    )

    # ── Identification ───────────────────────────────────────
    debtor_type: Mapped[DebtorType] = mapped_column(
        Enum(DebtorType, name="debtor_type_enum"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    ipn_code: Mapped[str | None] = mapped_column(
        String(10), index=True, comment="ІПН / ЄДРПОУ"
    )
    passport_series: Mapped[str | None] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)

    # ── Address ──────────────────────────────────────────────
    registration_address: Mapped[str | None] = mapped_column(Text)
    actual_address: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(100))

    # ── Contact ──────────────────────────────────────────────
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))

    # ── Debt ─────────────────────────────────────────────────
    original_debt_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    current_debt_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="UAH")
    original_creditor: Mapped[str | None] = mapped_column(String(255))
    original_contract_number: Mapped[str | None] = mapped_column(String(100))
    original_contract_date: Mapped[date | None] = mapped_column(Date)

    # ── Status ───────────────────────────────────────────────
    status: Mapped[DebtorStatus] = mapped_column(
        Enum(DebtorStatus, name="debtor_status_enum"),
        default=DebtorStatus.NEW,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # ── Relationships ────────────────────────────────────────
    portfolio: Mapped["Portfolio"] = relationship(back_populates="debtors")  # noqa: F821
    court_cases: Mapped[list["CourtCase"]] = relationship(  # noqa: F821
        back_populates="debtor", cascade="all, delete-orphan"
    )
    registry_checks: Mapped[list["RegistryCheck"]] = relationship(  # noqa: F821
        back_populates="debtor", cascade="all, delete-orphan"
    )
    bankruptcy_checks: Mapped[list["BankruptcyCheck"]] = relationship(  # noqa: F821
        back_populates="debtor", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_debtors_full_name_trgm", "full_name", postgresql_using="gin"),
        Index("ix_debtors_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Debtor {self.full_name}>"
