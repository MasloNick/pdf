"""
Notification and escalation rules configuration.

Defines what events trigger notifications, to whom, with what priority,
and escalation timelines.
"""

from dataclasses import dataclass, field
from typing import Optional

from ..models.enums import UserRole, TaskPriority


@dataclass
class NotificationRule:
    """A rule that triggers a notification when a specific event occurs."""
    event: str
    description_ua: str
    notify_roles: list[UserRole]
    priority: TaskPriority
    timing: str  # "immediate", "daily_digest", "on_due_date"
    escalation_after_hours: Optional[int] = None
    escalation_to: list[UserRole] = field(default_factory=list)


NOTIFICATION_RULES: list[NotificationRule] = [
    # --- Court events ---
    NotificationRule(
        event="court_without_motion",
        description_ua="Пропущено строк усунення недоліків по суду",
        notify_roles=[UserRole.LAWYER, UserRole.LEGAL_HEAD],
        priority=TaskPriority.CRITICAL,
        timing="immediate",
        escalation_after_hours=24,
        escalation_to=[UserRole.DIRECTOR],
    ),
    NotificationRule(
        event="court_decision_issued",
        description_ua="Отримано рішення суду",
        notify_roles=[UserRole.LAWYER, UserRole.LEGAL_HEAD, UserRole.DIRECTOR],
        priority=TaskPriority.HIGH,
        timing="immediate",
    ),
    NotificationRule(
        event="court_hearing_scheduled",
        description_ua="Призначено засідання суду",
        notify_roles=[UserRole.LAWYER, UserRole.LEGAL_HEAD],
        priority=TaskPriority.MEDIUM,
        timing="immediate",
    ),

    # --- Payment events ---
    NotificationRule(
        event="installment_payment_overdue",
        description_ua="Пропущено платіж по розстрочці",
        notify_roles=[UserRole.CALL_CENTER_OPERATOR],
        priority=TaskPriority.HIGH,
        timing="on_due_date",
        escalation_after_hours=48,
        escalation_to=[UserRole.DIRECTOR],
    ),
    NotificationRule(
        event="large_payment_received",
        description_ua="Платіж > встановленого порогу",
        notify_roles=[UserRole.DIRECTOR, UserRole.FINANCE_MANAGER],
        priority=TaskPriority.MEDIUM,
        timing="immediate",
    ),
    NotificationRule(
        event="full_payment_received",
        description_ua="Повне погашення боргу",
        notify_roles=[UserRole.DIRECTOR, UserRole.FINANCE_MANAGER],
        priority=TaskPriority.HIGH,
        timing="immediate",
    ),

    # --- Enforcement events ---
    NotificationRule(
        event="enforcement_proceeding_opened",
        description_ua="ВП відкрито",
        notify_roles=[UserRole.ENFORCEMENT_SPECIALIST, UserRole.ENFORCEMENT_HEAD],
        priority=TaskPriority.MEDIUM,
        timing="immediate",
    ),
    NotificationRule(
        event="exec_doc_returned_no_open",
        description_ua="Повернуто ВД без відкриття",
        notify_roles=[UserRole.ENFORCEMENT_SPECIALIST, UserRole.ENFORCEMENT_HEAD],
        priority=TaskPriority.HIGH,
        timing="immediate",
    ),
    NotificationRule(
        event="enforcement_closed_no_recovery",
        description_ua="ВП завершено без стягнення",
        notify_roles=[UserRole.ENFORCEMENT_HEAD, UserRole.DIRECTOR],
        priority=TaskPriority.HIGH,
        timing="immediate",
    ),

    # --- Case management events ---
    NotificationRule(
        event="case_closed_uncollectible",
        description_ua="Справу закрито безрезультатно",
        notify_roles=[UserRole.DIRECTOR],
        priority=TaskPriority.CRITICAL,
        timing="immediate",
    ),
    NotificationRule(
        event="case_no_action_threshold",
        description_ua="Справа без дій > N днів",
        notify_roles=[UserRole.CALL_CENTER_OPERATOR, UserRole.LEGAL_HEAD],
        priority=TaskPriority.HIGH,
        timing="daily_digest",
        escalation_after_hours=72,
        escalation_to=[UserRole.DIRECTOR],
    ),
    NotificationRule(
        event="task_overdue",
        description_ua="Прострочена задача",
        notify_roles=[],  # Dynamically resolved to the task assignee
        priority=TaskPriority.HIGH,
        timing="immediate",
        escalation_after_hours=24,
        escalation_to=[],  # Dynamically resolved to the assignee's manager
    ),

    # --- Risk flag events ---
    NotificationRule(
        event="limitation_risk_detected",
        description_ua="Виявлено ризик позовної давності",
        notify_roles=[UserRole.LEGAL_HEAD, UserRole.LAWYER],
        priority=TaskPriority.CRITICAL,
        timing="immediate",
        escalation_after_hours=24,
        escalation_to=[UserRole.DIRECTOR],
    ),
    NotificationRule(
        event="deceased_flag_set",
        description_ua="Позначено прапорець 'померлий'",
        notify_roles=[UserRole.LEGAL_HEAD],
        priority=TaskPriority.HIGH,
        timing="immediate",
    ),
]


# =============================================================================
# AGING THRESHOLDS — when to trigger "no action" alerts
# =============================================================================

AGING_THRESHOLDS = {
    "call_center": {
        "warning_days": 14,
        "critical_days": 30,
    },
    "legal_prep": {
        "warning_days": 21,
        "critical_days": 45,
    },
    "court": {
        "warning_days": 30,
        "critical_days": 60,
    },
    "enforcement": {
        "warning_days": 30,
        "critical_days": 90,
    },
}

# =============================================================================
# INSTALLMENT OVERDUE THRESHOLD
# =============================================================================

INSTALLMENT_OVERDUE_DAYS = 60  # Days after missed payment to trigger BROKEN_INSTALLMENT
