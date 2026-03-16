"""Debtor Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class DebtorBase(BaseModel):
    full_name: str
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    ipn: Optional[str] = None
    birth_date: Optional[date] = None
    birth_place: Optional[str] = None
    gender: Optional[str] = None

    # Documents
    passport_series: Optional[str] = None
    passport_number: Optional[str] = None
    id_card_number: Optional[str] = None

    # Address
    registration_address_raw: Optional[str] = None
    actual_address_raw: Optional[str] = None

    # Contacts
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None

    # Credit
    credit_contract_number: Optional[str] = None
    credit_contract_date: Optional[date] = None
    original_creditor: Optional[str] = None
    product_type: Optional[str] = None

    # Financials
    purchased_principal_uah: Optional[Decimal] = None
    purchased_interest_uah: Optional[Decimal] = None
    purchased_penalty_uah: Optional[Decimal] = None
    purchased_court_fee_uah: Optional[Decimal] = None
    purchased_other_uah: Optional[Decimal] = None
    purchased_total_uah: Optional[Decimal] = None

    @field_validator("ipn")
    @classmethod
    def validate_ipn(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) != 10 or not v.isdigit():
            raise ValueError("IPN must be exactly 10 digits")
        # Ukrainian IPN checksum validation
        weights = [-1, 5, 7, 9, 4, 6, 10, 5, 7]
        checksum = sum(int(v[i]) * weights[i] for i in range(9)) % 11 % 10
        if checksum != int(v[9]):
            raise ValueError("IPN checksum validation failed")
        return v


class DebtorCreate(DebtorBase):
    portfolio_id: int


class DebtorUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    collection_status: Optional[str] = None
    responsible_lawyer_id: Optional[int] = None
    notes: Optional[str] = None


class DebtorResponse(DebtorBase):
    id: int
    portfolio_id: int
    collection_status: Optional[str] = None
    responsible_lawyer_id: Optional[int] = None
    in_erb: Optional[bool] = None
    in_bankruptcy: Optional[bool] = None
    registration_address_normalized: Optional[str] = None
    address_norm_confidence: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DebtorListResponse(BaseModel):
    items: list[DebtorResponse]
    total: int
    page: int
    page_size: int
