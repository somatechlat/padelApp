from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.generic import ListView

from apps.adminpanel.admin_base import FINANCIAL_ROLES, MANAGER_ROLES
from apps.adminpanel.mixins import StaffRequiredMixin, require_roles, role_level
from apps.security.services import log_event
from apps.users.models import Role as UserRole
from apps.users.models import Status as UserStatus

User = get_user_model()


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
        action = request.POST.get("action") or ""
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            messages.error(request, "Accion no valida.")
        else:
            handler(request)
        return redirect(request.get_full_path())

    def _action_change_role(self, request):
        require_roles(request, FINANCIAL_ROLES)
        target_user = get_object_or_404(User, id=request.POST.get("user_id"))
        new_role = request.POST.get("role")
        if new_role not in UserRole.values:
            messages.error(request, "Rol invalido.")
            return
        if role_level(new_role) > role_level(request.user.role):
            # Privilege escalation is an attack, not a typo: 403, not a flash.
            raise PermissionDenied(_("No puedes asignar un rol superior al tuyo."))
        if (
            target_user.role == "superadmin"
            and new_role != "superadmin"
            and not User.objects.filter(role="superadmin").exclude(pk=target_user.pk).exists()
        ):
            messages.error(
                request,
                _("No puedes quitar el ultimo superadmin. Crea otro antes de degradar este."),
            )
            return
        target_user.role = new_role
        target_user.save(update_fields=["role"])
        messages.success(
            request, f"Rol de {target_user.email} actualizado a {target_user.get_role_display()}."
        )
        log_event(request.user, "admin.user_role_change", "User", target_user.id)

    def _action_change_status(self, request):
        # Suspending/activating an account is operational management, not
        # front-desk work — a receptionist must not be able to lock anyone out.
        require_roles(request, MANAGER_ROLES)
        target_user = get_object_or_404(User, id=request.POST.get("user_id"))
        new_status = request.POST.get("status")
        if new_status not in UserStatus.values:
            messages.error(request, "Estado invalido.")
            return
        target_user.status = new_status
        target_user.save(update_fields=["status"])
        messages.success(
            request,
            f"Estado de {target_user.email} actualizado a {target_user.get_status_display()}.",
        )
        log_event(request.user, "admin.user_status_change", "User", target_user.id)
