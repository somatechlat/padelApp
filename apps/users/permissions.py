from rest_framework.permissions import BasePermission


def _is_active_account(user) -> bool:
    """True only for a live account: authenticated, not flagged, status active.

    ``status`` is the product-level lifecycle (suspended/blocked/deleted);
    ``is_active`` is the Django auth switch. A staff role claim on a
    suspended account must not grant anything.
    """
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and getattr(user, "status", "active") == "active"
    )


class IsStaffRole(BasePermission):
    """Recepcionista, gerente, dueno o superadmin."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            _is_active_account(user)
            and user.role in ("recepcionista", "gerente", "dueno", "superadmin")
        )


class IsManagerRole(BasePermission):
    """Gerente, dueno o superadmin."""

    def has_permission(self, request, view):
        user = request.user
        return bool(_is_active_account(user) and user.role in ("gerente", "dueno", "superadmin"))


class IsOwnerOrStaff(BasePermission):
    def has_permission(self, request, view):
        return _is_active_account(request.user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not _is_active_account(user):
            return False
        if user.role in ("gerente", "dueno", "superadmin"):
            return True
        if user.role == "recepcionista" and hasattr(obj, "court"):
            return True
        return getattr(obj, "user_id", None) == user.id
