"""Court case model — full lifecycle tracking."""

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


class CaseType(StrEnum):
    CIVIL = "civil"
    COMMERCIAL = "commercial"
    ADMINISTRATIVE = "administrative"
    NAKAZNE = "nakazne"  # наказне провадження
    POZOVNE = "pozovne"  # позовне провадження


class CaseStatus(StrEnum):
    DRAFT = "draft"
    FILED = "filed"
    IN_PROGRESS = "in_progress"
    DECIDED = "decided"
    APPEALED = "appealed"
    CASSATION = "cassation"
    ENFORCEMENT = "enforcement"
    CLOSED = "closed"
    RETURNED = "returned"


class CourtCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "court_cases"

    # ── Links ────────────────────────────────────────────────
    debtor_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("debtors.id"), nullable=False
    )

    # ── Case identifiers ────────────────────────────────────
    case_number: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, unique=True,
        comment="Номер справи (напр. 753/1234/24)"
    )
    case_type: Mapped[CaseType] = mapped_column(
        Enum(CaseType, name="case_type_enum"), nullable=False
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status_enum"),
        default=CaseStatus.DRAFT,
        nullable=False,
    )

    # ── Court info ───────────────────────────────────────────
    court_name: Mapped[str] = mapped_column(String(500), nullable=False)
    court_code: Mapped[str | None] = mapped_column(String(20))
    judge_name: Mapped[str | None] = mapped_column(String(255))

    # ── Financial ────────────────────────────────────────────
    claim_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    court_fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    awarded_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), comment="Стягнута сума за рішенням"
    )

    # ── Dates ────────────────────────────────────────────────
    filing_date: Mapped[date | None] = mapped_column(Date)
    hearing_date: Mapped[date | None] = mapped_column(Date)
    decision_date: Mapped[date | None] = mapped_column(Date)

    # ── Party replacement (заміна сторони) ───────────────────
    party_replacement_needed: Mapped[bool] = mapped_column(default=False)
    party_replacement_status: Mapped[str | None] = mapped_column(String(50))
    party_replacement_date: Mapped[date | None] = mapped_column(Date)

    notes: Mapped[str | None] = mapped_column(Text)

    # ── Relationships ────────────────────────────────────────
    debtor: Mapped["Debtor"] = relationship(back_populates="court_cases")  # noqa: F821
    decisions: Mapped[list["CourtDecision"]] = relationship(  # noqa: F821
        back_populates="court_case", cascade="all, delete-orphan"
    )
    rulings: Mapped[list["CourtRuling"]] = relationship(  # noqa: F821
        back_populates="court_case", cascade="all, delete-orphan"
    )
    enforcement_proceedings: Mapped[list["EnforcementProceeding"]] = relationship(  # noqa: F821
        back_populates="court_case", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_court_cases_court_judge", "court_name", "judge_name"),
        Index("ix_court_cases_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<CourtCase {self.case_number}>"
