"""ERB Registry — local copy of ЄДРБ."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Numeric, Date, DateTime, Text, Boolean,
    ForeignKey, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ErbRegistry(Base):
    __tablename__ = "erb_registry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ipn: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    debtor_type: Mapped[Optional[str]] = mapped_column(String(20))
    creditor_name: Mapped[Optional[str]] = mapped_column(String(255))
    creditor_edrpou: Mapped[Optional[str]] = mapped_column(String(10))
    debt_amount_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    debt_currency: Mapped[Optional[str]] = mapped_column(String(3))
    entry_date: Mapped[Optional[date]] = mapped_column(Date)
    basis_document: Mapped[Optional[str]] = mapped_column(Text)
    enforcement_body: Mapped[Optional[str]] = mapped_column(String(255))
    executor_name: Mapped[Optional[str]] = mapped_column(String(255))
    executor_region: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[Optional[str]] = mapped_column(String(20), default="active")
    removal_date: Mapped[Optional[date]] = mapped_column(Date)
    removal_reason: Mapped[Optional[str]] = mapped_column(Text)
    debtor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("debtors.id"))
    matched: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    match_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    source_file: Mapped[Optional[str]] = mapped_column(String(255))
    import_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    row_hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_erb_registry_full_name", "full_name"),
        Index("ix_erb_registry_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ErbRegistry(id={self.id}, ipn='{self.ipn}')>"
