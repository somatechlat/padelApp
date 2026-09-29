from datetime import date as date_type
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView

from apps.adminpanel.mixins import StaffRequiredMixin
from apps.events.models import (
    Event,
    EventRegistration,
    NewsPost,
    Tournament,
    TournamentRegistration,
)
from apps.security.services import log_event


class EventsAdminView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/events.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tournaments"] = Tournament.objects.all().order_by("-start_date")
        ctx["events"] = Event.objects.prefetch_related("registrations").order_by("-start_at")
        ctx["event_registrations"] = (
            EventRegistration.objects.select_related("event", "user")
            .filter(status=EventRegistration.Status.GOING)
            .order_by("-created_at")[:50]
        )
        ctx["news"] = NewsPost.objects.all().order_by("-published_at")
        ctx["registrations"] = (
            TournamentRegistration.objects.select_related("tournament", "user")
            .order_by("-created_at")[:50]
        )
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or ""
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            messages.error(request, "Accion no valida.")
        else:
            handler(request)
        return redirect("adminpanel:events")

    def _action_create_event(self, request):
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "")
        location = request.POST.get("location", "")
        category = request.POST.get("category", "quedada")
        start_at = request.POST.get("start_at", "")
        end_at = request.POST.get("end_at", "")
        if not title:
            messages.error(request, "El titulo es obligatorio.")
            return
        try:
            start_dt = datetime.fromisoformat(start_at)
            end_dt = datetime.fromisoformat(end_at)
        except (ValueError, TypeError):
            messages.error(request, "Fecha u hora invalida.")
            return
        try:
            capacity = int(request.POST.get("capacity", 0) or 0)
        except (ValueError, TypeError):
            capacity = 0
        e = Event.objects.create(
            title=title,
            title_es=title,
            description_es=description,
            location=location,
            category=category,
            start_at=start_dt,
            end_at=end_dt,
            status="published",
            capacity=capacity,
            allow_registration=request.POST.get("allow_registration") == "on",
            created_by=request.user,
        )
        messages.success(request, f"Evento '{e.title}' creado exitosamente.")
        log_event(request.user, "admin.event_create", "Event", e.id)

    def _action_edit_event(self, request):
        e = get_object_or_404(Event, id=request.POST.get("event_id"))
        try:
            capacity = int(request.POST.get("capacity", e.capacity) or 0)
        except (ValueError, TypeError):
            messages.error(request, "Capacidad invalida. Use un numero entero.")
            return
        e.title = request.POST.get("title", e.title)
        e.title_es = e.title
        e.description_es = request.POST.get("description", e.description_es)
        e.location = request.POST.get("location", e.location)
        e.category = request.POST.get("category", e.category)
        e.allow_registration = request.POST.get("allow_registration") == "on"
        e.capacity = capacity
        start_at = request.POST.get("start_at", "")
        end_at = request.POST.get("end_at", "")
        try:
            if start_at:
                e.start_at = datetime.fromisoformat(start_at)
            if end_at:
                e.end_at = datetime.fromisoformat(end_at)
        except (ValueError, TypeError):
            messages.error(request, "Fecha u hora invalida.")
            return
        e.save()
        messages.success(request, f"Evento '{e.title}' actualizado.")
        log_event(request.user, "admin.event_edit", "Event", e.id)

    def _action_delete_event(self, request):
        event_id = request.POST.get("event_id")
        e = get_object_or_404(Event, id=event_id)
        title = e.title
        e.delete()
        messages.success(request, f"Evento '{title}' eliminado.")
        log_event(request.user, "admin.event_delete", "Event", int(event_id))

    def _action_toggle_event(self, request):
        e = get_object_or_404(Event, id=request.POST.get("event_id"))
        e.status = "draft" if e.status == "published" else "published"
        e.save()
        messages.success(request, f"Evento '{e.title}' ahora es {e.get_status_display()}.")
        log_event(request.user, "admin.event_toggle", "Event", e.id)

    def _action_toggle_tournament(self, request):
        t = get_object_or_404(Tournament, id=request.POST.get("tournament_id"))
        if t.status == "open":
            t.status = "closed"
        elif t.status in ("closed", "draft"):
            t.status = "open"
        t.save()
        messages.success(request, f"Torneo '{t.name}' ahora es {t.get_status_display()}.")
        log_event(request.user, "admin.tournament_toggle", "Tournament", t.id)

    def _action_create_tournament(self, request):
        title = request.POST.get("title", "")
        try:
            capacity = int(request.POST.get("max_teams", 16))
            fee = Decimal(request.POST.get("entry_fee", "0.00"))
        except (ValueError, TypeError, ArithmeticError):
            messages.error(request, "Capacidad o tarifa invalida.")
            return
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")
        try:
            sd = date_type.fromisoformat(start_date)
            ed = date_type.fromisoformat(end_date)
        except (ValueError, TypeError):
            messages.error(request, "Fecha de torneo invalida. Use formato YYYY-MM-DD.")
            return
        if ed < sd:
            messages.error(request, "La fecha de fin debe ser igual o posterior a la de inicio.")
            return
        t = Tournament.objects.create(
            name=title,
            name_es=title,
            capacity=capacity,
            price=fee,
            start_date=sd,
            end_date=ed,
            registration_deadline=timezone.now() + timedelta(days=7),
            status="open",
            created_by=request.user,
        )
        messages.success(request, f"Torneo '{t.name}' creado exitosamente.")
        log_event(request.user, "admin.tournament_create", "Tournament", t.id)

    def _action_edit_tournament(self, request):
        t = get_object_or_404(Tournament, id=request.POST.get("tournament_id"))
        try:
            capacity = int(request.POST.get("max_teams", t.capacity))
            fee = Decimal(request.POST.get("entry_fee", str(t.price)))
        except (ValueError, TypeError, ArithmeticError):
            messages.error(request, "Capacidad o tarifa invalida.")
            return
        t.name = request.POST.get("title", t.name)
        t.name_es = t.name
        t.capacity = capacity
        t.price = fee
        sd = request.POST.get("start_date", "")
        ed = request.POST.get("end_date", "")
        if sd:
            t.start_date = sd
        if ed:
            t.end_date = ed
        t.save()
        messages.success(request, f"Torneo '{t.name}' actualizado.")
        log_event(request.user, "admin.tournament_edit", "Tournament", t.id)

    def _action_delete_tournament(self, request):
        tournament_id = request.POST.get("tournament_id")
        t = get_object_or_404(Tournament, id=tournament_id)
        name = t.name
        t.delete()
        messages.success(request, f"Torneo '{name}' eliminado.")
        log_event(request.user, "admin.tournament_delete", "Tournament", int(tournament_id))

    def _action_create_news(self, request):
        title = request.POST.get("title")
        content = request.POST.get("content")
        n = NewsPost(
            title=title,
            title_es=title,
            body_es=content,
            created_by=request.user,
        )
        n.save()
        n.publish()
        messages.success(request, f"Noticia '{n.title}' publicada y notificaciones enviadas.")
        log_event(request.user, "admin.news_create", "NewsPost", n.id)

    def _action_edit_news(self, request):
        n = get_object_or_404(NewsPost, id=request.POST.get("news_id"))
        n.title = request.POST.get("title", n.title)
        n.title_es = n.title
        n.body_es = request.POST.get("content", n.body_es)
        n.save()
        messages.success(request, f"Noticia '{n.title}' actualizada.")
        log_event(request.user, "admin.news_edit", "NewsPost", n.id)

    def _action_delete_news(self, request):
        news_id = request.POST.get("news_id")
        n = get_object_or_404(NewsPost, id=news_id)
        title = n.title
        n.delete()
        messages.success(request, f"Noticia '{title}' eliminada.")
        log_event(request.user, "admin.news_delete", "NewsPost", int(news_id))
