from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.policies.models import CancellationPolicy


@admin.register(CancellationPolicy)
class CancellationPolicyAdmin(RoleGatedAdmin):
    list_display = (
        "venue", "free_window_hours", "penalty_ratio", "no_show_ratio", "hold_minutes", "active",
    )
    list_filter = ("active", "venue")
