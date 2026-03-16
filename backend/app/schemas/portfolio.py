"""Portfolio schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class PortfolioCreate(BaseModel):
    name: str
    seller_name: str
    purchase_date: date
    purchase_price: Decimal
    total_nominal_value: Decimal
    currency: str = "UAH"
    contract_number: str | None = None
    notes: str | None = None


class PortfolioUpdate(BaseModel):
    name: str | None = None
    seller_name: str | None = None
    purchase_price: Decimal | None = None
    total_nominal_value: Decimal | None = None
    notes: str | None = None


class PortfolioResponse(BaseModel):
    id: int
    name: str
    seller_name: str
    purchase_date: date
    purchase_price: Decimal
    total_nominal_value: Decimal
    currency: str
    contract_number: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PortfolioDebtorLinkCreate(BaseModel):
    portfolio_id: int
    debtor_id: int
    original_creditor: str | None = None
    original_contract_number: str | None = None
    original_contract_date: date | None = None
    nominal_debt: Decimal
    principal: Decimal | None = None
    interest: Decimal | None = None
    penalties: Decimal | None = None
    commission: Decimal | None = None
