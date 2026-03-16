"""NPL Portfolio model."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Portfolio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "portfolios"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    seller_name: Mapped[str] = mapped_column(String(255), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    total_nominal_debt: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=0
    )
    currency: Mapped[str] = mapped_column(String(3), default="UAH")
    contract_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    debtors: Mapped[list["Debtor"]] = relationship(  # noqa: F821
        back_populates="portfolio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Portfolio {self.name}>"
