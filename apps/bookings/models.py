from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.scheduling.models import TimeSlot


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pendiente de pago"
        CONFIRMED = "confirmed", "Confirmada"
        IN_PROGRESS = "in_progress", "En curso"
        COMPLETED = "completed", "Completada"
        CANCELLED = "cancelled", "Cancelada"
        NO_SHOW = "no_show", "No asistio"

    LEGAL_TRANSITIONS = {
        Status.PENDING_PAYMENT: {Status.CONFIRMED, Status.CANCELLED},
        Status.CONFIRMED: {Status.IN_PROGRESS, Status.CANCELLED, Status.NO_SHOW},
        Status.IN_PROGRESS: {Status.COMPLETED},
        Status.COMPLETED: set(),
        Status.CANCELLED: set(),
        Status.NO_SHOW: set(),
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    court = models.ForeignKey(
        "courts.Court", on_delete=models.CASCADE, related_name="bookings"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField()
    players = models.PositiveSmallIntegerField(default=4)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "reserva"
        verbose_name_plural = "reservas"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} - {self.court} {self.date} {self.start_time}"

    @property
    def start_at(self):
        from datetime import datetime

        return timezone.make_aware(
            datetime.combine(self.date, self.start_time), timezone.get_current_timezone()
        )

    def transition_to(self, new_status):
        current = self.status
        allowed = self.LEGAL_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise ValueError(f"Transicion ilegal: {current} -> {new_status}")
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])
        BookingEvent.objects.create(
            booking=self, from_status=current, to_status=new_status
        )
        return self


class BookingSlot(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="slots")
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name="bookings")

    class Meta:
        verbose_name = "franja de reserva"
        verbose_name_plural = "franjas de reserva"
        constraints = [
            models.UniqueConstraint(fields=("slot",), name="uniq_slot_booked_once")
        ]


class BookingEvent(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "evento de reserva"
        verbose_name_plural = "eventos de reserva"
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.booking_id}: {self.from_status} -> {self.to_status}"
