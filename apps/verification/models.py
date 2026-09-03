import hmac
import secrets as _std
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

CODE_TTL = timedelta(minutes=15)
MAX_ATTEMPTS = 5


class VerificationCode(models.Model):
    class Purpose(models.TextChoices):
        EMAIL_VERIFY = "email_verify", "Verificacion de email"
        PASSWORD_RESET = "password_reset", "Restablecimiento de contrasena"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_codes",
    )
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "purpose", "code"), name="uniq_user_purpose_code"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"{_std.randbelow(10**6):06d}"
        if not self.expires_at:
            self.expires_at = timezone.now() + CODE_TTL
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.verified_at:
            return True
        if self.attempts >= MAX_ATTEMPTS:
            return True
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} [{self.purpose}]"


class VerificationCodeService:
    @staticmethod
    def issue(user, purpose):
        VerificationCode.objects.filter(user=user, purpose=purpose).delete()
        return VerificationCode.objects.create(user=user, purpose=purpose)

    @staticmethod
    def verify(user, purpose, code):
        try:
            instance = VerificationCode.objects.filter(
                user=user, purpose=purpose
            ).latest("created_at")
        except VerificationCode.DoesNotExist:
            return False
        if instance.is_expired:
            return False
        if hmac.compare_digest(instance.code, code):
            instance.verified_at = timezone.now()
            instance.save(update_fields=["verified_at"])
            return True
        instance.attempts += 1
        instance.save(update_fields=["attempts"])
        return False
