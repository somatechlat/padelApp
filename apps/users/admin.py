from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import SkillLevel, User


@admin.register(SkillLevel)
class SkillLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "birth_date", "skill_level", "role", "status", "is_staff")
    list_filter = ("role", "status", "skill_level", "is_staff", "is_active")
    search_fields = ("email", "full_name", "first_name", "last_name", "phone")
    readonly_fields = ("last_login", "date_joined", "email_verified")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Perfil", {"fields": ("first_name", "last_name", "full_name", "birth_date", "skill_level", "phone", "avatar", "language_code")}),
        ("Roles", {"fields": ("role", "status")}),
        ("Permisos", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("Consentimiento", {"fields": ("email_verified", "consent_version", "consent_ts")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
