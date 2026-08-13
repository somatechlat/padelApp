from django.conf import settings
from django.db import models


class ConsentRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consent_records"
    )
    version = models.CharField(max_length=16)
    granted = models.BooleanField()
    source = models.CharField(max_length=32, default="app")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "registro de consentimiento"
        verbose_name_plural = "registros de consentimiento"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} v{self.version} {'si' if self.granted else 'no'}"
