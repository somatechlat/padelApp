from django.urls import path

from apps.payments.views import (
    BookingPaymentView,
    PaymentConfirmTransferView,
    PaymentConfirmView,
    PaymentRefundView,
)

app_name = "payments"

urlpatterns = [
    path(
        "bookings/<int:booking_id>/payments/",
        BookingPaymentView.as_view(),
        name="booking-payment",
    ),
    path("payments/<int:pk>/confirm/", PaymentConfirmView.as_view(), name="payment-confirm"),
    path(
        "payments/<int:pk>/confirm-transfer/",
        PaymentConfirmTransferView.as_view(),
        name="payment-confirm-transfer",
    ),
    path("payments/<int:pk>/refund/", PaymentRefundView.as_view(), name="payment-refund"),
]
