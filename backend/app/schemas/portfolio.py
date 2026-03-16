"""Portfolio schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PortfolioCreate(BaseModel):
    name: str = Field(..., max_length=255)
    seller_name: str = Field(..., max_length=255)
    purchase_date: date
    purchase_price: Decimal = Field(..., ge=0)
    total_nominal_debt: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="UAH", max_length=3)
    contract_number: str | None = None
    notes: str | None = None


class PortfolioUpdate(BaseModel):
    name: str | None = None
    seller_name: str | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    total_nominal_debt: Decimal | None = None
    currency: str | None = None
    contract_number: str | None = None
    notes: str | None = None


class PortfolioOut(BaseModel):
    id: uuid.UUID
    name: str
    seller_name: str
    purchase_date: date
    purchase_price: Decimal
    total_nominal_debt: Decimal
    currency: str
    contract_number: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    debtor_count: int = 0

    model_config = {"from_attributes": True}
