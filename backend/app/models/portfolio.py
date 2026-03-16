"""Portfolio and portfolio-debtor link models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Portfolio(Base):
    """A purchased NPL portfolio."""

    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    seller_name: Mapped[str] = mapped_column(String(255), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_nominal_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UAH")
    contract_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    debtor_links: Mapped[list["PortfolioDebtorLink"]] = relationship(back_populates="portfolio")


class PortfolioDebtorLink(Base):
    """Links a debtor to a portfolio with debtor-specific financial data."""

    __tablename__ = "portfolio_debtor_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    debtor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False, index=True
    )

    original_creditor: Mapped[str | None] = mapped_column(String(255))
    original_contract_number: Mapped[str | None] = mapped_column(String(100))
    original_contract_date: Mapped[date | None] = mapped_column(Date)
    nominal_debt: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    principal: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    interest: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    penalties: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    commission: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio: Mapped["Portfolio"] = relationship(back_populates="debtor_links")
    debtor: Mapped["Debtor"] = relationship(back_populates="portfolio_links")
