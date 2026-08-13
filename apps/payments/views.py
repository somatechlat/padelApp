from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer, RefundSerializer
from apps.payments.services import PaymentService
from apps.users.permissions import IsOwnerOrStaff, IsStaffRole


class BookingPaymentView(APIView):
    permission_classes = [IsOwnerOrStaff]

    def post(self, request, booking_id=None):
        booking = get_object_or_404(
            Booking.objects.filter(user=request.user) if request.user.role == "cliente" else Booking.objects.all(),
            pk=booking_id,
        )
        method = request.data.get("method", "stripe")
        if method == "cash":
            if request.user.role == "cliente":
                return Response(status=status.HTTP_403_FORBIDDEN)
            payment = PaymentService.record_cash(booking, request.data.get("amount") or booking.price)
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


class PaymentRefundView(APIView):
    permission_classes = [IsStaffRole]

    def post(self, request, pk=None):
        payment = get_object_or_404(Payment, pk=pk)
        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        PaymentService.refund(payment, serializer.validated_data["amount"])
        return Response(PaymentSerializer(payment).data)
