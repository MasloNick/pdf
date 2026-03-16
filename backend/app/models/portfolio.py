"""Portfolio model — purchased NPL portfolios."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Numeric, Integer, Date, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date)
    purchase_price_uah: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    seller_name: Mapped[Optional[str]] = mapped_column(String(255))
    seller_edrpou: Mapped[Optional[str]] = mapped_column(String(10))
    contract_number: Mapped[Optional[str]] = mapped_column(String(100))
    total_claimed_at_purchase: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    total_principal_at_purchase: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    total_interest_at_purchase: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    total_penalty_at_purchase: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    debtor_count: Mapped[Optional[int]] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="UAH")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    debtors: Mapped[List["Debtor"]] = relationship(back_populates="portfolio", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, name='{self.name}')>"
