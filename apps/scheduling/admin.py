from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.scheduling.models import BookingHold, MaintenanceWindow, TimeSlot


@admin.register(TimeSlot)
class TimeSlotAdmin(RoleGatedAdmin):
    list_display = ("court", "date", "start", "end", "status")
    list_filter = ("status", "date")
    search_fields = ("court__name",)
    date_hierarchy = "date"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MaintenanceWindow)
class MaintenanceWindowAdmin(RoleGatedAdmin):
    list_display = ("court", "start", "end", "reason")
    list_filter = ("court",)


@admin.register(BookingHold)
class BookingHoldAdmin(RoleGatedAdmin):
    list_display = ("court", "user", "slot", "expires_at", "is_expired")
    list_filter = ("court",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
