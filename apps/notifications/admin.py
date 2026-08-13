from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.notifications.models import DeviceToken, Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(RoleGatedAdmin):
    list_display = ("user", "event_type", "title", "read_at", "created_at")
    list_filter = ("event_type", "read_at")
    search_fields = ("user__email", "title")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(RoleGatedAdmin):
    list_display = ("user", "event_type", "channel", "enabled")
    list_filter = ("channel", "enabled")


@admin.register(DeviceToken)
class DeviceTokenAdmin(RoleGatedAdmin):
    list_display = ("user", "platform", "token", "is_active", "created_at")
    list_filter = ("platform", "is_active")
