from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "notificacion"
        verbose_name_plural = "notificaciones"
        ordering = ("-created_at",)

    def mark_read(self):
        from django.utils import timezone

        self.read_at = timezone.now()
        self.save(update_fields=["read_at"])

    def __str__(self):
        return f"{self.user} - {self.title}"


class NotificationPreference(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        PUSH = "push", "Push"
        INAPP = "inapp", "En la app"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_prefs"
    )
    event_type = models.CharField(max_length=50)
    channel = models.CharField(max_length=8, choices=Channel.choices)
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "preferencia de notificacion"
        verbose_name_plural = "preferencias de notificacion"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "event_type", "channel"), name="uniq_user_event_channel"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.event_type}/{self.channel}: {self.enabled}"


class DeviceToken(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens"
    )
    platform = models.CharField(max_length=8, choices=Platform.choices)
    token = models.CharField(max_length=512, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "token de dispositivo"
        verbose_name_plural = "tokens de dispositivo"

    def __str__(self):
        return f"{self.user} [{self.platform}]"
