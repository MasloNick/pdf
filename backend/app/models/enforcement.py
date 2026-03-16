"""Enforcement proceeding (виконавче провадження) model."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EnforcementStatus(StrEnum):
    PENDING_SUBMISSION = "pending_submission"
    SUBMITTED = "submitted"
    OPENED = "opened"
    IN_PROGRESS = "in_progress"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    RETURNED = "returned"
    CLOSED = "closed"


class EnforcementProceeding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "enforcement_proceedings"

    court_case_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("court_cases.id"), nullable=False
    )

    # ── Identifiers ──────────────────────────────────────────
    enforcement_number: Mapped[str | None] = mapped_column(
        String(100), index=True
    )
    executor_name: Mapped[str | None] = mapped_column(String(255))
    executor_office: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[EnforcementStatus] = mapped_column(
        Enum(EnforcementStatus, name="enforcement_status_enum"),
        default=EnforcementStatus.PENDING_SUBMISSION,
    )

    # ── Financial ────────────────────────────────────────────
    total_debt_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    recovered_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), default=0
    )

    # ── Dates ────────────────────────────────────────────────
    submission_date: Mapped[date | None] = mapped_column(Date)
    opening_date: Mapped[date | None] = mapped_column(Date)
    completion_date: Mapped[date | None] = mapped_column(Date)

    # ── Party replacement tracking ───────────────────────────
    party_replacement_filed: Mapped[bool] = mapped_column(default=False)
    party_replacement_date: Mapped[date | None] = mapped_column(Date)
    party_replacement_granted: Mapped[bool | None] = mapped_column()

    notes: Mapped[str | None] = mapped_column(Text)

    court_case: Mapped["CourtCase"] = relationship(  # noqa: F821
        back_populates="enforcement_proceedings"
    )

    def __repr__(self) -> str:
        return f"<Enforcement {self.enforcement_number}>"
