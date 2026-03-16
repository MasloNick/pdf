"""Debtor schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.debtor import DebtorStatus, DebtorType


class DebtorCreate(BaseModel):
    portfolio_id: uuid.UUID
    debtor_type: DebtorType
    full_name: str = Field(..., max_length=500)
    ipn_code: str | None = Field(default=None, max_length=10)
    passport_series: str | None = None
    date_of_birth: date | None = None
    registration_address: str | None = None
    actual_address: str | None = None
    region: str | None = None
    phone: str | None = None
    email: str | None = None
    original_debt_amount: Decimal = Field(..., ge=0)
    current_debt_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="UAH", max_length=3)
    original_creditor: str | None = None
    original_contract_number: str | None = None
    original_contract_date: date | None = None
    notes: str | None = None


class DebtorUpdate(BaseModel):
    full_name: str | None = None
    ipn_code: str | None = None
    status: DebtorStatus | None = None
    registration_address: str | None = None
    actual_address: str | None = None
    phone: str | None = None
    email: str | None = None
    current_debt_amount: Decimal | None = None
    notes: str | None = None


class DebtorOut(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    debtor_type: DebtorType
    full_name: str
    ipn_code: str | None
    date_of_birth: date | None
    registration_address: str | None
    region: str | None
    phone: str | None
    email: str | None
    original_debt_amount: Decimal
    current_debt_amount: Decimal
    currency: str
    original_creditor: str | None
    status: DebtorStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DebtorListOut(BaseModel):
    items: list[DebtorOut]
    total: int
    page: int
    size: int
