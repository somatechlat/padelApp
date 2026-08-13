from django.contrib import admin, messages
from django.utils.translation import ngettext

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.bookings.models import Booking, BookingEvent, BookingSlot


class BookingSlotInline(admin.TabularInline):
    model = BookingSlot
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class BookingEventInline(admin.TabularInline):
    model = BookingEvent
    extra = 0
    can_delete = False
    readonly_fields = ("from_status", "to_status", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(RoleGatedAdmin):
    list_display = (
        "user", "court", "date", "start_time", "end_time", "duration_minutes", "price", "status",
    )
    list_filter = ("status", "date", "court")
    search_fields = ("user__email", "user__full_name", "court__name")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
    inlines = (BookingSlotInline, BookingEventInline)
    actions = ("mark_confirmed", "mark_cancelled")

    @admin.action(description="Confirmar reservas seleccionadas")
    def mark_confirmed(self, request, queryset):
        updated = 0
        for booking in queryset:
            try:
                booking.transition_to(Booking.Status.CONFIRMED)
                updated += 1
            except ValueError:
                continue
        self.message_user(
            request,
            ngettext(
                "%d reserva confirmada.", "%d reservas confirmadas.", updated
            ) % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Cancelar reservas seleccionadas")
    def mark_cancelled(self, request, queryset):
        updated = 0
        for booking in queryset:
            try:
                booking.transition_to(Booking.Status.CANCELLED)
                updated += 1
            except ValueError:
                continue
        self.message_user(
            request,
            ngettext(
                "%d reserva cancelada.", "%d reservas canceladas.", updated
            ) % updated,
            messages.SUCCESS,
        )


@admin.register(BookingEvent)
class BookingEventAdmin(RoleGatedAdmin):
    list_display = ("booking", "from_status", "to_status", "created_at")
    list_filter = ("from_status", "to_status")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
