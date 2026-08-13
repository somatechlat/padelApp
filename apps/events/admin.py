from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.events.models import Event, NewsPost, Tournament, TournamentRegistration


@admin.register(Event)
class EventAdmin(RoleGatedAdmin):
    list_display = ("title_localized", "status", "start_at", "end_at", "location")
    list_filter = ("status",)
    search_fields = ("title", "title_es")


@admin.register(Tournament)
class TournamentAdmin(RoleGatedAdmin):
    list_display = (
        "name_localized", "status", "start_date", "end_date",
        "capacity", "confirmed_count", "price", "registration_deadline",
    )
    list_filter = ("status",)
    search_fields = ("name", "name_es")


@admin.register(TournamentRegistration)
class TournamentRegistrationAdmin(RoleGatedAdmin):
    list_display = ("tournament", "user", "status", "created_at")
    list_filter = ("status", "tournament")

    def has_add_permission(self, request):
        return False


@admin.register(NewsPost)
class NewsPostAdmin(RoleGatedAdmin):
    list_display = ("title_localized", "status", "published_at", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "title_es")
