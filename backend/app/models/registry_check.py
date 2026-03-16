"""Registry check and bankruptcy alert models."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RegistryCheck(Base):
    """Result of checking a debtor against Ukrainian public registries."""

    __tablename__ = "registry_checks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    debtor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False, index=True
    )

    registry_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # edr / court_registry / enforcement / bankruptcy / sanctions / etc.
    check_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="success"
    )  # success / error / timeout
    result_summary: Mapped[str | None] = mapped_column(Text)
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
    has_match: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    debtor: Mapped["Debtor"] = relationship(back_populates="registry_checks")


class BankruptcyAlert(Base):
    """Alert raised when bankruptcy is detected for a debtor."""

    __tablename__ = "bankruptcy_alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    debtor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    registry_check_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("registry_checks.id", ondelete="SET NULL")
    )

    alert_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    case_number: Mapped[str | None] = mapped_column(String(50))
    court_name: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[str | None] = mapped_column(Text)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(100))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
