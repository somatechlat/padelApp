from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeSlot(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponible"
        BOOKED = "booked", "Reservado"
        HELD = "held", "En espera"
        BLOCKED = "blocked", "Bloqueado"

    court = models.ForeignKey(
        "courts.Court", on_delete=models.CASCADE, related_name="slots"
    )
    date = models.DateField()
    start = models.TimeField()
    end = models.TimeField()
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.AVAILABLE
    )

    class Meta:
        verbose_name = "franja"
        verbose_name_plural = "franjas"
        ordering = ("date", "start")
        constraints = [
            models.UniqueConstraint(
                fields=("court", "date", "start"), name="uniq_court_date_start"
            ),
            models.CheckConstraint(
                condition=models.Q(end__gt=models.F("start")),
                name="chk_slot_time_order",
            ),
        ]
        indexes = [
            models.Index(fields=["court", "date", "status"], name="idx_slot_court_date_status"),
        ]

    def __str__(self):
        return f"{self.court} {self.date} {self.start}-{self.end}"


class MaintenanceWindow(models.Model):
    court = models.ForeignKey(
        "courts.Court", on_delete=models.CASCADE, related_name="maintenance_windows"
    )
    start = models.DateTimeField()
    end = models.DateTimeField()
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "mantenimiento"
        verbose_name_plural = "mantenimientos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end__gt=models.F("start")),
                name="chk_maintenance_time_order",
            ),
        ]

    def __str__(self):
        return f"{self.court} {self.start} - {self.end}"


class BookingHold(models.Model):
    court = models.ForeignKey("courts.Court", on_delete=models.CASCADE)
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name="holds")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holds"
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "reserva temporal"
        verbose_name_plural = "reservas temporales"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user} -> {self.slot}"
