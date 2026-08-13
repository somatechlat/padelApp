from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.security.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(RoleGatedAdmin):
    list_display = ("created_at", "user", "action", "entity", "entity_id", "ip")
    list_filter = ("action", "entity")
    search_fields = ("user__email", "entity", "entity_id", "ip")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
