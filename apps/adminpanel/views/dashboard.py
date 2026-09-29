from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView

from apps.adminpanel.admin_base import STAFF_ROLES
from apps.adminpanel.mixins import StaffRequiredMixin
from apps.bookings.models import Booking
from apps.courts.models import Court
from apps.payments.models import Payment
from apps.scheduling.models import MaintenanceWindow, TimeSlot
from apps.security.services import log_event

User = get_user_model()


class AdminLoginView(TemplateView):
    template_name = "adminpanel/login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request.user, "role", None) in STAFF_ROLES:
            return redirect("adminpanel:dashboard")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from django.core.cache import cache

        ip = request.META.get("REMOTE_ADDR", "unknown")
        cache_key = f"admin_login_fail:{ip}"
        if cache.get(cache_key, 0) >= 10:
            messages.error(request, "Demasiados intentos. Intente de nuevo en 15 minutos.")
            return self.get(request, *args, **kwargs)

        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            cache.delete(cache_key)
            if getattr(user, "role", None) in STAFF_ROLES or user.is_staff:
                auth_login(request, user)
                next_url = request.GET.get("next") or ""
                if not url_has_allowed_host_and_scheme(
                    url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
                ):
                    next_url = reverse("adminpanel:dashboard")
                log_event(user, "admin.login", "User", user.id)
                messages.success(request, f"Bienvenido al panel, {user.email}.")
                return redirect(next_url)
            else:
                cache.set(cache_key, cache.get(cache_key, 0) + 1, 900)
                messages.error(request, "Acceso denegado: tu cuenta no tiene rol administrativo.")
        else:
            cache.set(cache_key, cache.get(cache_key, 0) + 1, 900)
            messages.error(request, "Credenciales invalidas. Por favor verifica tu email y contrasena.")
        return self.get(request, *args, **kwargs)


class AdminLogoutView(View):
    """Logout is POST-only so a cross-site `<img>`/link cannot log a staff user out."""

    def post(self, request, *args, **kwargs):
        auth_logout(request)
        messages.info(request, "Has cerrado sesion del panel de control.")
        return redirect("adminpanel:login")


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
