from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from apps.adminpanel.mixins import FinanceRequiredMixin
from apps.adminpanel.views.common import validate_image_upload
from apps.courts.models import Venue
from apps.policies.models import CancellationPolicy
from apps.pricing.models import Holiday, PriceRule
from apps.security.services import log_event


class SettingsAdminView(FinanceRequiredMixin, TemplateView):
    """Bank details, pricing rules and cancellation policies — dueno/superadmin only."""

    template_name = "adminpanel/settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["policies"] = CancellationPolicy.objects.all()
        ctx["price_rules"] = PriceRule.objects.select_related("venue").all()
        ctx["holidays"] = Holiday.objects.all().order_by("date")
        ctx["club"] = Venue.objects.first() or Venue.objects.create(
            name="Andes Padel Club", address=""
        )
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or ""
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            messages.error(request, "Accion no valida.")
        else:
            handler(request)
        return redirect("adminpanel:settings")

    @staticmethod
    def _venue():
        venue = Venue.objects.first()
        if not venue:
            venue = Venue.objects.create(name="Andes Padel Club", address="Quito")
        return venue

    def _action_update_club(self, request):
        venue = self._venue()
        self._apply_club_contact_fields(request, venue)
        self._apply_club_i18n_fields(request, venue)
        logo_error = self._apply_club_logo(request, venue)
        if logo_error:
            messages.error(request, logo_error)
            return
        venue.save()
        messages.success(request, "Informacion del club actualizada.")
        log_event(request.user, "admin.club_update", "Venue", venue.id)

    @staticmethod
    def _apply_club_contact_fields(request, venue):
        venue.name = request.POST.get("name", venue.name)
        venue.address = request.POST.get("address", venue.address)
        venue.maps_query = request.POST.get("maps_query", venue.maps_query)
        venue.maps_url = request.POST.get("maps_url", venue.maps_url)
        venue.phone = request.POST.get("phone", venue.phone)
        venue.email = request.POST.get("email", venue.email)
        venue.whatsapp_number = request.POST.get("whatsapp_number", venue.whatsapp_number)
        venue.whatsapp_message = request.POST.get("whatsapp_message", venue.whatsapp_message)
        venue.instagram_url = request.POST.get("instagram_url", venue.instagram_url)
        venue.booking_alert_email = request.POST.get(
            "booking_alert_email", venue.booking_alert_email
        ).strip()
        venue.booking_alert_push = request.POST.get("booking_alert_push") == "1"
        venue.bank_name = request.POST.get("bank_name", venue.bank_name)
        venue.bank_account_number = request.POST.get(
            "bank_account_number", venue.bank_account_number
        )
        venue.bank_account_holder = request.POST.get(
            "bank_account_holder", venue.bank_account_holder
        )
        venue.bank_account_code = request.POST.get("bank_account_code", venue.bank_account_code)
        venue.bank_extra = request.POST.get("bank_extra", venue.bank_extra)

    @staticmethod
    def _apply_club_i18n_fields(request, venue):
        section = dict(venue.home_section_title_i18n or {})
        greeting = dict(venue.home_greeting_tagline_i18n or {})
        for lang in ("es", "en", "pt", "ca"):
            if f"home_section_title_{lang}" in request.POST:
                section[lang] = request.POST.get(f"home_section_title_{lang}", "").strip()
            if f"home_greeting_tagline_{lang}" in request.POST:
                greeting[lang] = request.POST.get(f"home_greeting_tagline_{lang}", "").strip()
        venue.home_section_title_i18n = {k: v for k, v in section.items() if v}
        venue.home_greeting_tagline_i18n = {k: v for k, v in greeting.items() if v}

    @staticmethod
    def _apply_club_logo(request, venue):
        image = request.FILES.get("logo")
        if image:
            image_error = validate_image_upload(image, field_label="logo")
            if image_error:
                return image_error
            venue.logo = image
        if request.POST.get("remove_logo") == "1":
            if venue.logo:
                venue.logo.delete(save=False)
            venue.logo = None
        return None

    def _action_create_policy(self, request):
        try:
            free_window = int(request.POST.get("free_window_hours", 24))
            penalty = Decimal(request.POST.get("penalty_ratio", "0.50"))
            no_show = Decimal(request.POST.get("no_show_ratio", "1.00"))
            hold_minutes = int(request.POST.get("hold_minutes", 10))
            max_holds = int(request.POST.get("max_holds_per_user", 5))
        except (ValueError, TypeError, ArithmeticError):
            messages.error(request, "Valores de politica invalidos.")
            return
        CancellationPolicy.objects.create(
            venue=self._venue(),
            free_window_hours=free_window,
            penalty_ratio=penalty,
            no_show_ratio=no_show,
            hold_minutes=hold_minutes,
            max_holds_per_user=max_holds,
        )
        messages.success(request, "Politica de cancelacion creada.")
        log_event(request.user, "admin.policy_create", "CancellationPolicy", 0)

    def _action_edit_policy(self, request):
        p = get_object_or_404(CancellationPolicy, id=request.POST.get("policy_id"))
        try:
            p.free_window_hours = int(request.POST.get("free_window_hours", p.free_window_hours))
            p.penalty_ratio = Decimal(request.POST.get("penalty_ratio", str(p.penalty_ratio)))
            p.no_show_ratio = Decimal(request.POST.get("no_show_ratio", str(p.no_show_ratio)))
            p.hold_minutes = int(request.POST.get("hold_minutes", p.hold_minutes))
            p.max_holds_per_user = int(request.POST.get("max_holds_per_user", p.max_holds_per_user))
        except (ValueError, TypeError, ArithmeticError):
            messages.error(request, "Valores de politica invalidos.")
            return
        p.save()
        messages.success(request, "Politica actualizada.")
        log_event(request.user, "admin.policy_edit", "CancellationPolicy", p.id)

    def _action_delete_policy(self, request):
        policy_id = request.POST.get("policy_id")
        p = get_object_or_404(CancellationPolicy, id=policy_id)
        p.delete()
        messages.success(request, "Politica eliminada.")
        log_event(request.user, "admin.policy_delete", "CancellationPolicy", int(policy_id))

    def _action_create_pricerule(self, request):
        name = request.POST.get("name", "")
        zone = request.POST.get("zone", "valle")
        court_type = request.POST.get("court_type") or None
        try:
            multiplier = Decimal(request.POST.get("multiplier", "1.000"))
            priority = int(request.POST.get("priority", 10))
        except (ValueError, TypeError, ArithmeticError):
            messages.error(request, "Multiplicador o prioridad invalidos.")
            return
        PriceRule.objects.create(
            venue=self._venue(),
            name=name,
            zone=zone,
            court_type=court_type,
            multiplier=multiplier,
            priority=priority,
        )
        messages.success(request, f"Regla '{name}' creada.")
        log_event(request.user, "admin.pricerule_create", "PriceRule", 0)

    def _action_edit_pricerule(self, request):
        r = get_object_or_404(PriceRule, id=request.POST.get("pricerule_id"))
        try:
            multiplier = Decimal(request.POST.get("multiplier", str(r.multiplier)))
            priority = int(request.POST.get("priority", r.priority))
        except (ValueError, TypeError, ArithmeticError):
            messages.error(request, "Multiplicador o prioridad invalidos.")
            return
        r.name = request.POST.get("name", r.name)
        r.zone = request.POST.get("zone", r.zone)
        r.court_type = request.POST.get("court_type") or None
        r.multiplier = multiplier
        r.priority = priority
        r.save()
        messages.success(request, f"Regla '{r.name}' actualizada.")
        log_event(request.user, "admin.pricerule_edit", "PriceRule", r.id)

    def _action_delete_pricerule(self, request):
        pricerule_id = request.POST.get("pricerule_id")
        r = get_object_or_404(PriceRule, id=pricerule_id)
        r.delete()
        messages.success(request, "Regla eliminada.")
        log_event(request.user, "admin.pricerule_delete", "PriceRule", int(pricerule_id))

    def _action_create_holiday(self, request):
        h = Holiday.objects.create(
            venue=self._venue(),
            date=request.POST.get("date", ""),
            name=request.POST.get("name", ""),
        )
        messages.success(request, f"Feriado '{h.name}' creado.")
        log_event(request.user, "admin.holiday_create", "Holiday", h.id)

    def _action_delete_holiday(self, request):
        holiday_id = request.POST.get("holiday_id")
        h = get_object_or_404(Holiday, id=holiday_id)
        h.delete()
        messages.success(request, "Feriado eliminado.")
        log_event(request.user, "admin.holiday_delete", "Holiday", int(holiday_id))
