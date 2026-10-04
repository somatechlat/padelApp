from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from apps.adminpanel.mixins import StaffRequiredMixin
from apps.adminpanel.views.common import validate_image_upload
from apps.courts.models import Court, CourtSchedule, Venue
from apps.scheduling.models import MaintenanceWindow
from apps.security.services import log_event


class CourtsAdminView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/courts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["courts"] = Court.objects.prefetch_related("schedules").order_by("name")
        ctx["maintenances"] = MaintenanceWindow.objects.select_related("court").order_by("-start")[
            :20
        ]
        ctx["venues"] = Venue.objects.all()
        ctx["weekdays"] = [
            (0, "Lunes"),
            (1, "Martes"),
            (2, "Miercoles"),
            (3, "Jueves"),
            (4, "Viernes"),
            (5, "Sabado"),
            (6, "Domingo"),
        ]
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or ""
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            messages.error(request, "Accion no valida.")
        else:
            handler(request)
        return redirect("adminpanel:courts")

    def _action_toggle_status(self, request):
        court = get_object_or_404(Court, id=request.POST.get("court_id"))
        court.status = "archived" if court.status == "active" else "active"
        court.save()
        messages.success(request, f"Estado de {court.name} cambiado a {court.status}.")
        log_event(request.user, "admin.court_toggle", "Court", court.id)

    def _action_create_court(self, request):
        image = request.FILES.get("image")
        if image:
            image_error = validate_image_upload(image, field_label="imagen")
            if image_error:
                messages.error(request, image_error)
                return
        name = request.POST.get("name")
        court_type = request.POST.get("court_type", "techada")
        venue = Venue.objects.first()
        if not venue:
            venue = Venue.objects.create(name="Andes Padel Club", address="Quito")
        court = Court(
            venue=venue,
            name=name,
            description=request.POST.get("description", ""),
            court_type=court_type,
            has_lighting=request.POST.get("has_lighting") == "on",
            price_base=request.POST.get("price_base", "10.00"),
            status="active",
        )
        if image:
            court.image = image
        court.save()
        self._apply_default_schedule(court)
        messages.success(request, f"Cancha '{court.name}' creada exitosamente.")
        log_event(request.user, "admin.court_create", "Court", court.id)

    def _action_edit_court(self, request):
        court = get_object_or_404(Court, id=request.POST.get("court_id"))
        image = request.FILES.get("image")
        if image:
            image_error = validate_image_upload(image, field_label="imagen")
            if image_error:
                messages.error(request, image_error)
                return
        court.name = request.POST.get("name", court.name)
        court.description = request.POST.get("description", court.description)
        court.court_type = request.POST.get("court_type", court.court_type)
        court.has_lighting = request.POST.get("has_lighting") == "on"
        price = request.POST.get("price_base")
        if price:
            court.price_base = price
        if image:
            court.image = image
        if request.POST.get("remove_image") == "1":
            court.image.delete(save=False)
            court.image = None
        court.save()
        messages.success(request, f"Cancha '{court.name}' actualizada.")
        log_event(request.user, "admin.court_edit", "Court", court.id)

    def _action_save_schedule(self, request):
        court = get_object_or_404(Court, id=request.POST.get("court_id"))
        for weekday in range(7):
            open_str = (request.POST.get(f"open_{weekday}") or "").strip()
            close_str = (request.POST.get(f"close_{weekday}") or "").strip()
            active = request.POST.get(f"active_{weekday}") == "on"
            existing = CourtSchedule.objects.filter(court=court, weekday=weekday).first()
            if not open_str or not close_str or not active:
                if existing:
                    existing.delete()
                continue
            try:
                open_time = datetime.strptime(open_str, "%H:%M").time()
                close_time = datetime.strptime(close_str, "%H:%M").time()
            except ValueError:
                messages.error(request, f"Horario invalido el dia {weekday}. Use HH:MM.")
                return
            if close_time <= open_time:
                messages.error(
                    request,
                    f"La hora de cierre debe ser posterior a la de apertura (dia {weekday}).",
                )
                return
            CourtSchedule.objects.update_or_create(
                court=court,
                weekday=weekday,
                defaults={"open_time": open_time, "close_time": close_time, "is_active": True},
            )
        messages.success(request, f"Horario de {court.name} actualizado.")
        log_event(request.user, "admin.court_schedule", "Court", court.id)

    def _action_apply_default_schedule(self, request):
        court = get_object_or_404(Court, id=request.POST.get("court_id"))
        self._apply_default_schedule(court)
        messages.success(request, f"Horario 08:00–22:00 aplicado a {court.name} (lun–dom).")
        log_event(request.user, "admin.court_schedule_default", "Court", court.id)

    def _action_delete_court(self, request):
        court = get_object_or_404(Court, id=request.POST.get("court_id"))
        name = court.name
        court_id = court.id
        court.delete()
        messages.success(request, f"Cancha '{name}' eliminada.")
        log_event(request.user, "admin.court_delete", "Court", court_id)

    def _action_schedule_maintenance(self, request):
        court = get_object_or_404(Court, id=request.POST.get("court_id"))
        reason = request.POST.get("reason", "Mantenimiento rutinario")
        start_str = request.POST.get("start", "")
        end_str = request.POST.get("end", "")
        try:
            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)
        except (ValueError, TypeError):
            messages.error(request, "Fecha u hora de mantenimiento invalida.")
            return
        if end_dt <= start_dt:
            messages.error(request, "La fecha de fin debe ser posterior a la de inicio.")
            return
        mw = MaintenanceWindow.objects.create(
            court=court,
            reason=reason,
            start=start_dt,
            end=end_dt,
        )
        messages.success(request, f"Mantenimiento agendado para {court.name}.")
        log_event(request.user, "admin.maintenance_create", "MaintenanceWindow", mw.id)

    @staticmethod
    def _apply_default_schedule(court):
        for weekday in range(7):
            CourtSchedule.objects.get_or_create(
                court=court,
                weekday=weekday,
                defaults={
                    "open_time": datetime.strptime("08:00", "%H:%M").time(),
                    "close_time": datetime.strptime("22:00", "%H:%M").time(),
                    "is_active": True,
                },
            )
