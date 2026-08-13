from django.contrib import admin

from apps.adminpanel.admin_base import RoleGatedAdmin
from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(RoleGatedAdmin):
    FINANCIAL = True
    list_display = ("booking", "user", "method", "amount", "currency", "status", "created_at")
    list_filter = ("method", "status")
    search_fields = ("user__email", "booking__id", "reference", "stripe_payment_intent_id")
    readonly_fields = ("created_at", "updated_at", "stripe_payment_intent_id", "reference")

    def has_add_permission(self, request):
        return False
