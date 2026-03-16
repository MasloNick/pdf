"""Court decision model — AI-parsed financial data."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Date,
    Enum,
    Float,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DecisionResult(StrEnum):
    SATISFIED = "satisfied"
    PARTIALLY_SATISFIED = "partially_satisfied"
    DENIED = "denied"
    RETURNED = "returned"
    CLOSED = "closed"
    MISSING_IN_DECISION = "MISSING_IN_DECISION"


class ParseConfidence(StrEnum):
    HIGH = "high"          # >= 0.85
    MEDIUM = "medium"      # 0.65–0.85
    LOW = "low"            # < 0.65, needs review
    NEEDS_REVIEW = "NEEDS_REVIEW"


class CourtDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "court_decisions"

    court_case_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("court_cases.id"), nullable=False
    )

    # ── Decision metadata ────────────────────────────────────
    decision_date: Mapped[date | None] = mapped_column(Date)
    full_text: Mapped[str | None] = mapped_column(Text)
    reyestr_url: Mapped[str | None] = mapped_column(
        String(500), comment="URL в ЄДРСР"
    )
    reyestr_doc_id: Mapped[str | None] = mapped_column(String(50))

    # ── AI-parsed results ────────────────────────────────────
    result: Mapped[DecisionResult] = mapped_column(
        Enum(DecisionResult, name="decision_result_enum"),
        default=DecisionResult.MISSING_IN_DECISION,
    )
    awarded_principal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    awarded_interest: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    awarded_penalties: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    awarded_court_fee: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    awarded_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # ── Reasons and analysis ─────────────────────────────────
    denial_reason: Mapped[str | None] = mapped_column(
        Text, comment="Причина відмови (якщо denied)"
    )
    decision_summary: Mapped[str | None] = mapped_column(Text)
    parsed_data: Mapped[dict | None] = mapped_column(
        JSONB, comment="Full structured parse output"
    )

    # ── Parse quality ────────────────────────────────────────
    parse_confidence: Mapped[float | None] = mapped_column(Float)
    confidence_level: Mapped[ParseConfidence | None] = mapped_column(
        Enum(ParseConfidence, name="parse_confidence_enum")
    )
    parse_method: Mapped[str | None] = mapped_column(
        String(50), comment="rules / local_llm / claude_api"
    )
    needs_review: Mapped[bool] = mapped_column(default=False)
    review_reason: Mapped[str | None] = mapped_column(Text)

    # ── Relationship ─────────────────────────────────────────
    court_case: Mapped["CourtCase"] = relationship(back_populates="decisions")  # noqa: F821

    def __repr__(self) -> str:
        return f"<CourtDecision case={self.court_case_id} result={self.result}>"
