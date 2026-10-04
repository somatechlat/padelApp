import csv

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.adminpanel.admin_base import FINANCIAL_ROLES
from apps.adminpanel.mixins import ManagerRequiredMixin, require_roles, user_role
from apps.bookings.models import Booking
from apps.payments.models import Payment

User = get_user_model()


class ReportsAdminView(ManagerRequiredMixin, TemplateView):
    """gerente and above may read the reports page.

    Booking counts are visible to managers. Revenue, per-court income and the
    top-customers list (customer emails) are dueno/superadmin only, as is the
    CSV export."""

    template_name = "adminpanel/reports.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        start_month = today.replace(day=1)

        ctx["bookings_by_status"] = Booking.objects.values("status").annotate(count=Count("id"))

        # Money figures and customer PII are owner-only. Managers get the
        # operational booking counts; nothing else is even computed, so a
        # template slip cannot leak revenue to them.
        can_see_revenue = user_role(self.request.user) in FINANCIAL_ROLES
        ctx["can_see_revenue"] = can_see_revenue
        if can_see_revenue:
            ctx["month_revenue"] = (
                Payment.objects.filter(
                    status__in=("captured", "confirmed"),
                    created_at__date__gte=start_month,
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )
            ctx["revenue_by_court"] = (
                Payment.objects.filter(status__in=("captured", "confirmed"))
                .values("booking__court__name")
                .annotate(total=Sum("amount"))
            )
            ctx["top_customers"] = User.objects.annotate(booking_count=Count("bookings")).order_by(
                "-booking_count"
            )[:10]

        return ctx

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            return self._export_csv(request)
        return super().get(request, *args, **kwargs)

    def _export_csv(self, request):
        require_roles(request, FINANCIAL_ROLES)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="andes_padel_report.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID Reserva", "Fecha", "Cliente", "Cancha", "Precio", "Estado"])
        for b in Booking.objects.select_related("user", "court").order_by("-date")[:500]:
            writer.writerow([b.id, b.date, b.user.email, b.court.name, b.price, b.status])
        return response
