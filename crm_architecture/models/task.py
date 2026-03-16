"""
Task / SLA entity — the main driver of employee workflow.
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, Enum, Boolean,
)
from sqlalchemy.orm import relationship

from .credit_case import Base
from .enums import TaskPriority, TaskStatus


class Task(Base):
    """A concrete action assigned to a user with a deadline and priority."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("credit_cases.id"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # --- Assignment ---
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # --- Timing ---
    due_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # --- State ---
    priority = Column(
        Enum(TaskPriority, name="task_priority_enum"),
        nullable=False,
        default=TaskPriority.MEDIUM,
    )
    status = Column(
        Enum(TaskStatus, name="task_status_enum"),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
    )

    # --- Context ---
    module = Column(String(50), nullable=True)  # call_center, court, enforcement, etc.
    is_auto_generated = Column(Boolean, default=False)
    trigger_event = Column(String(100), nullable=True)  # What event created this task

    resolution = Column(Text, nullable=True)

    case = relationship("CreditCase", back_populates="tasks")

    @property
    def is_overdue(self) -> bool:
        if self.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            return False
        return datetime.utcnow() > self.due_date
