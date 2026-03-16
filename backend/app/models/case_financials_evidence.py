"""Case financials evidence — proof of extracted amounts."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Numeric, Integer, DateTime, Text,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CaseFinancialsEvidence(Base):
    __tablename__ = "case_financials_evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("court_cases.id"), nullable=False)

    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value_raw: Mapped[Optional[str]] = mapped_column(Text)
    value_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    scale: Mapped[Optional[str]] = mapped_column(String(20))
    evidence_quote: Mapped[Optional[str]] = mapped_column(Text)
    evidence_section: Mapped[Optional[str]] = mapped_column(String(50))
    char_start: Mapped[Optional[int]] = mapped_column(Integer)
    char_end: Mapped[Optional[int]] = mapped_column(Integer)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    extraction_method: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case: Mapped["CourtCase"] = relationship(back_populates="financials_evidence")

    __table_args__ = (Index("ix_case_financials_evidence_case_id", "case_id"),)

    def __repr__(self) -> str:
        return f"<CaseFinancialsEvidence(id={self.id}, field='{self.field_name}')>"
