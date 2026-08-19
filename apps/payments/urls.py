from django.urls import path

from apps.payments.views import (
    BookingPaymentView,
    PaymentConfirmTransferView,
    PaymentConfirmView,
    PaymentProofUploadView,
    PaymentRefundView,
    PaymentRejectTransferView,
    stripe_webhook,
)

app_name = "payments"

urlpatterns = [
    path(
        "bookings/<int:booking_id>/payments/",
        BookingPaymentView.as_view(),
        name="booking-payment",
    ),
    path(
        "payments/<int:pk>/upload-proof/",
        PaymentProofUploadView.as_view(),
        name="payment-upload-proof",
    ),
    path("payments/<int:pk>/confirm/", PaymentConfirmView.as_view(), name="payment-confirm"),
    path(
        "payments/<int:pk>/confirm-transfer/",
        PaymentConfirmTransferView.as_view(),
        name="payment-confirm-transfer",
    ),
    path(
        "payments/<int:pk>/reject-transfer/",
        PaymentRejectTransferView.as_view(),
        name="payment-reject-transfer",
    ),
    path("payments/<int:pk>/refund/", PaymentRefundView.as_view(), name="payment-refund"),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
]
