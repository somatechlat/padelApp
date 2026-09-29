"""Role-scoped access control for the staff admin panel.

Role hierarchy (low to high):
    cliente < recepcionista < gerente < dueno < superadmin

View mixins below gate whole views. Use `require_roles` inside a `post()`
handler when a single view mixes privileged and routine actions.
"""

from typing import ClassVar

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from apps.adminpanel.admin_base import FINANCIAL_ROLES, MANAGER_ROLES, STAFF_ROLES

ROLE_LEVEL = {
    "cliente": 0,
    "recepcionista": 1,
    "gerente": 2,
    "dueno": 3,
    "superadmin": 4,
}


def user_role(user):
    return getattr(user, "role", None)


def role_level(role):
    return ROLE_LEVEL.get(role, 0)


def require_roles(request, roles):
    """Raise PermissionDenied when the acting user's role is not in `roles`."""
    if user_role(request.user) not in roles:
        raise PermissionDenied("Tu rol no tiene permiso para esta accion.")


class StaffRequiredMixin(LoginRequiredMixin):
    """Any staff role may enter. Clients and anonymous users may not."""

    login_url = "/adminpanel/login/"
    allowed_roles: ClassVar[tuple[str, ...]] = STAFF_ROLES

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user_role(user) not in self.allowed_roles:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ManagerRequiredMixin(StaffRequiredMixin):
    """gerente and above — operational management and non-destructive reports."""

    allowed_roles = MANAGER_ROLES


class FinanceRequiredMixin(StaffRequiredMixin):
    """dueno/superadmin only — refunds, bank details, pricing, policies, audit,
    and role changes."""

    allowed_roles = FINANCIAL_ROLES
