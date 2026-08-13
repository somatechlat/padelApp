from datetime import time as dt_time

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from apps.adminpanel.admin_base import STAFF_ROLES
from apps.bookings.models import Booking
from apps.courts.models import Court
from apps.payments.models import Payment
from apps.scheduling.models import MaintenanceWindow, TimeSlot
from apps.security.models import AuditLog


class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", None) not in STAFF_ROLES:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        active = ("pending_payment", "confirmed", "in_progress")
        bookings_today = Booking.objects.filter(date=today, status__in=active)
        ctx["bookings_today"] = bookings_today.count()
        ctx["bookings_list"] = bookings_today.select_related("court", "user")[:10]

        slots = TimeSlot.objects.filter(date=today)
        total = slots.count()
        used = slots.filter(status__in=("booked", "held", "blocked")).count()
        ctx["occupancy_pct"] = round(used * 100 / total, 1) if total else 0

        revenue = Payment.objects.filter(
            status__in=("captured", "confirmed"),
            created_at__date=today,
        ).aggregate(total=Sum("amount"))["total"] or 0
        ctx["revenue_today"] = revenue

        ctx["alerts"] = {
            "mantenimiento_hoy": MaintenanceWindow.objects.filter(start__date=today).count(),
            "transferencias_pendientes": Payment.objects.filter(
                status="pending_transfer"
            ).count(),
            "reservas_sin_pagar": Booking.objects.filter(
                status="pending_payment", date__gte=today
            ).count(),
        }
        return ctx


class CalendarView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/calendar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        day = timezone.localdate()
        day_param = self.request.GET.get("date", "")
        if day_param:
            try:
                day = timezone.datetime.strptime(day_param, "%Y-%m-%d").date()
            except ValueError:
                day = timezone.localdate()
        ctx["day"] = day
        ctx["prev_day"] = day - timezone.timedelta(days=1)
        ctx["next_day"] = day + timezone.timedelta(days=1)

        courts = Court.objects.filter(status="active").order_by("name")
        ctx["courts"] = courts
        slots = TimeSlot.objects.filter(date=day).order_by("start")
        grid = {}
        for s in slots:
            grid.setdefault(s.start, {})[s.court_id] = s
        bookings = Booking.objects.filter(date=day).select_related("user")
        by_start = {}
        for b in bookings:
            by_start.setdefault(b.start_time, []).append(b)
        ctx["rows"] = []
        minutes = 6 * 60
        while minutes < 24 * 60:
            time = dt_time(minutes // 60, minutes % 60)
            cells = []
            for court in courts:
                slot = grid.get(time, {}).get(court.id)
                day_bookings = [b for b in by_start.get(time, []) if b.court_id == court.id]
                cells.append((slot, day_bookings))
            ctx["rows"].append((time, cells))
            minutes += 30
        return ctx


class AuditListView(StaffRequiredMixin, ListView):
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
