from datetime import datetime, timedelta
from datetime import time as dt_time

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.adminpanel.mixins import StaffRequiredMixin
from apps.bookings.models import Booking
from apps.courts.models import Court
from apps.notifications.tasks import notify_task
from apps.pricing.services import TariffService
from apps.scheduling.models import TimeSlot
from apps.security.services import log_event

User = get_user_model()


class CalendarView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/calendar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        day = self._day_from_param(self.request.GET.get("date", ""))
        ctx["day"] = day
        ctx["prev_day"] = day - timedelta(days=1)
        ctx["next_day"] = day + timedelta(days=1)

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

        ctx["all_users"] = User.objects.filter(status="active").order_by("email")
        return ctx

    @staticmethod
    def _day_from_param(day_param):
        if day_param:
            try:
                return datetime.strptime(day_param, "%Y-%m-%d").date()
            except ValueError:
                pass
        return timezone.localdate()

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or ""
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            messages.error(request, "Accion no valida.")
        else:
            handler(request)

        day_param = request.POST.get("date", "")
        redirect_url = reverse("adminpanel:calendar")
        if day_param:
            redirect_url += f"?date={day_param}"
        return redirect(redirect_url)

    def _action_block_slot(self, request):
        slot = get_object_or_404(TimeSlot, id=request.POST.get("slot_id"))
        if slot.status == "available":
            slot.status = "blocked"
            slot.save()
            messages.success(request, f"Horario {slot.start} bloqueado en {slot.court.name}.")
            log_event(request.user, "admin.slot_block", "TimeSlot", slot.id)
        else:
            messages.error(request, "No se puede bloquear un horario en uso.")

    def _action_unblock_slot(self, request):
        slot = get_object_or_404(TimeSlot, id=request.POST.get("slot_id"))
        if slot.status == "blocked":
            slot.status = "available"
            slot.save()
            messages.success(request, f"Horario {slot.start} desbloqueado en {slot.court.name}.")
            log_event(request.user, "admin.slot_unblock", "TimeSlot", slot.id)

    def _action_cancel_booking(self, request):
        booking = get_object_or_404(Booking, id=request.POST.get("booking_id"))
        try:
            booking.transition_to("cancelled")
            messages.success(request, f"Reserva de {booking.user.email} cancelada.")
            log_event(request.user, "admin.booking_cancel", "Booking", booking.id)
        except ValueError as exc:
            messages.error(request, str(exc))

    def _action_mark_noshow(self, request):
        booking = get_object_or_404(Booking, id=request.POST.get("booking_id"))
        try:
            booking.transition_to("no_show")
            messages.success(request, f"Reserva de {booking.user.email} marcada como no-show.")
            log_event(request.user, "admin.booking_noshow", "Booking", booking.id)
        except ValueError as exc:
            messages.error(request, str(exc))

    def _action_create_booking(self, request):
        day_param = request.POST.get("date", "")
        time_str = request.POST.get("start_time", "")
        try:
            duration = int(request.POST.get("duration", 60))
        except (ValueError, TypeError):
            messages.error(request, "Duracion invalida.")
            return
        court = get_object_or_404(Court, id=request.POST.get("court_id"))
        user = get_object_or_404(User, id=request.POST.get("user_id"))
        try:
            date_val = datetime.strptime(day_param, "%Y-%m-%d").date()
            start_time_val = datetime.strptime(time_str, "%H:%M").time()
        except (ValueError, TypeError):
            messages.error(request, "Fecha u hora invalida.")
            return

        end_dt = datetime.combine(date_val, start_time_val) + timedelta(minutes=duration)
        end_time_val = end_dt.time()

        booking = Booking.objects.create(
            user=user,
            court=court,
            date=date_val,
            start_time=start_time_val,
            end_time=end_time_val,
            duration_minutes=duration,
            price=TariffService.compute(court, date_val, duration),
            status="confirmed",
        )
        messages.success(request, f"Reserva manual creada #{booking.id} para {user.email}.")
        log_event(request.user, "admin.booking_create", "Booking", booking.id)
        notify_task.delay(
            user.id,
            "booking_confirmed",
            "",
            "",
            {
                "court": court.name,
                "date": str(date_val),
                "time": str(start_time_val),
                "booking_id": booking.id,
            },
        )
