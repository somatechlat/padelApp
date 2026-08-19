from django.conf import settings
from django.db import models


class Payment(models.Model):
    class Method(models.TextChoices):
        STRIPE = "stripe", "Tarjeta"
        TRANSFER = "transfer", "Transferencia"
        CASH = "cash", "Efectivo"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        AUTHORIZED = "authorized", "Autorizado"
        PENDING_TRANSFER = "pending_transfer", "Pendiente de transferencia"
        CAPTURED = "captured", "Capturado"
        REFUNDED = "refunded", "Reembolsado"
        FAILED = "failed", "Fallido"
        CONFIRMED = "confirmed", "Confirmado"

    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.CASCADE, related_name="payments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    method = models.CharField(max_length=10, choices=Method.choices)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    stripe_payment_intent_id = models.CharField(max_length=128, blank=True)
    reference = models.CharField(max_length=128, blank=True)
    proof_image = models.ImageField(
        upload_to="transfer_proofs/%Y/%m/",
        blank=True,
        null=True,
        help_text="Foto del comprobante de transferencia bancaria",
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Motivo de rechazo de transferencia (visible para el cliente)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "pago"
        verbose_name_plural = "pagos"

    def __str__(self):
        return f"{self.method} {self.amount} {self.currency} - {self.status}"
