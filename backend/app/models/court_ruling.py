"""Intermediate court ruling (ухвала) model."""

from datetime import date
from enum import StrEnum

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RulingType(StrEnum):
    OPENED = "opened"                  # відкриття провадження
    SCHEDULED = "scheduled"            # призначення до розгляду
    POSTPONED = "postponed"            # відкладення розгляду
    SUSPENDED = "suspended"            # зупинення провадження
    RESUMED = "resumed"                # відновлення провадження
    PARTY_REPLACED = "party_replaced"  # заміна сторони
    EVIDENCE = "evidence"              # витребування доказів
    SECURITY = "security"              # забезпечення позову
    RETURNED = "returned"              # повернення позовної заяви
    OTHER = "other"


class CourtRuling(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "court_rulings"

    court_case_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("court_cases.id"), nullable=False
    )
    ruling_date: Mapped[date | None] = mapped_column(Date)
    ruling_type: Mapped[RulingType] = mapped_column(
        Enum(RulingType, name="ruling_type_enum"), nullable=False
    )
    summary: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str | None] = mapped_column(Text)
    reyestr_url: Mapped[str | None] = mapped_column(String(500))
    reyestr_doc_id: Mapped[str | None] = mapped_column(String(50))
    next_hearing_date: Mapped[date | None] = mapped_column(Date)

    court_case: Mapped["CourtCase"] = relationship(back_populates="rulings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<CourtRuling {self.ruling_type} case={self.court_case_id}>"
