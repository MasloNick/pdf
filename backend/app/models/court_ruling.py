"""Court ruling model — intermediate rulings per case."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Numeric, Integer, DateTime, Text, Boolean,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CourtRuling(Base):
    __tablename__ = "court_rulings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("court_cases.id"), nullable=False)
    debtor_id: Mapped[int] = mapped_column(ForeignKey("debtors.id"), nullable=False)

    ruling_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ruling_type: Mapped[Optional[str]] = mapped_column(String(50))
    ruling_description: Mapped[Optional[str]] = mapped_column(Text)
    ruling_text_raw: Mapped[Optional[str]] = mapped_column(Text)

    # Registry
    registry_id: Mapped[Optional[str]] = mapped_column(String(50))
    registry_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Impact
    affects_timeline: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    delay_days: Mapped[Optional[int]] = mapped_column(Integer)
    is_blocking: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Source
    source: Mapped[Optional[str]] = mapped_column(String(50))
    ai_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case: Mapped["CourtCase"] = relationship(back_populates="rulings")

    __table_args__ = (
        Index("ix_court_rulings_case_id", "case_id"),
        Index("ix_court_rulings_ruling_type", "ruling_type"),
    )

    def __repr__(self) -> str:
        return f"<CourtRuling(id={self.id}, type='{self.ruling_type}')>"
