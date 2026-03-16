"""Court case, decision, and ruling models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CourtCase(Base):
    """A court case filed for debt recovery."""

    __tablename__ = "court_cases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    debtor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    portfolio_debtor_link_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("portfolio_debtor_links.id", ondelete="SET NULL"), index=True
    )

    # -- Case identification --
    case_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    court_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    judge_name: Mapped[str | None] = mapped_column(String(255), index=True)
    proceeding_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # civil / commercial / administrative

    # -- Claim --
    claim_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    court_fee: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    filing_date: Mapped[date | None] = mapped_column(Date, index=True)

    # -- Status --
    status: Mapped[str] = mapped_column(
        String(30), default="filed", index=True
    )  # filed / in_progress / decided / appealed / closed
    current_stage: Mapped[str | None] = mapped_column(String(50))

    # -- Decision summary (populated by AI parser) --
    decision_date: Mapped[date | None] = mapped_column(Date)
    decision_type: Mapped[str | None] = mapped_column(String(50))  # satisfied / partial / rejected
    awarded_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_principal: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_interest: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_penalties: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_court_fee: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_3percent: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_inflation: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # -- Relations --
    debtor: Mapped["Debtor"] = relationship(back_populates="court_cases")
    decisions: Mapped[list["CourtDecision"]] = relationship(
        back_populates="court_case", order_by="CourtDecision.decision_date"
    )
    rulings: Mapped[list["CourtRuling"]] = relationship(
        back_populates="court_case", order_by="CourtRuling.ruling_date"
    )


class CourtDecision(Base):
    """A parsed court decision (рішення / постанова)."""

    __tablename__ = "court_decisions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    court_case_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("court_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # -- Source --
    reyestr_id: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True
    )  # ID in court registry
    document_url: Mapped[str | None] = mapped_column(String(500))
    raw_text: Mapped[str | None] = mapped_column(Text)

    # -- Parsed data --
    decision_date: Mapped[date | None] = mapped_column(Date, index=True)
    decision_type: Mapped[str | None] = mapped_column(String(50))
    court_name: Mapped[str | None] = mapped_column(String(255))
    judge_name: Mapped[str | None] = mapped_column(String(255))
    proceeding_form: Mapped[str | None] = mapped_column(String(50))  # written / oral / simplified

    # -- Financial extraction --
    claimed_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_principal: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_interest: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_penalties: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_court_fee: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_3percent: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_inflation: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # -- AI analysis --
    outcome: Mapped[str | None] = mapped_column(
        String(30)
    )  # satisfied / partial / rejected / returned
    rejection_reasons: Mapped[dict | None] = mapped_column(JSONB)
    key_findings: Mapped[dict | None] = mapped_column(JSONB)

    # -- Quality markers --
    parse_method: Mapped[str | None] = mapped_column(String(20))  # rules / local_llm / claude
    confidence: Mapped[float | None] = mapped_column(Float)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    review_reason: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    court_case: Mapped["CourtCase"] = relationship(back_populates="decisions")


class CourtRuling(Base):
    """An intermediate court ruling / order (ухвала)."""

    __tablename__ = "court_rulings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    court_case_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("court_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reyestr_id: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    document_url: Mapped[str | None] = mapped_column(String(500))
    raw_text: Mapped[str | None] = mapped_column(Text)

    ruling_date: Mapped[date | None] = mapped_column(Date, index=True)
    ruling_type: Mapped[str | None] = mapped_column(
        String(100)
    )  # opening / scheduling / suspension / closing / etc.
    court_name: Mapped[str | None] = mapped_column(String(255))
    judge_name: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)

    parse_method: Mapped[str | None] = mapped_column(String(20))
    confidence: Mapped[float | None] = mapped_column(Float)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    court_case: Mapped["CourtCase"] = relationship(back_populates="rulings")
