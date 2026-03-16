"""Batch bankruptcy check results with alerts."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BankruptcyStatus(StrEnum):
    NO_RECORDS = "no_records"
    PROCEEDINGS_OPENED = "proceedings_opened"
    BANKRUPT = "bankrupt"
    REHABILITATED = "rehabilitated"
    CHECK_FAILED = "check_failed"


class BankruptcyCheck(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bankruptcy_checks"

    debtor_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("debtors.id"), nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[BankruptcyStatus] = mapped_column(
        Enum(BankruptcyStatus, name="bankruptcy_status_enum"), nullable=False
    )
    case_number: Mapped[str | None] = mapped_column(String(100))
    court_name: Mapped[str | None] = mapped_column(String(500))
    details: Mapped[str | None] = mapped_column(Text)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(String(500))

    debtor: Mapped["Debtor"] = relationship(back_populates="bankruptcy_checks")  # noqa: F821

    def __repr__(self) -> str:
        return f"<BankruptcyCheck {self.status} debtor={self.debtor_id}>"
