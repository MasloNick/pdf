"""
All status enums for the multi-dimensional CRM state model.

Each dimension of a credit case state is represented by a separate enum.
A credit case can have simultaneous active states across multiple dimensions
without conflict.
"""

import enum


class GlobalLifecycle(str, enum.Enum):
    """Main lifecycle stage of a credit case. Exactly one per case."""

    IMPORTED = "IMPORTED"                       # Завантажено, не перевірено
    VERIFICATION = "VERIFICATION"               # Перевірка даних і документів
    PRE_COLLECTION = "PRE_COLLECTION"           # Досудова робота
    LITIGATION = "LITIGATION"                   # Позов поданий / судовий контур
    ENFORCEMENT = "ENFORCEMENT"                 # ВД в роботі у виконавця
    CLOSED_COLLECTED = "CLOSED_COLLECTED"       # Борг погашено
    CLOSED_UNCOLLECTIBLE = "CLOSED_UNCOLLECTIBLE"  # Без перспективи
    ARCHIVED = "ARCHIVED"                       # Для історії та звітності


class CallCenterState(str, enum.Enum):
    """Call-center module state. Optional (0..1 per case)."""

    NEW = "NEW"                         # Необроблений
    NO_VALID_CONTACT = "NO_VALID_CONTACT"  # Недійсний контакт
    CALLBACK = "CALLBACK"               # Передзвонити (з датою)
    CONTACTED = "CONTACTED"             # Був зв'язок, без результату
    NEGOTIATION = "NEGOTIATION"         # Тривають перемовини
    PROMISE = "PROMISE"                 # Обіцянка оплати / гарантійний лист
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT"  # Часткова оплата
    REFUSAL = "REFUSAL"                 # Явна відмова
    DORMANT = "DORMANT"                 # Без активності > N днів
    STOP_CONTACT = "STOP_CONTACT"       # Контакти припинені


class LegalPrepState(str, enum.Enum):
    """Legal preparation module state. Optional (0..1 per case)."""

    TO_ANALYZE = "TO_ANALYZE"               # Потребує аналізу
    DATA_GAP = "DATA_GAP"                   # Брак даних / документів
    READY_FOR_CLAIM = "READY_FOR_CLAIM"     # Готово до позову
    ON_HOLD_SETTLEMENT = "ON_HOLD_SETTLEMENT"  # Пауза через перемовини
    NOT_PROFITABLE = "NOT_PROFITABLE"       # Недоцільно подавати
    APPROVED_FOR_FILING = "APPROVED_FOR_FILING"  # Погоджено подання


class CourtState(str, enum.Enum):
    """Court proceedings module state. Optional (0..1 per case)."""

    DRAFTING = "DRAFTING"                   # Готується позов
    FILED = "FILED"                         # Подано позов
    WITHOUT_MOTION = "WITHOUT_MOTION"       # Залишено без руху
    OPENED = "OPENED"                       # Відкрито провадження
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"  # Отримано відзив
    HEARING = "HEARING"                     # Призначено розгляд
    DECISION_ISSUED = "DECISION_ISSUED"     # Є рішення
    DECISION_FINAL = "DECISION_FINAL"       # Набрало законної сили
    EXEC_DOC_REQUESTED = "EXEC_DOC_REQUESTED"  # Запитано ВД
    EXEC_DOC_RECEIVED = "EXEC_DOC_RECEIVED"    # ВД отримано
    APPEAL = "APPEAL"                       # Апеляція / оскарження


class EnforcementState(str, enum.Enum):
    """Enforcement proceedings module state. Optional (0..1 per case)."""

    PACKAGE_PREP = "PACKAGE_PREP"           # Готується пакет
    SUBMITTED = "SUBMITTED"                 # Подано ВД
    RETURNED_NO_OPEN = "RETURNED_NO_OPEN"   # Повернуто без відкриття
    OPENED = "OPENED"                       # ВП відкрито
    SEARCH_ASSETS = "SEARCH_ASSETS"         # Пошук активів
    GARNISHMENT = "GARNISHMENT"             # Стягнення із зарплати/рахунків
    SUSPENDED = "SUSPENDED"                 # ВП зупинене
    PARTIAL_RECOVERY = "PARTIAL_RECOVERY"   # Частково стягнуто
    CLOSED_RECOVERED = "CLOSED_RECOVERED"   # Завершено зі стягненням
    CLOSED_NO_RECOVERY = "CLOSED_NO_RECOVERY"  # Завершено без стягнення


class PaymentState(str, enum.Enum):
    """Payment state. Exactly one per case, independent of other dimensions."""

    NO_PAYMENTS = "NO_PAYMENTS"             # Немає оплат
    AD_HOC_PAYMENT = "AD_HOC_PAYMENT"       # Разова / епізодична оплата
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT"     # Часткова оплата
    ACTIVE_INSTALLMENT = "ACTIVE_INSTALLMENT"  # Активна розстрочка
    BROKEN_INSTALLMENT = "BROKEN_INSTALLMENT"  # Порушена розстрочка
    FORCED_REGULAR = "FORCED_REGULAR"       # Регулярне примусове стягнення
    FULLY_PAID = "FULLY_PAID"               # Повністю сплачено


class RiskFlag(str, enum.Enum):
    """Risk flags. A case can have 0..N flags simultaneously."""

    DECEASED = "DECEASED"                   # Ознаки смерті
    BANKRUPTCY_RISK = "BANKRUPTCY_RISK"     # Банкрутство / неплатоспроможність
    INVALID_CONTACT = "INVALID_CONTACT"     # Недійсний контакт
    ADDRESS_UNKNOWN = "ADDRESS_UNKNOWN"     # Відсутня адреса
    NO_ORIGINALS = "NO_ORIGINALS"           # Немає оригіналів документів
    LIMITATION_RISK = "LIMITATION_RISK"     # Ризик позовної давності
    DUPLICATE_PERSON = "DUPLICATE_PERSON"   # Дублікат / пов'язані справи
    VIP_CONTROL = "VIP_CONTROL"             # Контроль керівництва


class TaskPriority(str, enum.Enum):
    """Task priority levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskStatus(str, enum.Enum):
    """Task execution status."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class EventType(str, enum.Enum):
    """Types of events in the immutable event log."""

    STATUS_CHANGE = "STATUS_CHANGE"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    CALL_MADE = "CALL_MADE"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    CLAIM_FILED = "CLAIM_FILED"
    COURT_EVENT = "COURT_EVENT"
    ENFORCEMENT_EVENT = "ENFORCEMENT_EVENT"
    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    FLAG_SET = "FLAG_SET"
    FLAG_REMOVED = "FLAG_REMOVED"
    CASE_IMPORTED = "CASE_IMPORTED"
    MANUAL_NOTE = "MANUAL_NOTE"
    INSTALLMENT_CREATED = "INSTALLMENT_CREATED"
    INSTALLMENT_BROKEN = "INSTALLMENT_BROKEN"
    ESCALATION = "ESCALATION"


class UserRole(str, enum.Enum):
    """System roles for access control."""

    DIRECTOR = "DIRECTOR"
    CALL_CENTER_OPERATOR = "CALL_CENTER_OPERATOR"
    LEGAL_HEAD = "LEGAL_HEAD"
    LAWYER = "LAWYER"
    ENFORCEMENT_HEAD = "ENFORCEMENT_HEAD"
    ENFORCEMENT_SPECIALIST = "ENFORCEMENT_SPECIALIST"
    DOCUMENT_CLERK = "DOCUMENT_CLERK"
    FINANCE_MANAGER = "FINANCE_MANAGER"


class ChangeSource(str, enum.Enum):
    """Source of a state change for audit trail."""

    MANUAL = "MANUAL"               # User action
    AUTOMATIC_RULE = "AUTOMATIC_RULE"  # Business rule trigger
    INTEGRATION = "INTEGRATION"     # External system (ESITS, bank, etc.)
    IMPORT = "IMPORT"               # Batch import
    SYSTEM = "SYSTEM"               # Internal system process
