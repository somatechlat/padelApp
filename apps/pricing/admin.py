from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.pricing.models import Holiday, PriceRule


@admin.register(PriceRule)
class PriceRuleAdmin(RoleGatedAdmin):
    list_display = (
        "name",
        "venue",
        "zone",
        "day_scope_display",
        "court_type",
        "start_time",
        "end_time",
        "price",
        "multiplier",
        "priority",
        "active",
    )
    list_filter = ("zone", "scope", "active", "venue")
    search_fields = ("name",)


@admin.register(Holiday)
class HolidayAdmin(RoleGatedAdmin):
    list_display = ("venue", "date", "name")
    list_filter = ("venue",)
