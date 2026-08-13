from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.courts.models import Court, CourtSchedule, Venue


@admin.register(Venue)
class VenueAdmin(RoleGatedAdmin):
    list_display = ("name", "address", "timezone", "currency", "active")
    search_fields = ("name", "address")


@admin.register(Court)
class CourtAdmin(RoleGatedAdmin):
    list_display = ("name", "venue", "court_type", "price_base", "status")
    list_filter = ("court_type", "status", "venue")
    search_fields = ("name", "venue__name")


@admin.register(CourtSchedule)
class CourtScheduleAdmin(RoleGatedAdmin):
    list_display = ("court", "weekday", "open_time", "close_time", "is_active")
    list_filter = ("is_active", "weekday")
    search_fields = ("court__name",)
