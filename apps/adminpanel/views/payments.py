from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView

from apps.adminpanel.admin_base import FINANCIAL_ROLES, MANAGER_ROLES
from apps.adminpanel.mixins import StaffRequiredMixin, require_roles
from apps.payments.models import Payment
from apps.payments.services import PaymentService


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
        action = request.POST.get("action") or ""
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            messages.error(request, "Accion no valida.")
        else:
            handler(request)
        return redirect(request.get_full_path())

    def _action_confirm_transfer(self, request):
        require_roles(request, MANAGER_ROLES)
        payment = get_object_or_404(Payment, id=request.POST.get("payment_id"))
        PaymentService.confirm_transfer(payment)
        messages.success(request, f"Comprobante de transferencia verificado para pago #{payment.id}.")

    def _action_reject_transfer(self, request):
        require_roles(request, MANAGER_ROLES)
        payment = get_object_or_404(Payment, id=request.POST.get("payment_id"))
        reason = request.POST.get("rejection_reason", "").strip()
        if not reason:
            messages.error(request, "El motivo de rechazo es obligatorio.")
            return
        PaymentService.reject_transfer(payment, reason)
        messages.warning(request, f"Transferencia rechazada para pago #{payment.id}.")

    def _action_refund(self, request):
        require_roles(request, FINANCIAL_ROLES)
        payment = get_object_or_404(Payment, id=request.POST.get("payment_id"))
        amount = payment.amount
        PaymentService.refund(payment, amount)
        if payment.booking:
            payment.booking.transition_to("cancelled")
        messages.success(request, f"Reembolso procesado para pago #{payment.id}.")
