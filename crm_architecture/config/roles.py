"""
Role-based access control configuration.

Defines what each role can do across different modules and entity types.
"""

from dataclasses import dataclass, field

from ..models.enums import UserRole


@dataclass
class ModulePermission:
    """Permissions for a specific module."""
    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False
    can_change_status: bool = False
    can_mass_action: bool = False


@dataclass
class RoleDefinition:
    """Complete permission set for a role."""
    role: UserRole
    description_ua: str
    modules: dict[str, ModulePermission] = field(default_factory=dict)
    can_close_case: bool = False
    can_view_all_cases: bool = False
    can_view_analytics: bool = False
    can_manage_users: bool = False
    can_export_data: bool = False


# =============================================================================
# ROLE DEFINITIONS
# =============================================================================

ROLE_DEFINITIONS: dict[UserRole, RoleDefinition] = {
    UserRole.DIRECTOR: RoleDefinition(
        role=UserRole.DIRECTOR,
        description_ua="Директор / власник — повний доступ до всіх модулів та звітів",
        modules={
            "call_center": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
            "legal_prep": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
            "court": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
            "enforcement": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
            "payments": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
            "documents": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
        },
        can_close_case=True,
        can_view_all_cases=True,
        can_view_analytics=True,
        can_manage_users=True,
        can_export_data=True,
    ),

    UserRole.CALL_CENTER_OPERATOR: RoleDefinition(
        role=UserRole.CALL_CENTER_OPERATOR,
        description_ua="Оператор кол-центру — дзвінки, контакти, обіцянки, задачі",
        modules={
            "call_center": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=False),
            "legal_prep": ModulePermission(can_view=True),
            "court": ModulePermission(can_view=True),
            "enforcement": ModulePermission(can_view=True),
            "payments": ModulePermission(can_view=True),
            "documents": ModulePermission(can_view=True, can_create=True),
        },
        can_close_case=False,
        can_view_all_cases=False,
        can_view_analytics=False,
    ),

    UserRole.LEGAL_HEAD: RoleDefinition(
        role=UserRole.LEGAL_HEAD,
        description_ua="Керівник юрвідділу — погодження подач, контроль строків, шаблони",
        modules={
            "call_center": ModulePermission(can_view=True),
            "legal_prep": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
            "court": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
            "enforcement": ModulePermission(can_view=True),
            "payments": ModulePermission(can_view=True),
            "documents": ModulePermission(can_view=True, can_create=True, can_edit=True),
        },
        can_close_case=True,
        can_view_all_cases=True,
        can_view_analytics=True,
        can_export_data=True,
    ),

    UserRole.LAWYER: RoleDefinition(
        role=UserRole.LAWYER,
        description_ua="Юрист — процесуальні документи, судові події",
        modules={
            "call_center": ModulePermission(can_view=True),
            "legal_prep": ModulePermission(can_view=True, can_create=True, can_edit=True),
            "court": ModulePermission(can_view=True, can_create=True, can_edit=True, can_change_status=True),
            "enforcement": ModulePermission(can_view=True),
            "payments": ModulePermission(can_view=True),
            "documents": ModulePermission(can_view=True, can_create=True, can_edit=True),
        },
        can_close_case=False,
        can_view_all_cases=False,
        can_view_analytics=False,
    ),

    UserRole.ENFORCEMENT_HEAD: RoleDefinition(
        role=UserRole.ENFORCEMENT_HEAD,
        description_ua="Керівник виконавчого напряму — масові зміни, маршрутизація, KPI",
        modules={
            "call_center": ModulePermission(can_view=True),
            "legal_prep": ModulePermission(can_view=True),
            "court": ModulePermission(can_view=True),
            "enforcement": ModulePermission(can_view=True, can_create=True, can_edit=True, can_delete=False, can_change_status=True, can_mass_action=True),
            "payments": ModulePermission(can_view=True),
            "documents": ModulePermission(can_view=True, can_create=True),
        },
        can_close_case=True,
        can_view_all_cases=True,
        can_view_analytics=True,
        can_export_data=True,
    ),

    UserRole.ENFORCEMENT_SPECIALIST: RoleDefinition(
        role=UserRole.ENFORCEMENT_SPECIALIST,
        description_ua="Спеціаліст виконання — ведення ВП, листування, документи",
        modules={
            "call_center": ModulePermission(can_view=True),
            "legal_prep": ModulePermission(can_view=True),
            "court": ModulePermission(can_view=True),
            "enforcement": ModulePermission(can_view=True, can_create=True, can_edit=True, can_change_status=True),
            "payments": ModulePermission(can_view=True),
            "documents": ModulePermission(can_view=True, can_create=True),
        },
        can_close_case=False,
        can_view_all_cases=False,
    ),

    UserRole.DOCUMENT_CLERK: RoleDefinition(
        role=UserRole.DOCUMENT_CLERK,
        description_ua="Документообіг / архів — завантаження, реєстрація, друк, пошта",
        modules={
            "call_center": ModulePermission(can_view=True),
            "legal_prep": ModulePermission(can_view=True),
            "court": ModulePermission(can_view=True),
            "enforcement": ModulePermission(can_view=True),
            "payments": ModulePermission(can_view=True),
            "documents": ModulePermission(can_view=True, can_create=True, can_edit=True, can_change_status=True),
        },
        can_close_case=False,
        can_view_all_cases=True,
    ),

    UserRole.FINANCE_MANAGER: RoleDefinition(
        role=UserRole.FINANCE_MANAGER,
        description_ua="Фінансовий менеджер / бухгалтерія — платежі, проводки, звіти",
        modules={
            "call_center": ModulePermission(can_view=True),
            "legal_prep": ModulePermission(can_view=True),
            "court": ModulePermission(can_view=True),
            "enforcement": ModulePermission(can_view=True),
            "payments": ModulePermission(can_view=True, can_create=True, can_edit=True, can_change_status=True),
            "documents": ModulePermission(can_view=True),
        },
        can_close_case=False,
        can_view_all_cases=True,
        can_view_analytics=True,
        can_export_data=True,
    ),
}


def get_role_permissions(role: UserRole) -> RoleDefinition:
    """Get the full permission definition for a role."""
    return ROLE_DEFINITIONS[role]


def can_user_access_module(role: UserRole, module: str, action: str) -> bool:
    """Check if a role can perform a specific action on a module."""
    role_def = ROLE_DEFINITIONS.get(role)
    if role_def is None:
        return False
    module_perm = role_def.modules.get(module)
    if module_perm is None:
        return False
    return getattr(module_perm, f"can_{action}", False)
