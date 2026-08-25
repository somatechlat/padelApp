from datetime import time as dt_time, timedelta
from decimal import Decimal
import csv
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q, Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.adminpanel.admin_base import STAFF_ROLES
from apps.bookings.models import Booking, BookingSlot
from apps.courts.models import Court, Venue
from apps.events.models import Event, Tournament, NewsPost
from apps.payments.models import Payment
from apps.policies.models import CancellationPolicy
from apps.pricing.models import PriceRule
from apps.scheduling.models import MaintenanceWindow, TimeSlot
from apps.security.models import AuditLog
from apps.security.services import log_event

User = get_user_model()


from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

class StaffRequiredMixin(LoginRequiredMixin):
    login_url = "/adminpanel/login/"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", None) not in STAFF_ROLES:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdminLoginView(TemplateView):
    template_name = "adminpanel/login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request.user, "role", None) in STAFF_ROLES:
            return redirect("adminpanel:dashboard")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if getattr(user, "role", None) in STAFF_ROLES or user.is_staff:
                auth_login(request, user)
                next_url = request.GET.get("next") or reverse("adminpanel:dashboard")
                log_event(user, "admin.login", "User", user.id)
                messages.success(request, f"Bienvenido al panel, {user.email}.")
                return redirect(next_url)
            else:
                messages.error(request, "Acceso denegado: tu cuenta no tiene rol administrativo.")
        else:
            messages.error(request, "Credenciales invalidas. Por favor verifica tu email y contrasena.")
        return self.get(request, *args, **kwargs)


class AdminLogoutView(View):
    def get(self, request, *args, **kwargs):
        auth_logout(request)
        messages.info(request, "Has cerrado sesion del panel de control.")
        return redirect("adminpanel:login")

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)



class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        active = ("pending_payment", "confirmed", "in_progress")
        bookings_today = Booking.objects.filter(date=today, status__in=active)
        ctx["bookings_today"] = bookings_today.count()
        ctx["bookings_list"] = bookings_today.select_related("court", "user").order_by("start_time")[:10]

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

        ctx["recent_payments"] = Payment.objects.select_related("booking__user").order_by("-created_at")[:5]
        ctx["total_users"] = User.objects.count()
        ctx["total_courts"] = Court.objects.count()

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

        ctx["all_users"] = User.objects.filter(status="active").order_by("email")
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        day_param = request.POST.get("date", "")
        if action == "block_slot":
            slot_id = request.POST.get("slot_id")
            slot = get_object_or_404(TimeSlot, id=slot_id)
            if slot.status == "available":
                slot.status = "blocked"
                slot.save()
                messages.success(request, f"Horario {slot.start} bloqueado en {slot.court.name}.")
                log_event(request.user, "admin.slot_block", "TimeSlot", slot.id)
            else:
                messages.error(request, "No se puede bloquear un horario en uso.")
        elif action == "unblock_slot":
            slot_id = request.POST.get("slot_id")
            slot = get_object_or_404(TimeSlot, id=slot_id)
            if slot.status == "blocked":
                slot.status = "available"
                slot.save()
                messages.success(request, f"Horario {slot.start} desbloqueado en {slot.court.name}.")
                log_event(request.user, "admin.slot_unblock", "TimeSlot", slot.id)
        elif action == "create_booking":
            court_id = request.POST.get("court_id")
            user_id = request.POST.get("user_id")
            time_str = request.POST.get("start_time")
            duration = int(request.POST.get("duration", 60))
            court = get_object_or_404(Court, id=court_id)
            user = get_object_or_404(User, id=user_id)
            date_val = timezone.datetime.strptime(day_param, "%Y-%m-%d").date()
            start_time_val = timezone.datetime.strptime(time_str, "%H:%M").time()

            end_dt = timezone.datetime.combine(date_val, start_time_val) + timedelta(minutes=duration)
            end_time_val = end_dt.time()

            booking = Booking.objects.create(
                user=user,
                court=court,
                date=date_val,
                start_time=start_time_val,
                end_time=end_time_val,
                duration_minutes=duration,
                total_price=Decimal("30.00"),
                deposit_amount=Decimal("30.00"),
                status="confirmed",
            )
            messages.success(request, f"Reserva manual creada #{booking.id[:8]} para {user.email}.")
            log_event(request.user, "admin.booking_create", "Booking", booking.id)
            from apps.notifications.tasks import notify_task
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

        redirect_url = reverse("adminpanel:calendar")
        if day_param:
            redirect_url += f"?date={day_param}"
        return redirect(redirect_url)


class CourtsAdminView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/courts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["courts"] = Court.objects.all().order_by("name")
        ctx["maintenances"] = MaintenanceWindow.objects.select_related("court").order_by("-start")[:20]
        ctx["venues"] = Venue.objects.all()
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "toggle_status":
            court_id = request.POST.get("court_id")
            court = get_object_or_404(Court, id=court_id)
            court.status = "inactive" if court.status == "active" else "active"
            court.save()
            messages.success(request, f"Estado de {court.name} cambiado a {court.status}.")
            log_event(request.user, "admin.court_toggle", "Court", court.id)
        elif action == "create_court":
            name = request.POST.get("name")
            court_type = request.POST.get("court_type", "techada")
            venue = Venue.objects.first()
            if not venue:
                venue = Venue.objects.create(name="Andes Padel Club", address="Quito")
            court = Court.objects.create(
                venue=venue,
                name=name,
                court_type=court_type,
                has_lighting=request.POST.get("has_lighting") == "on",
                status="active"
            )
            messages.success(request, f"Cancha '{court.name}' creada exitosamente.")
            log_event(request.user, "admin.court_create", "Court", court.id)
        elif action == "schedule_maintenance":
            court_id = request.POST.get("court_id")
            reason = request.POST.get("reason", "Mantenimiento rutinario")
            start_str = request.POST.get("start")
            end_str = request.POST.get("end")
            court = get_object_or_404(Court, id=court_id)
            start_dt = timezone.datetime.fromisoformat(start_str)
            end_dt = timezone.datetime.fromisoformat(end_str)
            mw = MaintenanceWindow.objects.create(
                court=court,
                reason=reason,
                start=start_dt,
                end=end_dt
            )
            messages.success(request, f"Mantenimiento agendado para {court.name}.")
            log_event(request.user, "admin.maintenance_create", "MaintenanceWindow", mw.id)

        return redirect("adminpanel:courts")


class UsersAdminView(StaffRequiredMixin, ListView):
    template_name = "adminpanel/users.html"
    context_object_name = "users_list"
    paginate_by = 30
    model = User

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        role = self.request.GET.get("role", "")
        status_val = self.request.GET.get("status", "")
        q = self.request.GET.get("q", "")
        if role:
            qs = qs.filter(role=role)
        if status_val:
            qs = qs.filter(status=status_val)
        if q:
            qs = qs.filter(Q(email__icontains=q) | Q(full_name__icontains=q))
        return qs

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")
        target_user = get_object_or_404(User, id=user_id)

        if action == "change_role":
            new_role = request.POST.get("role")
            if new_role in dict(User.Role.choices):
                target_user.role = new_role
                target_user.save(update_fields=["role"])
                messages.success(request, f"Rol de {target_user.email} actualizado a {target_user.get_role_display()}.")
                log_event(request.user, "admin.user_role_change", "User", target_user.id)
        elif action == "change_status":
            new_status = request.POST.get("status")
            if new_status in dict(User.Status.choices):
                target_user.status = new_status
                target_user.save(update_fields=["status"])
                messages.success(request, f"Estado de {target_user.email} actualizado a {target_user.get_status_display()}.")
                log_event(request.user, "admin.user_status_change", "User", target_user.id)

        return redirect(request.get_full_path())


class PaymentsAdminView(StaffRequiredMixin, ListView):
    template_name = "adminpanel/payments.html"
    context_object_name = "payments_list"
    paginate_by = 30
    model = Payment

    def get_queryset(self):
        qs = Payment.objects.select_related("booking__user", "booking__court").order_by("-created_at")
        status_val = self.request.GET.get("status", "")
        method = self.request.GET.get("method", "")
        if status_val:
            qs = qs.filter(status=status_val)
        if method:
            qs = qs.filter(method=method)
        return qs

    def post(self, request, *args, **kwargs):
        payment_id = request.POST.get("payment_id")
        action = request.POST.get("action")
        payment = get_object_or_404(Payment, id=payment_id)

        if action == "confirm_transfer":
            PaymentService.confirm_transfer(payment)
            messages.success(request, f"Comprobante de transferencia verificado para pago #{payment.id[:8]}.")
        elif action == "reject_transfer":
            reason = request.POST.get("rejection_reason", "").strip()
            if not reason:
                messages.error(request, "El motivo de rechazo es obligatorio.")
                return redirect(request.get_full_path())
            PaymentService.reject_transfer(payment, reason)
            messages.warning(request, f"Transferencia rechazada para pago #{payment.id[:8]}.")
        elif action == "refund":
            amount = payment.amount
            PaymentService.refund(payment, amount)
            if payment.booking:
                payment.booking.status = "cancelled"
                payment.booking.save(update_fields=["status"])
            messages.success(request, f"Reembolso procesado para pago #{payment.id[:8]}.")

        return redirect(request.get_full_path())


class EventsAdminView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/events.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tournaments"] = Tournament.objects.all().order_by("-start_date")
        ctx["events"] = Event.objects.all().order_by("-start_at")
        ctx["news"] = NewsPost.objects.all().order_by("-published_at")
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "create_tournament":
            title = request.POST.get("title")
            category = request.POST.get("category", "Open")
            max_teams = int(request.POST.get("max_teams", 16))
            fee = Decimal(request.POST.get("entry_fee", "0.00"))
            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")
            t = Tournament.objects.create(
                title=title,
                category=category,
                max_teams=max_teams,
                entry_fee=fee,
                start_date=start_date,
                end_date=end_date,
                status="open"
            )
            messages.success(request, f"Torneo '{t.title}' creado exitosamente.")
            log_event(request.user, "admin.tournament_create", "Tournament", t.id)
        elif action == "create_news":
            title = request.POST.get("title")
            content = request.POST.get("content")
            n = NewsPost(
                title=title,
                content=content,
            )
            n.publish()
            messages.success(request, f"Noticia '{n.title}' publicada y notificaciones enviadas.")
            log_event(request.user, "admin.news_create", "NewsPost", n.id)

        return redirect("adminpanel:events")


class ReportsAdminView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/reports.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        start_month = today.replace(day=1)
        
        ctx["month_revenue"] = Payment.objects.filter(
            status__in=("captured", "confirmed"),
            created_at__date__gte=start_month
        ).aggregate(total=Sum("amount"))["total"] or 0

        ctx["bookings_by_status"] = Booking.objects.values("status").annotate(count=Count("id"))
        ctx["revenue_by_court"] = Payment.objects.filter(
            status__in=("captured", "confirmed")
        ).values("booking__court__name").annotate(total=Sum("amount"))

        ctx["top_customers"] = User.objects.annotate(
            booking_count=Count("bookings")
        ).order_by("-booking_count")[:10]

        return ctx

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="andes_padel_report.csv"'
            writer = csv.writer(response)
            writer.writerow(["ID Reserva", "Fecha", "Cliente", "Cancha", "Precio", "Estado"])
            for b in Booking.objects.select_related("user", "court").order_by("-date")[:500]:
                writer.writerow([b.id, b.date, b.user.email, b.court.name, b.price, b.status])
            return response
        return super().get(request, *args, **kwargs)


class SettingsAdminView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["policies"] = CancellationPolicy.objects.all()
        ctx["price_rules"] = PriceRule.objects.select_related("venue").all()
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

