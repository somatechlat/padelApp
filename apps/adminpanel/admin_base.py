from django.contrib import admin

FINANCIAL_ROLES = ("dueno", "superadmin")
MANAGER_ROLES = ("gerente", "dueno", "superadmin")
STAFF_ROLES = ("recepcionista", "gerente", "dueno", "superadmin")


class RoleGatedAdmin(admin.ModelAdmin):
    """RBAC: superadmin/dueno = full; gerente = full on non-financial, view/change on
    financial; recepcionista = manage operations but never modify financial models."""

    FINANCIAL = False

    def _can(self, user, action):
        role = getattr(user, "role", None)
        if not user.is_authenticated or role not in STAFF_ROLES:
            return False
        if role in ("superadmin", "dueno"):
            return True
        if role == "gerente":
            if self.FINANCIAL and action in ("add", "delete"):
                return False
            return True
        if self.FINANCIAL:
            return False
        return action in ("view", "add", "change")

    def has_view_permission(self, request, obj=None):
        return self._can(request.user, "view")

    def has_add_permission(self, request):
        return self._can(request.user, "add")

    def has_change_permission(self, request, obj=None):
        return self._can(request.user, "change")

    def has_delete_permission(self, request, obj=None):
        return self._can(request.user, "delete")
