from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.users.managers import UserManager


class Role(models.TextChoices):
    CLIENTE = "cliente", "Cliente"
    RECEPCIONISTA = "recepcionista", "Recepcionista"
    GERENTE = "gerente", "Gerente"
    DUENO = "dueno", "Dueno"
    SUPERADMIN = "superadmin", "Superadmin"


class Status(models.TextChoices):
    ACTIVE = "active", "Activo"
    SUSPENDED = "suspended", "Suspendido"
    BLOCKED = "blocked", "Bloqueado"
    DELETED = "deleted", "Eliminado"


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    language_code = models.CharField(
        max_length=8, default="es", choices=settings.LANGUAGES
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CLIENTE
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.ACTIVE
    )
    email_verified = models.BooleanField(default=False)
    consent_version = models.CharField(max_length=16, null=True, blank=True)
    consent_ts = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.email

    @property
    def is_active_account(self):
        return self.status == Status.ACTIVE
