"""
Validation logic for state transitions.

Ensures:
- Transition is allowed from the current state
- User has the required role for manual transitions
- Required reason is provided for critical transitions
- Side effects are properly triggered
"""

from dataclasses import dataclass
from typing import Optional

from ..models.enums import ChangeSource, UserRole
from .transitions import Transition, get_allowed_transitions, ALL_TRANSITIONS


@dataclass
class ValidationResult:
    """Result of a transition validation check."""
    is_valid: bool
    error: Optional[str] = None
    transition: Optional[Transition] = None


def validate_transition(
    dimension: str,
    current_state: str,
    target_state: str,
    source: ChangeSource,
    user_role: Optional[UserRole] = None,
    reason: Optional[str] = None,
) -> ValidationResult:
    """
    Validate whether a state transition is allowed.

    Rules:
    1. The transition must exist in the registry
    2. The source (manual/auto/integration) must be allowed
    3. For manual transitions, the user role must be in allowed_roles
    4. If requires_reason=True, a reason must be provided
    """
    allowed = get_allowed_transitions(dimension, current_state)
    matching = [t for t in allowed if t.to_state == target_state or str(t.to_state) == target_state]

    if not matching:
        return ValidationResult(
            is_valid=False,
            error=(
                f"Перехід {current_state} → {target_state} не дозволений "
                f"у вимірі '{dimension}'"
            ),
        )

    transition = matching[0]

    # Check source is allowed
    if source not in transition.sources:
        return ValidationResult(
            is_valid=False,
            error=(
                f"Джерело '{source.value}' не може ініціювати перехід "
                f"{current_state} → {target_state}"
            ),
        )

    # Check role for manual transitions
    if source == ChangeSource.MANUAL:
        if transition.allowed_roles and user_role not in transition.allowed_roles:
            return ValidationResult(
                is_valid=False,
                error=(
                    f"Роль '{user_role}' не має права на перехід "
                    f"{current_state} → {target_state}. "
                    f"Дозволені ролі: {[r.value for r in transition.allowed_roles]}"
                ),
            )

    # Check reason requirement
    if transition.requires_reason and not reason:
        return ValidationResult(
            is_valid=False,
            error=(
                f"Перехід {current_state} → {target_state} вимагає "
                f"обов'язкового коментаря (причини)"
            ),
        )

    return ValidationResult(is_valid=True, transition=transition)


# =============================================================================
# BUSINESS RULES: constraints that prevent invalid system states
# =============================================================================

BUSINESS_RULES = {
    "no_backward_lifecycle_on_payment": {
        "description": (
            "Global lifecycle NEVER goes back to PRE_COLLECTION from LITIGATION "
            "or ENFORCEMENT just because a payment was received. "
            "Only the payment_state changes."
        ),
    },
    "close_uncollectible_requires_manager": {
        "description": (
            "CLOSED_UNCOLLECTIBLE can only be set by DIRECTOR, LEGAL_HEAD, "
            "or ENFORCEMENT_HEAD with a mandatory reason."
        ),
    },
    "financial_facts_are_automatic": {
        "description": (
            "Payment facts must come from the financial system (bank/accounting), "
            "not from manual user input without verification."
        ),
    },
    "critical_flags_need_verification": {
        "description": (
            "DECEASED and BANKRUPTCY_RISK flags require verified source data, "
            "not casual clicks."
        ),
    },
    "event_log_is_immutable": {
        "description": (
            "Event log records are NEVER modified or deleted. "
            "They form the audit trail and analytics foundation."
        ),
    },
    "modules_are_independent": {
        "description": (
            "A court state change does NOT directly modify call_center_state. "
            "It can only create events or tasks for the call-center module."
        ),
    },
}
