"""
Debtor entity — a person who owes debt.
One debtor can have multiple credit cases.
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Boolean
from sqlalchemy.orm import relationship

from .credit_case import Base


class Debtor(Base):
    """Physical person with debt obligations."""

    __tablename__ = "debtors"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # --- Identity ---
    last_name = Column(String(100), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    tax_id = Column(String(20), nullable=True, unique=True, index=True)  # ІПН
    date_of_birth = Column(Date, nullable=True)
    passport_series = Column(String(10), nullable=True)
    passport_number = Column(String(20), nullable=True)

    # --- Contacts ---
    phone_primary = Column(String(20), nullable=True)
    phone_secondary = Column(String(20), nullable=True)
    phone_work = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    # --- Address ---
    registration_address = Column(Text, nullable=True)
    actual_address = Column(Text, nullable=True)
    region = Column(String(100), nullable=True)

    # --- Employment ---
    employer = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)

    # --- Metadata ---
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    # --- Relationships ---
    cases = relationship("CreditCase", back_populates="debtor")

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)
