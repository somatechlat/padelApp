from django.views.generic import ListView

from apps.adminpanel.mixins import FinanceRequiredMixin
from apps.security.models import AuditLog


class AuditListView(FinanceRequiredMixin, ListView):
    """Full audit trail — dueno/superadmin only."""

    template_name = "adminpanel/audit.html"
    context_object_name = "entries"
    paginate_by = 50
    model = AuditLog

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user")
        action = self.request.GET.get("action", "")
        entity = self.request.GET.get("entity", "")
        user = self.request.GET.get("user", "")
        if action:
            qs = qs.filter(action=action)
        if entity:
            qs = qs.filter(entity=entity)
        if user:
            qs = qs.filter(user__email__icontains=user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = (
            AuditLog.objects.order_by("action").values_list("action", flat=True).distinct()[:50]
        )
        ctx["entities"] = (
            AuditLog.objects.order_by("entity").values_list("entity", flat=True).distinct()[:50]
        )
        return ctx
