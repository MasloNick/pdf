"""
Payment and installment plan entities.
"""

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, Text, ForeignKey, Boolean,
)
from sqlalchemy.orm import relationship

from .credit_case import Base


class Payment(Base):
    """A single payment fact."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)

    amount = Column(Numeric(14, 2), nullable=False)
    payment_date = Column(Date, nullable=False, index=True)
    received_at = Column(DateTime, default=datetime.utcnow)

    source = Column(String(100), nullable=True)  # bank, executor, voluntary, etc.
    reference_number = Column(String(100), nullable=True)
    confirmed = Column(Boolean, default=False)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CreditCase", back_populates="payments")


class InstallmentPlan(Base):
    """An agreed payment schedule (rozstochka)."""

    __tablename__ = "installment_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)

    total_amount = Column(Numeric(14, 2), nullable=False)
    monthly_amount = Column(Numeric(14, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    payment_day = Column(Integer, nullable=True)  # Day of month

    is_active = Column(Boolean, default=True)
    broken_at = Column(DateTime, nullable=True)
    break_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)


class InstallmentPayment(Base):
    """Expected payment in an installment plan."""

    __tablename__ = "installment_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("installment_plans.id"), nullable=False, index=True)
    due_date = Column(Date, nullable=False)
    expected_amount = Column(Numeric(14, 2), nullable=False)
    actual_payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    is_paid = Column(Boolean, default=False)
    is_overdue = Column(Boolean, default=False)
