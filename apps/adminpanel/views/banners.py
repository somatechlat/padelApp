from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from apps.adminpanel.mixins import StaffRequiredMixin
from apps.adminpanel.views.common import i18n_from_post, parse_dt, validate_image_upload
from apps.courts.models import PromoBanner
from apps.security.services import log_event


class BannersAdminView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/banners.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["banners"] = PromoBanner.objects.all().order_by("sort_order", "-created_at")
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or ""
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            messages.error(request, "Accion no valida.")
        else:
            handler(request)
        return redirect("adminpanel:banners")

    def _action_create_banner(self, request):
        image = request.FILES.get("image")
        image_error = validate_image_upload(image)
        if image_error:
            messages.error(request, image_error)
            return
        try:
            starts_at = parse_dt(request.POST.get("starts_at", ""))
            ends_at = parse_dt(request.POST.get("ends_at", ""))
        except (ValueError, TypeError):
            messages.error(request, "Fecha de vigencia invalida. Use formato ISO.")
            return
        if starts_at and ends_at and ends_at < starts_at:
            messages.error(request, "La fecha de fin debe ser posterior a la de inicio.")
            return
        title_i18n = i18n_from_post(request, "title")
        if not title_i18n.get("es"):
            messages.error(request, "El titulo en espanol es obligatorio.")
            return
        try:
            sort_order = int(request.POST.get("sort_order", 0) or 0)
        except (ValueError, TypeError):
            messages.error(request, "Orden invalido. Use un numero entero.")
            return
        banner = PromoBanner(
            title_i18n=title_i18n,
            subtitle_i18n=i18n_from_post(request, "subtitle"),
            link_url=request.POST.get("link_url", ""),
            link_type=request.POST.get("link_type", PromoBanner.LinkType.NONE),
            active=request.POST.get("active") == "on",
            sort_order=sort_order,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        banner.image = image
        banner.save()
        messages.success(request, f"Banner '{banner.title_for()}' creado.")
        log_event(request.user, "admin.banner_create", "PromoBanner", banner.id)

    def _action_edit_banner(self, request):
        banner = get_object_or_404(PromoBanner, id=request.POST.get("banner_id"))
        image = request.FILES.get("image")
        if image:
            image_error = validate_image_upload(image)
            if image_error:
                messages.error(request, image_error)
                return
        try:
            sort_order = int(request.POST.get("sort_order", banner.sort_order) or 0)
        except (ValueError, TypeError):
            messages.error(request, "Orden invalido. Use un numero entero.")
            return
        title = i18n_from_post(request, "title")
        subtitle = i18n_from_post(request, "subtitle")
        if title:
            banner.title_i18n = title
        if subtitle:
            banner.subtitle_i18n = subtitle
        banner.link_url = request.POST.get("link_url", banner.link_url)
        banner.link_type = request.POST.get("link_type", banner.link_type)
        banner.active = request.POST.get("active") == "on"
        banner.sort_order = sort_order
        try:
            if request.POST.get("starts_at", ""):
                banner.starts_at = parse_dt(request.POST.get("starts_at"))
            if request.POST.get("ends_at", ""):
                banner.ends_at = parse_dt(request.POST.get("ends_at"))
        except (ValueError, TypeError):
            messages.error(request, "Fecha de vigencia invalida. Use formato ISO.")
            return
        if image:
            banner.image = image
        if request.POST.get("remove_image") == "1" and not image:
            banner.clear_image()
            messages.success(request, f"Banner '{banner.title_for()}' actualizado.")
            log_event(request.user, "admin.banner_edit", "PromoBanner", banner.id)
            return
        if request.POST.get("remove_image") == "1" and image:
            banner.image.delete(save=False)
        if not banner.image:
            messages.error(request, "La imagen del banner es obligatoria.")
            return
        banner.save()
        messages.success(request, f"Banner '{banner.title_for()}' actualizado.")
        log_event(request.user, "admin.banner_edit", "PromoBanner", banner.id)

    def _action_toggle_banner(self, request):
        banner = get_object_or_404(PromoBanner, id=request.POST.get("banner_id"))
        banner.active = not banner.active
        banner.save(update_fields=["active"])
        estado = "activo" if banner.active else "inactivo"
        messages.success(request, f"Banner '{banner.title_for()}' ahora esta {estado}.")
        log_event(request.user, "admin.banner_toggle", "PromoBanner", banner.id)

    def _action_move_banner(self, request):
        banner = get_object_or_404(PromoBanner, id=request.POST.get("banner_id"))
        direction = request.POST.get("direction")
        if direction == "up":
            banner.sort_order -= 1
        elif direction == "down":
            banner.sort_order += 1
        banner.save(update_fields=["sort_order"])
        messages.success(request, f"Orden de '{banner.title_for()}' actualizado.")
        log_event(request.user, "admin.banner_reorder", "PromoBanner", banner.id)

    def _action_delete_banner(self, request):
        banner = get_object_or_404(PromoBanner, id=request.POST.get("banner_id"))
        title = banner.title_for()
        banner_id = banner.id
        if banner.image:
            banner.image.delete(save=False)
        banner.delete()
        messages.success(request, f"Banner '{title}' eliminado.")
        log_event(request.user, "admin.banner_delete", "PromoBanner", banner_id)
