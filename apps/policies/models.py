from django.db import models


class CancellationPolicy(models.Model):
    venue = models.ForeignKey(
        "courts.Venue", on_delete=models.CASCADE, related_name="cancellation_policies"
    )
    free_window_hours = models.PositiveIntegerField(default=24)
    penalty_ratio = models.DecimalField(max_digits=4, decimal_places=2, default="0.50")
    no_show_ratio = models.DecimalField(max_digits=4, decimal_places=2, default="1.00")
    hold_minutes = models.PositiveIntegerField(default=10)
    # Concurrent temporary checkouts per user (a 90-min booking is ONE hold,
    # not three 30-min rows). Default is generous so real players never hit it.
    max_holds_per_user = models.PositiveIntegerField(default=5)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "politica de cancelacion"
        verbose_name_plural = "politicas de cancelacion"
        constraints = [
            models.UniqueConstraint(fields=("venue",), name="uniq_venue_cancellation_policy"),
        ]

    def __str__(self):
        return f"{self.venue} - gratis {self.free_window_hours}h"
