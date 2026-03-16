"""Portfolio Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PortfolioBase(BaseModel):
    name: str
    purchase_date: Optional[date] = None
    purchase_price_uah: Optional[Decimal] = None
    seller_name: Optional[str] = None
    seller_edrpou: Optional[str] = None
    contract_number: Optional[str] = None
    total_claimed_at_purchase: Optional[Decimal] = None
    total_principal_at_purchase: Optional[Decimal] = None
    total_interest_at_purchase: Optional[Decimal] = None
    total_penalty_at_purchase: Optional[Decimal] = None
    debtor_count: Optional[int] = None
    currency: str = "UAH"
    notes: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_price_uah: Optional[Decimal] = None
    seller_name: Optional[str] = None
    seller_edrpou: Optional[str] = None
    contract_number: Optional[str] = None
    notes: Optional[str] = None


class PortfolioResponse(PortfolioBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioListResponse(BaseModel):
    items: list[PortfolioResponse]
    total: int
    page: int
    page_size: int
