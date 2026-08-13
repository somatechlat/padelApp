from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.verification.models import VerificationCode


@admin.register(VerificationCode)
class VerificationCodeAdmin(RoleGatedAdmin):
    list_display = ("user", "purpose", "code", "expires_at", "attempts", "verified_at")
    list_filter = ("purpose",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
