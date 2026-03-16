"""
State transition rules for all dimensions of the credit case status model.

Each transition defines:
- from_state → to_state (within a single dimension)
- trigger event
- who can trigger it (manual / automatic / integration)
- side effects (tasks, notifications, other dimension changes)
"""

from dataclasses import dataclass, field
from typing import Optional

from ..models.enums import (
    GlobalLifecycle, CallCenterState, LegalPrepState, CourtState,
    EnforcementState, PaymentState, ChangeSource, UserRole,
)


@dataclass
class SideEffect:
    """An action triggered as a consequence of a state transition."""
    create_task: Optional[dict] = None        # {"title": ..., "module": ..., "priority": ...}
    notify_roles: list[str] = field(default_factory=list)
    update_dimension: Optional[dict] = None   # {"dimension": ..., "new_value": ...}


@dataclass
class Transition:
    """A single allowed state transition within one dimension."""
    dimension: str
    from_state: str
    to_state: str
    trigger: str                              # Event that causes this transition
    sources: list[ChangeSource]               # Who/what can trigger it
    allowed_roles: list[UserRole] = field(default_factory=list)  # For manual transitions
    requires_reason: bool = False
    side_effects: list[SideEffect] = field(default_factory=list)


# =============================================================================
# GLOBAL LIFECYCLE TRANSITIONS
# =============================================================================

GLOBAL_LIFECYCLE_TRANSITIONS = [
    Transition(
        dimension="global_lifecycle",
        from_state=GlobalLifecycle.IMPORTED,
        to_state=GlobalLifecycle.VERIFICATION,
        trigger="case_imported_and_assigned",
        sources=[ChangeSource.AUTOMATIC_RULE, ChangeSource.IMPORT],
    ),
    Transition(
        dimension="global_lifecycle",
        from_state=GlobalLifecycle.VERIFICATION,
        to_state=GlobalLifecycle.PRE_COLLECTION,
        trigger="verification_completed",
        sources=[ChangeSource.MANUAL, ChangeSource.AUTOMATIC_RULE],
        allowed_roles=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD, UserRole.CALL_CENTER_OPERATOR],
        side_effects=[
            SideEffect(
                create_task={"title": "Первинний контакт з боржником", "module": "call_center", "priority": "MEDIUM"},
            ),
        ],
    ),
    Transition(
        dimension="global_lifecycle",
        from_state=GlobalLifecycle.PRE_COLLECTION,
        to_state=GlobalLifecycle.LITIGATION,
        trigger="claim_filed",
        sources=[ChangeSource.AUTOMATIC_RULE, ChangeSource.INTEGRATION],
        side_effects=[
            SideEffect(notify_roles=[UserRole.LEGAL_HEAD, UserRole.LAWYER]),
        ],
    ),
    Transition(
        dimension="global_lifecycle",
        from_state=GlobalLifecycle.LITIGATION,
        to_state=GlobalLifecycle.ENFORCEMENT,
        trigger="enforcement_proceeding_opened",
        sources=[ChangeSource.AUTOMATIC_RULE, ChangeSource.INTEGRATION],
        side_effects=[
            SideEffect(notify_roles=[UserRole.ENFORCEMENT_HEAD, UserRole.ENFORCEMENT_SPECIALIST]),
        ],
    ),
    # Any active state → CLOSED_COLLECTED (on full payment)
    Transition(
        dimension="global_lifecycle",
        from_state="*_ACTIVE",  # Any non-closed state
        to_state=GlobalLifecycle.CLOSED_COLLECTED,
        trigger="full_payment_confirmed",
        sources=[ChangeSource.AUTOMATIC_RULE],
        side_effects=[
            SideEffect(notify_roles=[UserRole.DIRECTOR, UserRole.FINANCE_MANAGER]),
        ],
    ),
    # Any active state → CLOSED_UNCOLLECTIBLE (manual only, with reason)
    Transition(
        dimension="global_lifecycle",
        from_state="*_ACTIVE",
        to_state=GlobalLifecycle.CLOSED_UNCOLLECTIBLE,
        trigger="case_deemed_uncollectible",
        sources=[ChangeSource.MANUAL],
        allowed_roles=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD, UserRole.ENFORCEMENT_HEAD],
        requires_reason=True,
        side_effects=[
            SideEffect(notify_roles=[UserRole.DIRECTOR]),
        ],
    ),
    # Closed → ARCHIVED
    Transition(
        dimension="global_lifecycle",
        from_state=GlobalLifecycle.CLOSED_COLLECTED,
        to_state=GlobalLifecycle.ARCHIVED,
        trigger="archival_period_elapsed",
        sources=[ChangeSource.AUTOMATIC_RULE, ChangeSource.MANUAL],
    ),
    Transition(
        dimension="global_lifecycle",
        from_state=GlobalLifecycle.CLOSED_UNCOLLECTIBLE,
        to_state=GlobalLifecycle.ARCHIVED,
        trigger="archival_period_elapsed",
        sources=[ChangeSource.AUTOMATIC_RULE, ChangeSource.MANUAL],
    ),
]

# =============================================================================
# CALL CENTER TRANSITIONS
# =============================================================================

CALL_CENTER_TRANSITIONS = [
    Transition(
        dimension="call_center_state",
        from_state=CallCenterState.NEW,
        to_state=CallCenterState.NO_VALID_CONTACT,
        trigger="no_valid_phone_found",
        sources=[ChangeSource.MANUAL, ChangeSource.AUTOMATIC_RULE],
        side_effects=[
            SideEffect(create_task={"title": "Збагачення контактних даних", "module": "call_center", "priority": "HIGH"}),
        ],
    ),
    Transition(
        dimension="call_center_state",
        from_state=CallCenterState.NEW,
        to_state=CallCenterState.CONTACTED,
        trigger="first_contact_made",
        sources=[ChangeSource.MANUAL],
        allowed_roles=[UserRole.CALL_CENTER_OPERATOR],
    ),
    Transition(
        dimension="call_center_state",
        from_state=CallCenterState.NEW,
        to_state=CallCenterState.CALLBACK,
        trigger="callback_scheduled",
        sources=[ChangeSource.MANUAL],
        allowed_roles=[UserRole.CALL_CENTER_OPERATOR],
    ),
    Transition(
        dimension="call_center_state",
        from_state=CallCenterState.CONTACTED,
        to_state=CallCenterState.NEGOTIATION,
        trigger="negotiation_started",
        sources=[ChangeSource.MANUAL],
        allowed_roles=[UserRole.CALL_CENTER_OPERATOR],
    ),
    Transition(
        dimension="call_center_state",
        from_state=CallCenterState.NEGOTIATION,
        to_state=CallCenterState.PROMISE,
        trigger="guarantee_letter_created",
        sources=[ChangeSource.AUTOMATIC_RULE],  # When document is generated in CRM
    ),
    Transition(
        dimension="call_center_state",
        from_state=CallCenterState.NEGOTIATION,
        to_state=CallCenterState.REFUSAL,
        trigger="debtor_refused",
        sources=[ChangeSource.MANUAL],
        allowed_roles=[UserRole.CALL_CENTER_OPERATOR],
    ),
    Transition(
        dimension="call_center_state",
        from_state=CallCenterState.PROMISE,
        to_state=CallCenterState.PARTIAL_PAYMENT,
        trigger="payment_received_after_promise",
        sources=[ChangeSource.AUTOMATIC_RULE],
    ),
    Transition(
        dimension="call_center_state",
        from_state=CallCenterState.PROMISE,
        to_state=CallCenterState.DORMANT,
        trigger="promise_not_kept_timeout",
        sources=[ChangeSource.AUTOMATIC_RULE],
    ),
    # Any non-terminal → STOP_CONTACT
    Transition(
        dimension="call_center_state",
        from_state="*",
        to_state=CallCenterState.STOP_CONTACT,
        trigger="contact_prohibited",
        sources=[ChangeSource.MANUAL, ChangeSource.AUTOMATIC_RULE],
        allowed_roles=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD],
    ),
]

# =============================================================================
# COURT STATE TRANSITIONS
# =============================================================================

COURT_STATE_TRANSITIONS = [
    Transition(
        dimension="court_state",
        from_state=CourtState.DRAFTING,
        to_state=CourtState.FILED,
        trigger="claim_submitted_to_court",
        sources=[ChangeSource.MANUAL, ChangeSource.INTEGRATION],
        allowed_roles=[UserRole.LAWYER, UserRole.LEGAL_HEAD],
        side_effects=[
            SideEffect(
                update_dimension={"dimension": "global_lifecycle", "new_value": GlobalLifecycle.LITIGATION},
                notify_roles=[UserRole.LEGAL_HEAD],
            ),
        ],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.FILED,
        to_state=CourtState.WITHOUT_MOTION,
        trigger="court_left_without_motion",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
        side_effects=[
            SideEffect(
                create_task={"title": "Усунення недоліків позову", "module": "court", "priority": "CRITICAL"},
                notify_roles=[UserRole.LAWYER, UserRole.LEGAL_HEAD],
            ),
        ],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.FILED,
        to_state=CourtState.OPENED,
        trigger="court_proceeding_opened",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.WITHOUT_MOTION,
        to_state=CourtState.OPENED,
        trigger="defects_cured_proceeding_opened",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.OPENED,
        to_state=CourtState.RESPONSE_RECEIVED,
        trigger="defendant_response_received",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
        side_effects=[
            SideEffect(
                create_task={"title": "Підготувати відповідь на відзив", "module": "court", "priority": "HIGH"},
            ),
        ],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.OPENED,
        to_state=CourtState.HEARING,
        trigger="hearing_scheduled",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.RESPONSE_RECEIVED,
        to_state=CourtState.HEARING,
        trigger="hearing_scheduled",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.HEARING,
        to_state=CourtState.DECISION_ISSUED,
        trigger="court_decision_issued",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
        side_effects=[
            SideEffect(notify_roles=[UserRole.LAWYER, UserRole.LEGAL_HEAD, UserRole.DIRECTOR]),
        ],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.DECISION_ISSUED,
        to_state=CourtState.DECISION_FINAL,
        trigger="decision_became_final",
        sources=[ChangeSource.AUTOMATIC_RULE, ChangeSource.MANUAL],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.DECISION_FINAL,
        to_state=CourtState.EXEC_DOC_REQUESTED,
        trigger="exec_doc_request_filed",
        sources=[ChangeSource.MANUAL],
        allowed_roles=[UserRole.LAWYER, UserRole.LEGAL_HEAD],
    ),
    Transition(
        dimension="court_state",
        from_state=CourtState.EXEC_DOC_REQUESTED,
        to_state=CourtState.EXEC_DOC_RECEIVED,
        trigger="exec_doc_received",
        sources=[ChangeSource.MANUAL, ChangeSource.INTEGRATION],
        side_effects=[
            SideEffect(
                create_task={"title": "Подати ВД на виконання", "module": "enforcement", "priority": "HIGH"},
                notify_roles=[UserRole.ENFORCEMENT_HEAD],
            ),
        ],
    ),
    # Appeal from any post-decision state
    Transition(
        dimension="court_state",
        from_state=CourtState.DECISION_ISSUED,
        to_state=CourtState.APPEAL,
        trigger="appeal_filed",
        sources=[ChangeSource.MANUAL, ChangeSource.INTEGRATION],
        side_effects=[
            SideEffect(notify_roles=[UserRole.LAWYER, UserRole.LEGAL_HEAD]),
        ],
    ),
]

# =============================================================================
# ENFORCEMENT STATE TRANSITIONS
# =============================================================================

ENFORCEMENT_STATE_TRANSITIONS = [
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.PACKAGE_PREP,
        to_state=EnforcementState.SUBMITTED,
        trigger="exec_doc_submitted_to_executor",
        sources=[ChangeSource.MANUAL],
        allowed_roles=[UserRole.ENFORCEMENT_SPECIALIST, UserRole.ENFORCEMENT_HEAD],
    ),
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.SUBMITTED,
        to_state=EnforcementState.RETURNED_NO_OPEN,
        trigger="exec_doc_returned_without_opening",
        sources=[ChangeSource.MANUAL, ChangeSource.INTEGRATION],
        side_effects=[
            SideEffect(
                create_task={"title": "Виправити та переподати ВД", "module": "enforcement", "priority": "HIGH"},
                notify_roles=[UserRole.ENFORCEMENT_HEAD],
            ),
        ],
    ),
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.SUBMITTED,
        to_state=EnforcementState.OPENED,
        trigger="enforcement_proceeding_opened",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
        side_effects=[
            SideEffect(
                update_dimension={"dimension": "global_lifecycle", "new_value": GlobalLifecycle.ENFORCEMENT},
                notify_roles=[UserRole.ENFORCEMENT_SPECIALIST, UserRole.ENFORCEMENT_HEAD],
            ),
        ],
    ),
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.OPENED,
        to_state=EnforcementState.SEARCH_ASSETS,
        trigger="asset_search_initiated",
        sources=[ChangeSource.MANUAL, ChangeSource.INTEGRATION],
    ),
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.SEARCH_ASSETS,
        to_state=EnforcementState.GARNISHMENT,
        trigger="garnishment_order_issued",
        sources=[ChangeSource.INTEGRATION, ChangeSource.MANUAL],
    ),
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.OPENED,
        to_state=EnforcementState.SUSPENDED,
        trigger="enforcement_suspended",
        sources=[ChangeSource.MANUAL, ChangeSource.INTEGRATION],
        side_effects=[
            SideEffect(notify_roles=[UserRole.ENFORCEMENT_HEAD]),
        ],
    ),
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.GARNISHMENT,
        to_state=EnforcementState.PARTIAL_RECOVERY,
        trigger="partial_amount_recovered",
        sources=[ChangeSource.AUTOMATIC_RULE],
    ),
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.PARTIAL_RECOVERY,
        to_state=EnforcementState.CLOSED_RECOVERED,
        trigger="full_amount_recovered",
        sources=[ChangeSource.AUTOMATIC_RULE],
        side_effects=[
            SideEffect(notify_roles=[UserRole.DIRECTOR, UserRole.FINANCE_MANAGER]),
        ],
    ),
    Transition(
        dimension="enforcement_state",
        from_state="*_ACTIVE_ENFORCEMENT",
        to_state=EnforcementState.CLOSED_NO_RECOVERY,
        trigger="enforcement_closed_no_result",
        sources=[ChangeSource.MANUAL, ChangeSource.INTEGRATION],
        requires_reason=True,
        side_effects=[
            SideEffect(notify_roles=[UserRole.ENFORCEMENT_HEAD, UserRole.DIRECTOR]),
        ],
    ),
    # Re-submission after return
    Transition(
        dimension="enforcement_state",
        from_state=EnforcementState.RETURNED_NO_OPEN,
        to_state=EnforcementState.SUBMITTED,
        trigger="exec_doc_resubmitted",
        sources=[ChangeSource.MANUAL],
        allowed_roles=[UserRole.ENFORCEMENT_SPECIALIST, UserRole.ENFORCEMENT_HEAD],
    ),
]

# =============================================================================
# PAYMENT STATE TRANSITIONS
# =============================================================================

PAYMENT_STATE_TRANSITIONS = [
    Transition(
        dimension="payment_state",
        from_state=PaymentState.NO_PAYMENTS,
        to_state=PaymentState.AD_HOC_PAYMENT,
        trigger="first_payment_received",
        sources=[ChangeSource.AUTOMATIC_RULE],
    ),
    Transition(
        dimension="payment_state",
        from_state=PaymentState.NO_PAYMENTS,
        to_state=PaymentState.ACTIVE_INSTALLMENT,
        trigger="installment_plan_activated",
        sources=[ChangeSource.MANUAL, ChangeSource.AUTOMATIC_RULE],
    ),
    Transition(
        dimension="payment_state",
        from_state=PaymentState.AD_HOC_PAYMENT,
        to_state=PaymentState.PARTIAL_PAYMENT,
        trigger="multiple_payments_received",
        sources=[ChangeSource.AUTOMATIC_RULE],
    ),
    Transition(
        dimension="payment_state",
        from_state=PaymentState.AD_HOC_PAYMENT,
        to_state=PaymentState.ACTIVE_INSTALLMENT,
        trigger="installment_plan_activated",
        sources=[ChangeSource.MANUAL],
    ),
    Transition(
        dimension="payment_state",
        from_state=PaymentState.ACTIVE_INSTALLMENT,
        to_state=PaymentState.BROKEN_INSTALLMENT,
        trigger="installment_payment_overdue_60_days",
        sources=[ChangeSource.AUTOMATIC_RULE],
        side_effects=[
            SideEffect(
                create_task={"title": "Реактивація стягнення після зриву розстрочки", "module": "call_center", "priority": "HIGH"},
                notify_roles=[UserRole.CALL_CENTER_OPERATOR, UserRole.DIRECTOR],
            ),
        ],
    ),
    Transition(
        dimension="payment_state",
        from_state=PaymentState.BROKEN_INSTALLMENT,
        to_state=PaymentState.ACTIVE_INSTALLMENT,
        trigger="installment_resumed",
        sources=[ChangeSource.MANUAL],
    ),
    Transition(
        dimension="payment_state",
        from_state="*_ANY_ACTIVE",
        to_state=PaymentState.FORCED_REGULAR,
        trigger="regular_garnishment_established",
        sources=[ChangeSource.AUTOMATIC_RULE],
    ),
    # Any state → FULLY_PAID
    Transition(
        dimension="payment_state",
        from_state="*",
        to_state=PaymentState.FULLY_PAID,
        trigger="debt_fully_paid",
        sources=[ChangeSource.AUTOMATIC_RULE],
        side_effects=[
            SideEffect(
                update_dimension={"dimension": "global_lifecycle", "new_value": GlobalLifecycle.CLOSED_COLLECTED},
                notify_roles=[UserRole.DIRECTOR, UserRole.FINANCE_MANAGER],
            ),
        ],
    ),
]

# =============================================================================
# ALL TRANSITIONS REGISTRY
# =============================================================================

ALL_TRANSITIONS = (
    GLOBAL_LIFECYCLE_TRANSITIONS
    + CALL_CENTER_TRANSITIONS
    + COURT_STATE_TRANSITIONS
    + ENFORCEMENT_STATE_TRANSITIONS
    + PAYMENT_STATE_TRANSITIONS
)


def get_transitions_for_dimension(dimension: str) -> list[Transition]:
    """Return all transitions for a given state dimension."""
    return [t for t in ALL_TRANSITIONS if t.dimension == dimension]


def get_allowed_transitions(dimension: str, current_state: str) -> list[Transition]:
    """Return transitions available from the current state in a dimension."""
    return [
        t for t in ALL_TRANSITIONS
        if t.dimension == dimension
        and (t.from_state == current_state or t.from_state.startswith("*"))
    ]
