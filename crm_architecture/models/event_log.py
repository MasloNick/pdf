"""
Event Log — immutable history of all case events.

This is the foundation for analytics, audit trails, and time-in-state calculations.
Events are NEVER modified or deleted.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship

from .credit_case import Base
from .enums import EventType, ChangeSource


class EventLog(Base):
    """Immutable event record. Never update or delete."""

    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)

    event_type = Column(
        Enum(EventType, name="event_type_enum"),
        nullable=False,
        index=True,
    )

    # --- What changed ---
    dimension = Column(String(50), nullable=True)  # Which state dimension changed
    old_value = Column(String(100), nullable=True)
    new_value = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # --- Who / how ---
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    source = Column(
        Enum(ChangeSource, name="change_source_enum"),
        nullable=False,
        default=ChangeSource.MANUAL,
    )

    # --- Additional structured data ---
    metadata = Column(JSON, nullable=True)  # Flexible storage for event-specific data

    # --- Timestamp (immutable) ---
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    case = relationship("CreditCase", back_populates="events")


class User(Base):
    """Minimal user entity for role-based access control."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False)  # UserRole enum value
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Document or file attached to a credit case."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    document_type = Column(String(100), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    version = Column(Integer, default=1)

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    case = relationship("CreditCase", back_populates="documents")
