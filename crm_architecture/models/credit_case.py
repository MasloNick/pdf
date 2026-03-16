"""
Credit Case — the central entity of the CRM.

A credit case holds the multi-dimensional state model:
- global_lifecycle (exactly 1)
- call_center_state (0..1)
- legal_prep_state (0..1)
- court_state (0..1)
- enforcement_state (0..1)
- payment_state (exactly 1)
- risk_flags (0..N)
- next_action / SLA (always present)
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, Enum, ForeignKey, Text,
    Boolean,
)
from sqlalchemy.orm import relationship, declarative_base

from .enums import (
    GlobalLifecycle, CallCenterState, LegalPrepState, CourtState,
    EnforcementState, PaymentState,
)

Base = declarative_base()


class CreditCase(Base):
    """Main credit case entity with multi-dimensional status model."""

    __tablename__ = "credit_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(50), unique=True, nullable=False, index=True)

    # --- Links ---
    debtor_id = Column(Integer, ForeignKey("debtors.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, index=True)

    # --- Debt economics ---
    original_debt_amount = Column(Numeric(14, 2), nullable=False)
    current_balance = Column(Numeric(14, 2), nullable=False)
    purchase_price = Column(Numeric(14, 2), nullable=True)
    currency = Column(String(3), default="UAH")

    # --- Contract info ---
    original_creditor = Column(String(255), nullable=True)
    contract_number = Column(String(100), nullable=True)
    contract_date = Column(Date, nullable=True)
    default_date = Column(Date, nullable=True)
    limitation_date = Column(Date, nullable=True)

    # ============================
    # MULTI-DIMENSIONAL STATE MODEL
    # ============================

    # Dimension 1: Global lifecycle (exactly one, mandatory)
    global_lifecycle = Column(
        Enum(GlobalLifecycle, name="global_lifecycle_enum"),
        nullable=False,
        default=GlobalLifecycle.IMPORTED,
        index=True,
    )
    global_lifecycle_since = Column(DateTime, default=datetime.utcnow)

    # Dimension 2: Call-center state (optional)
    call_center_state = Column(
        Enum(CallCenterState, name="call_center_state_enum"),
        nullable=True,
    )
    call_center_state_since = Column(DateTime, nullable=True)

    # Dimension 3: Legal prep state (optional)
    legal_prep_state = Column(
        Enum(LegalPrepState, name="legal_prep_state_enum"),
        nullable=True,
    )
    legal_prep_state_since = Column(DateTime, nullable=True)

    # Dimension 4: Court state (optional)
    court_state = Column(
        Enum(CourtState, name="court_state_enum"),
        nullable=True,
    )
    court_state_since = Column(DateTime, nullable=True)

    # Dimension 5: Enforcement state (optional)
    enforcement_state = Column(
        Enum(EnforcementState, name="enforcement_state_enum"),
        nullable=True,
    )
    enforcement_state_since = Column(DateTime, nullable=True)

    # Dimension 6: Payment state (exactly one, mandatory)
    payment_state = Column(
        Enum(PaymentState, name="payment_state_enum"),
        nullable=False,
        default=PaymentState.NO_PAYMENTS,
        index=True,
    )
    payment_state_since = Column(DateTime, default=datetime.utcnow)

    # --- Metadata ---
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    region = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # --- Relationships ---
    debtor = relationship("Debtor", back_populates="cases")
    portfolio = relationship("Portfolio", back_populates="cases")
    risk_flags = relationship("CaseRiskFlag", back_populates="case", cascade="all, delete-orphan")
    events = relationship("EventLog", back_populates="case", order_by="EventLog.created_at")
    tasks = relationship("Task", back_populates="case")
    payments = relationship("Payment", back_populates="case")
    court_proceedings = relationship("CourtProceeding", back_populates="case")
    enforcement_proceedings = relationship("EnforcementProceeding", back_populates="case")
    documents = relationship("Document", back_populates="case")
    state_history = relationship("StateHistory", back_populates="case", order_by="StateHistory.changed_at")

    def days_in_current_lifecycle(self) -> int:
        """Days the case has been in the current global lifecycle stage."""
        if self.global_lifecycle_since is None:
            return 0
        delta = datetime.utcnow() - self.global_lifecycle_since
        return delta.days

    def active_modules(self) -> list[str]:
        """Return list of currently active module names."""
        modules = []
        if self.call_center_state is not None:
            modules.append("call_center")
        if self.legal_prep_state is not None:
            modules.append("legal_prep")
        if self.court_state is not None:
            modules.append("court")
        if self.enforcement_state is not None:
            modules.append("enforcement")
        return modules


class CaseRiskFlag(Base):
    """Risk flag attached to a credit case. A case can have 0..N flags."""

    __tablename__ = "case_risk_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)
    flag = Column(String(50), nullable=False)  # RiskFlag enum value
    set_at = Column(DateTime, default=datetime.utcnow)
    set_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    case = relationship("CreditCase", back_populates="risk_flags")


class StateHistory(Base):
    """Immutable record of every state change across all dimensions."""

    __tablename__ = "state_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)
    dimension = Column(String(50), nullable=False)  # e.g. "global_lifecycle", "court_state"
    old_value = Column(String(50), nullable=True)
    new_value = Column(String(50), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    source = Column(String(30), nullable=False)  # ChangeSource enum value
    reason = Column(Text, nullable=True)

    case = relationship("CreditCase", back_populates="state_history")
