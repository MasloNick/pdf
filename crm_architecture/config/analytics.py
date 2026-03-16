"""
Analytics and reporting configuration.

Defines metrics, KPIs, and reporting levels for different user roles.
Analytics must be built from event_log and state_history, NOT just current field values.
"""

from dataclasses import dataclass, field
from typing import Optional

from ..models.enums import UserRole


@dataclass
class Metric:
    """Definition of a single analytics metric."""
    code: str
    name_ua: str
    description_ua: str
    source: str  # "state_history", "event_log", "payments", "tasks"
    formula: Optional[str] = None
    visible_to: list[UserRole] = field(default_factory=list)


# =============================================================================
# CORE METRICS
# =============================================================================

METRICS: list[Metric] = [
    # --- Funnel metrics ---
    Metric(
        code="funnel_conversion",
        name_ua="Воронка конверсій",
        description_ua=(
            "Скільки справ перейшло PRE_COLLECTION → LITIGATION → ENFORCEMENT "
            "→ CLOSED_COLLECTED за період"
        ),
        source="state_history",
        formula="COUNT(transitions) GROUP BY from_state, to_state, period",
        visible_to=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD, UserRole.ENFORCEMENT_HEAD],
    ),
    Metric(
        code="aging_by_stage",
        name_ua="Aging по етапах",
        description_ua="Скільки днів справа знаходиться в кожному етапі/модулі/підстатусі",
        source="state_history",
        formula="DATEDIFF(exit_at, enter_at) per state per case",
        visible_to=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD, UserRole.ENFORCEMENT_HEAD],
    ),
    Metric(
        code="conversion_rate",
        name_ua="Конверсія між станами",
        description_ua="Частка успішних переходів між станами",
        source="state_history",
        formula="COUNT(successful_transitions) / COUNT(total_cases_in_state)",
        visible_to=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD, UserRole.ENFORCEMENT_HEAD],
    ),

    # --- Financial metrics ---
    Metric(
        code="recovery_rate",
        name_ua="Recovery rate",
        description_ua="Сума стягнення / баланс боргу / сума купівлі портфеля",
        source="payments",
        formula="SUM(payments) / SUM(balance OR purchase_price)",
        visible_to=[UserRole.DIRECTOR, UserRole.FINANCE_MANAGER],
    ),
    Metric(
        code="cash_on_cash",
        name_ua="Cash-on-cash повернення",
        description_ua="Відношення стягнутих коштів до інвестованих по портфелю",
        source="payments",
        formula="SUM(recovered) / portfolio.purchase_price",
        visible_to=[UserRole.DIRECTOR],
    ),
    Metric(
        code="portfolio_roi",
        name_ua="ROI/IRR портфеля",
        description_ua="Портфельна дохідність з урахуванням часу",
        source="payments",
        formula="IRR(purchase_price, cashflows_by_period)",
        visible_to=[UserRole.DIRECTOR],
    ),

    # --- Call-center metrics ---
    Metric(
        code="promise_kept_rate",
        name_ua="Виконання обіцянок оплат",
        description_ua="Скільки обіцянок оплат реально виконано",
        source="event_log",
        formula="COUNT(promise_fulfilled) / COUNT(promise_made)",
        visible_to=[UserRole.DIRECTOR, UserRole.CALL_CENTER_OPERATOR],
    ),
    Metric(
        code="broken_installment_rate",
        name_ua="Частка зірваних розстрочок",
        description_ua="Скільки розстрочок було порушено",
        source="state_history",
        formula="COUNT(BROKEN_INSTALLMENT) / COUNT(ACTIVE_INSTALLMENT)",
        visible_to=[UserRole.DIRECTOR, UserRole.CALL_CENTER_OPERATOR],
    ),
    Metric(
        code="contact_rate",
        name_ua="Рівень контактування",
        description_ua="Частка справ із успішним контактом",
        source="event_log",
        formula="COUNT(CONTACTED+) / COUNT(total_assigned)",
        visible_to=[UserRole.DIRECTOR, UserRole.CALL_CENTER_OPERATOR],
    ),

    # --- Court metrics ---
    Metric(
        code="court_efficiency",
        name_ua="Ефективність суду",
        description_ua="Частка виграних/відкритих/повернутих позовів, строк отримання ВД",
        source="state_history",
        formula="COUNT(DECISION_FINAL) / COUNT(FILED), AVG(days to EXEC_DOC_RECEIVED)",
        visible_to=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD, UserRole.LAWYER],
    ),
    Metric(
        code="without_motion_rate",
        name_ua="Частка залишених без руху",
        description_ua="Позови залишені без руху / всі подані",
        source="state_history",
        formula="COUNT(WITHOUT_MOTION) / COUNT(FILED)",
        visible_to=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD],
    ),

    # --- Enforcement metrics ---
    Metric(
        code="executor_effectiveness",
        name_ua="Ефективність виконавців",
        description_ua="Стягнення, строк, витрати, частка безрезультатних повернень по виконавцю/регіону",
        source="state_history",
        formula="SUM(recovered) per executor, AVG(days), COUNT(CLOSED_NO_RECOVERY)/COUNT(*)",
        visible_to=[UserRole.DIRECTOR, UserRole.ENFORCEMENT_HEAD],
    ),

    # --- Operational metrics ---
    Metric(
        code="sla_compliance",
        name_ua="Виконання SLA",
        description_ua="Частка задач виконаних у строк",
        source="tasks",
        formula="COUNT(completed_on_time) / COUNT(all_completed)",
        visible_to=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD, UserRole.ENFORCEMENT_HEAD],
    ),
    Metric(
        code="overdue_tasks",
        name_ua="Прострочені задачі",
        description_ua="Кількість та частка прострочених задач по співробітнику / відділу",
        source="tasks",
        formula="COUNT(overdue) / COUNT(total), GROUP BY user",
        visible_to=[UserRole.DIRECTOR, UserRole.LEGAL_HEAD, UserRole.ENFORCEMENT_HEAD],
    ),
]


# =============================================================================
# REPORTING LEVELS — what each role sees in dashboards
# =============================================================================

REPORTING_LEVELS = {
    "employee": {
        "description_ua": "Власні справи, прострочені задачі, контакти, обіцянки, SLA, дії за день/тиждень",
        "roles": [UserRole.CALL_CENTER_OPERATOR, UserRole.LAWYER, UserRole.ENFORCEMENT_SPECIALIST, UserRole.DOCUMENT_CLERK],
        "metrics": ["promise_kept_rate", "contact_rate", "sla_compliance", "overdue_tasks"],
    },
    "segment_manager": {
        "description_ua": "Воронка сегменту, конверсії, навантаження, aging, прострочки, суми оплат",
        "roles": [UserRole.LEGAL_HEAD, UserRole.ENFORCEMENT_HEAD],
        "metrics": [
            "funnel_conversion", "aging_by_stage", "conversion_rate",
            "court_efficiency", "executor_effectiveness",
            "sla_compliance", "overdue_tasks",
        ],
    },
    "operations_director": {
        "description_ua": "Загальна воронка по портфелю, частка в суді/виконанні, recovered cash, прогноз, цикл справи",
        "roles": [UserRole.DIRECTOR],
        "metrics": [
            "funnel_conversion", "aging_by_stage", "conversion_rate",
            "recovery_rate", "cash_on_cash", "portfolio_roi",
            "promise_kept_rate", "broken_installment_rate",
            "court_efficiency", "without_motion_rate",
            "executor_effectiveness",
            "sla_compliance", "overdue_tasks",
        ],
    },
    "owners": {
        "description_ua": "Портфельна дохідність, cash-on-cash, ROI/IRR, судова конверсія, прогноз повернення інвестицій",
        "roles": [UserRole.DIRECTOR],
        "metrics": ["recovery_rate", "cash_on_cash", "portfolio_roi", "court_efficiency", "executor_effectiveness"],
    },
}
