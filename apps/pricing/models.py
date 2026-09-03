from django.db import models


class PriceRule(models.Model):
    class Zone(models.TextChoices):
        VALLE = "valle", "Valle"
        PICO = "pico", "Pico"

    venue = models.ForeignKey(
        "courts.Venue", on_delete=models.CASCADE, related_name="price_rules"
    )
    name = models.CharField(max_length=120)
    zone = models.CharField(max_length=8, choices=Zone.choices, default=Zone.VALLE)
    day_of_week = models.PositiveSmallIntegerField(null=True, blank=True)
    court_type = models.CharField(
        max_length=10,
        choices=(("techada", "Techada"), ("abierta", "Abierta")),
        null=True,
        blank=True,
    )
    multiplier = models.DecimalField(max_digits=6, decimal_places=3)
    priority = models.PositiveSmallIntegerField(default=10)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "regla de precio"
        verbose_name_plural = "reglas de precio"

    def __str__(self):
        return f"{self.venue} - {self.name}"


class Holiday(models.Model):
    venue = models.ForeignKey(
        "courts.Venue", on_delete=models.CASCADE, related_name="holidays"
    )
    date = models.DateField()
    name = models.CharField(max_length=120)

    class Meta:
        verbose_name = "feriado"
        verbose_name_plural = "feriados"
        constraints = [
            models.UniqueConstraint(fields=("venue", "date"), name="uniq_venue_holiday_date"),
        ]

    def __str__(self):
        return f"{self.venue} - {self.name} ({self.date})"
