from rest_framework.permissions import BasePermission


class IsStaffRole(BasePermission):
    """Recepcionista, gerente, dueno o superadmin."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated
            and user.role in ("recepcionista", "gerente", "dueno", "superadmin")
        )


class IsManagerRole(BasePermission):
    """Gerente, dueno o superadmin."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role in ("gerente", "dueno", "superadmin")
        )


class IsOwnerOrStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in ("gerente", "dueno", "superadmin"):
            return True
        if user.role == "recepcionista" and hasattr(obj, "court"):
            return True
        return getattr(obj, "user_id", None) == user.id
