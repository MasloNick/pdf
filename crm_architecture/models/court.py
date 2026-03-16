"""
Court and enforcement proceedings entities.
"""

from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, Text, ForeignKey, Enum,
)
from sqlalchemy.orm import relationship

from .credit_case import Base
from .enums import CourtState, EnforcementState


class CourtProceeding(Base):
    """A court case linked to a credit case."""

    __tablename__ = "court_proceedings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)

    # --- Court identifiers ---
    court_case_number = Column(String(100), nullable=True, index=True)
    esits_id = Column(String(100), nullable=True)  # ЄСІТС identifier
    court_name = Column(String(255), nullable=True)
    judge_name = Column(String(255), nullable=True)

    # --- Claim details ---
    claim_amount = Column(Numeric(14, 2), nullable=True)
    court_fee_amount = Column(Numeric(10, 2), nullable=True)
    filing_date = Column(Date, nullable=True)

    # --- Current state ---
    state = Column(
        Enum(CourtState, name="court_proceeding_state_enum"),
        nullable=False,
        default=CourtState.DRAFTING,
    )

    # --- Key dates ---
    hearing_date = Column(DateTime, nullable=True)
    decision_date = Column(Date, nullable=True)
    decision_effective_date = Column(Date, nullable=True)
    exec_doc_requested_date = Column(Date, nullable=True)
    exec_doc_received_date = Column(Date, nullable=True)

    # --- Decision ---
    decision_summary = Column(Text, nullable=True)
    awarded_amount = Column(Numeric(14, 2), nullable=True)

    # --- Instance tracking ---
    instance_level = Column(Integer, default=1)  # 1=first, 2=appeal, 3=cassation
    parent_proceeding_id = Column(Integer, ForeignKey("court_proceedings.id"), nullable=True)

    # --- Metadata ---
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    case = relationship("CreditCase", back_populates="court_proceedings")


class EnforcementProceeding(Base):
    """An enforcement proceeding linked to a credit case."""

    __tablename__ = "enforcement_proceedings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)

    # --- Enforcement identifiers ---
    proceeding_number = Column(String(100), nullable=True, index=True)
    executor_name = Column(String(255), nullable=True)
    executor_region = Column(String(100), nullable=True)
    executor_type = Column(String(50), nullable=True)  # private / state

    # --- Exec document ---
    exec_doc_number = Column(String(100), nullable=True)
    exec_doc_type = Column(String(100), nullable=True)
    submission_date = Column(Date, nullable=True)

    # --- Current state ---
    state = Column(
        Enum(EnforcementState, name="enforcement_proceeding_state_enum"),
        nullable=False,
        default=EnforcementState.PACKAGE_PREP,
    )

    # --- Key dates ---
    opened_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)

    # --- Recovery amounts ---
    recovered_amount = Column(Numeric(14, 2), default=0)
    executor_fee = Column(Numeric(10, 2), nullable=True)

    # --- Metadata ---
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    case = relationship("CreditCase", back_populates="enforcement_proceedings")
