"""Debtor schemas."""

from datetime import date, datetime

from pydantic import BaseModel


class DebtorCreate(BaseModel):
    debtor_type: str = "individual"
    last_name: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    full_name: str | None = None
    ipn: str | None = None
    edrpou: str | None = None
    passport_series: str | None = None
    passport_number: str | None = None
    birth_date: date | None = None
    notes: str | None = None


class DebtorUpdate(BaseModel):
    last_name: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    full_name: str | None = None
    status: str | None = None
    notes: str | None = None


class DebtorResponse(BaseModel):
    id: int
    debtor_type: str
    last_name: str | None
    first_name: str | None
    patronymic: str | None
    full_name: str | None
    ipn: str | None
    edrpou: str | None
    birth_date: date | None
    status: str
    is_bankrupt: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DebtorListResponse(BaseModel):
    items: list[DebtorResponse]
    total: int
    page: int
    page_size: int
