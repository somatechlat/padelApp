from django.db import models


class Venue(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=64, default="America/Guayaquil")
    currency = models.CharField(max_length=3, default="USD")
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "sede"
        verbose_name_plural = "sedes"

    def __str__(self):
        return self.name


class Court(models.Model):
    class CourtType(models.TextChoices):
        TECHADA = "techada", "Techada"
        ABIERTA = "abierta", "Abierta"

    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        ARCHIVED = "archived", "Archivada"
        MAINTENANCE = "maintenance", "En mantenimiento"

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="courts")
    name = models.CharField(max_length=80)
    court_type = models.CharField(max_length=10, choices=CourtType.choices, default=CourtType.TECHADA)
    has_lighting = models.BooleanField(default=False)
    price_base = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        verbose_name = "cancha"
        verbose_name_plural = "canchas"
        constraints = [
            models.UniqueConstraint(fields=("venue", "name"), name="uniq_venue_court_name")
        ]

    def __str__(self):
        return self.name


class CourtSchedule(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="schedules")
    weekday = models.PositiveSmallIntegerField()  # 0=Monday .. 6=Sunday
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "horario"
        verbose_name_plural = "horarios"
        constraints = [
            models.UniqueConstraint(
                fields=("court", "weekday"), name="uniq_court_weekday"
            ),
            models.CheckConstraint(
                condition=models.Q(weekday__gte=0) & models.Q(weekday__lte=6),
                name="chk_weekday_range",
            ),
            models.CheckConstraint(
                condition=models.Q(close_time__gt=models.F("open_time")),
                name="chk_schedule_time_order",
            ),
        ]

    def __str__(self):
        return f"{self.court.name} [{self.weekday}] {self.open_time}-{self.close_time}"
