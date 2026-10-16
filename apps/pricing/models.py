from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class PriceRule(models.Model):
    class Zone(models.TextChoices):
        VALLE = "valle", "Valle"
        PICO = "pico", "Pico"

    class Scope(models.TextChoices):
        """Which days of the week the rule covers. Only used when day_of_week is empty."""

        ALL = "all", "Todos los días"
        WEEKDAYS = "weekdays", "Entre semana"
        WEEKEND = "weekend", "Fin de semana"

    venue = models.ForeignKey("courts.Venue", on_delete=models.CASCADE, related_name="price_rules")
    name = models.CharField(max_length=120)
    zone = models.CharField(max_length=8, choices=Zone.choices, default=Zone.VALLE)
    day_of_week = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=(
            (0, "Lunes"),
            (1, "Martes"),
            (2, "Miércoles"),
            (3, "Jueves"),
            (4, "Viernes"),
            (5, "Sábado"),
            (6, "Domingo"),
        ),
        verbose_name="día específico",
    )
    scope = models.CharField(
        max_length=10,
        choices=Scope.choices,
        default=Scope.ALL,
        verbose_name="ambito de días",
    )
    court_type = models.CharField(
        max_length=10,
        choices=(("techada", "Techada"), ("abierta", "Abierta")),
        null=True,
        blank=True,
    )
    start_time = models.TimeField(null=True, blank=True, verbose_name="hora de inicio")
    end_time = models.TimeField(null=True, blank=True, verbose_name="hora de fin")
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="precio por hora",
    )
    multiplier = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="multiplicador",
    )
    priority = models.PositiveSmallIntegerField(default=10)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "regla de precio"
        verbose_name_plural = "reglas de precio"

    def __str__(self):
        return f"{self.venue} - {self.name}"

    def clean(self):
        """A rule carries a day, a time window and exactly one way to express a price."""
        if (self.start_time is None) != (self.end_time is None):
            raise ValidationError(
                "Indique la hora de inicio y la hora de fin, o ninguna de las dos."
            )
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("La hora de fin debe ser posterior a la hora de inicio.")
        if self.price is None and self.multiplier is None:
            raise ValidationError("Indique el precio por hora o el multiplicador.")
        if self.price is not None and self.multiplier is not None:
            raise ValidationError("Indique el precio por hora o el multiplicador, no ambos.")

    @property
    def day_scope_display(self):
        """An explicit day wins over the weekday/weekend scope."""
        if self.day_of_week is not None:
            return self.get_day_of_week_display()
        return self.get_scope_display()

    @property
    def start_time_display(self):
        return self.start_time.strftime("%H:%M") if self.start_time else ""

    @property
    def end_time_display(self):
        return self.end_time.strftime("%H:%M") if self.end_time else ""

    @property
    def price_display(self):
        """'' when the rule prices by multiplier. No amount is substituted."""
        if self.price in (None, ""):
            return ""
        return f"{Decimal(str(self.price)):.2f}"

    @property
    def multiplier_display(self):
        if self.multiplier in (None, ""):
            return ""
        return f"x{Decimal(str(self.multiplier))}"


class Holiday(models.Model):
    venue = models.ForeignKey("courts.Venue", on_delete=models.CASCADE, related_name="holidays")
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
