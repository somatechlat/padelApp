from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer, RefundSerializer
from apps.payments.services import PaymentService
from apps.users.permissions import IsOwnerOrStaff, IsStaffRole

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


class BookingPaymentView(APIView):
    permission_classes = [IsOwnerOrStaff]

    def post(self, request, booking_id=None):
        booking = get_object_or_404(
            Booking.objects.filter(user=request.user) if request.user.role == "cliente" else Booking.objects.all(),
            pk=booking_id,
        )
        method = request.data.get("method", "stripe")
        valid_methods = {c[0] for c in Payment.Method.choices}
        if method not in valid_methods:
            return Response(
                {"detail": f"Metodo de pago invalido. Opciones: {', '.join(valid_methods)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if method == "cash":
            if request.user.role == "cliente":
                return Response(status=status.HTTP_403_FORBIDDEN)
            payment = PaymentService.record_cash(booking, booking.price)
        elif method == "transfer":
            payment = PaymentService.record_transfer(
                booking, request.data.get("reference", "")
            )
        else:
            try:
                payment = PaymentService.create_intent(booking)
            except Exception:
                return Response(
                    {"detail": "No se pudo iniciar el pago"}, status=status.HTTP_400_BAD_REQUEST
                )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentProofUploadView(APIView):
    permission_classes = [IsOwnerOrStaff]

    def post(self, request, pk=None):
        payment = get_object_or_404(
            Payment.objects.filter(user=request.user) if request.user.role == "cliente" else Payment.objects.all(),
            pk=pk,
            method=Payment.Method.TRANSFER,
            status=Payment.Status.PENDING_TRANSFER,
        )
        proof = request.FILES.get("proof_image")
        if not proof:
            return Response(
                {"detail": "Adjunte el comprobante de transferencia"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if proof.content_type not in ALLOWED_IMAGE_TYPES:
            return Response(
                {"detail": "Formato no permitido. Use JPEG o PNG"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if proof.size > MAX_UPLOAD_SIZE:
            return Response(
                {"detail": "El archivo excede 5 MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment.proof_image = proof
        payment.save(update_fields=["proof_image", "updated_at"])
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)


class PaymentConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        payment = get_object_or_404(Payment, pk=pk, booking__user=request.user)
        PaymentService.confirm(payment)
        return Response(PaymentSerializer(payment).data)


class PaymentConfirmTransferView(APIView):
    permission_classes = [IsStaffRole]

    def post(self, request, pk=None):
        payment = get_object_or_404(Payment, pk=pk, method=Payment.Method.TRANSFER)
        PaymentService.confirm_transfer(payment)
        return Response(PaymentSerializer(payment).data)


class PaymentRejectTransferView(APIView):
    permission_classes = [IsStaffRole]

    def post(self, request, pk=None):
        payment = get_object_or_404(
            Payment, pk=pk, method=Payment.Method.TRANSFER,
            status=Payment.Status.PENDING_TRANSFER,
        )
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response(
                {"detail": "El motivo de rechazo es obligatorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        PaymentService.reject_transfer(payment, reason)
        return Response(PaymentSerializer(payment).data)


class PaymentRefundView(APIView):
    permission_classes = [IsStaffRole]

    def post(self, request, pk=None):
        payment = get_object_or_404(Payment, pk=pk)
        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        PaymentService.refund(payment, serializer.validated_data["amount"])
        return Response(PaymentSerializer(payment).data)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks for payment_intent.payment_failed events."""
    import stripe
    from runsecrets import secrets as app_secrets

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        return HttpResponse(status=400)
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (stripe.error.SignatureVerificationError, ValueError):
        return HttpResponse(status=400)

    if event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        payment = Payment.objects.filter(
            stripe_payment_intent_id=intent["id"]
        ).first()
        if payment and payment.status != Payment.Status.FAILED:
            reason = ""
            if "last_payment_error" in intent:
                reason = intent["last_payment_error"].get("message", "")
            PaymentService.fail(payment, reason)

    return HttpResponse(status=200)
