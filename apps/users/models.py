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


class SkillLevel(models.Model):
    """Nivel / categoría de juego. Combo box options — editable in admin."""

    name = models.CharField(max_length=60, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "nivel de juego"
        verbose_name_plural = "niveles de juego"
        ordering = ("order", "name")

    def __str__(self):
        return self.name


class User(AbstractUser):
    username = None  # type: ignore[assignment]
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120)
    # Registration form: Nombre / Apellido / Correo / Clave /
    # Fecha de nacimiento / Nivel de juego (combo from SkillLevel)
    first_name = models.CharField(max_length=60, blank=True)
    last_name = models.CharField(max_length=60, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    skill_level = models.ForeignKey(
        SkillLevel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
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

    objects = UserManager()  # type: ignore[assignment, misc]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Keep full_name in sync with Nombre + Apellido for search/admin lists.
        joined = f"{self.first_name} {self.last_name}".strip()
        if joined:
            self.full_name = joined
        if self.role not in Role.values:
            raise ValueError(f"Rol invalido: {self.role}")
        if self.status not in Status.values:
            raise ValueError(f"Estado invalido: {self.status}")
        super().save(*args, **kwargs)

    @property
    def is_active_account(self):
        return self.status == Status.ACTIVE
