from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

DEFAULT_LANG = "es"


def resolve_i18n(data, lang=None, fallback_lang=DEFAULT_LANG):
    """Resolve a translated string from a JSONField dict.

    Falls back to ``fallback_lang`` and then to the first non-empty value.
    """
    if not isinstance(data, dict):
        return data or ""
    lang = (lang or "").split("-")[0].lower() or fallback_lang
    value = data.get(lang)
    if value:
        return value
    value = data.get(fallback_lang)
    if value:
        return value
    for item in data.values():
        if item:
            return item
    return ""


class Venue(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=64, default="America/Guayaquil")
    currency = models.CharField(max_length=3, default="USD")
    active = models.BooleanField(default=True)

    # Contact / social (admin-managed; nothing hardcoded in mobile)
    maps_query = models.CharField(max_length=255, blank=True, default="")
    maps_url = models.URLField(max_length=500, blank=True, default="")
    phone = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    whatsapp_number = models.CharField(max_length=40, blank=True, default="")
    whatsapp_message = models.CharField(max_length=500, blank=True, default="")
    instagram_url = models.URLField(max_length=500, blank=True, default="")
    logo = models.ImageField(upload_to="club/", blank=True, null=True)

    # Admin reservation alerts (push + email). Email is editable in Admin > Ajustes.
    booking_alert_email = models.EmailField(
        blank=True,
        default="",
        help_text="Email que recibe aviso de cada nueva reserva",
    )
    booking_alert_push = models.BooleanField(
        default=True,
        help_text="Enviar push a los administradores en cada nueva reserva",
    )

    # Multilingual home copy (es / en / pt / ca)
    home_section_title_i18n = models.JSONField(default=dict, blank=True)
    home_greeting_tagline_i18n = models.JSONField(default=dict, blank=True)

    # Bank transfer data (admin-managed)
    bank_name = models.CharField(max_length=120, blank=True, default="")
    bank_account_number = models.CharField(max_length=120, blank=True, default="")
    bank_account_holder = models.CharField(max_length=160, blank=True, default="")
    bank_account_code = models.CharField(max_length=80, blank=True, default="")
    bank_extra = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "sede"
        verbose_name_plural = "sedes"

    def __str__(self):
        return self.name

    def home_section_title_for(self, lang=None, fallback_lang=DEFAULT_LANG):
        return resolve_i18n(self.home_section_title_i18n, lang, fallback_lang)

    def home_greeting_tagline_for(self, lang=None, fallback_lang=DEFAULT_LANG):
        return resolve_i18n(self.home_greeting_tagline_i18n, lang, fallback_lang)

    def logo_url(self, request=None):
        if not self.logo:
            return ""
        url = self.logo.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class PromoBanner(models.Model):
    class LinkType(models.TextChoices):
        NONE = "none", "Sin enlace"
        URL = "url", "URL"
        WHATSAPP = "whatsapp", "WhatsApp"
        EVENT = "event", "Evento"

    title_i18n = models.JSONField(default=dict, blank=True)
    subtitle_i18n = models.JSONField(default=dict, blank=True)
    image = models.ImageField(upload_to="banners/%Y/%m/")
    link_url = models.URLField(max_length=500, blank=True, default="")
    link_type = models.CharField(max_length=12, choices=LinkType.choices, default=LinkType.NONE)
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "banner"
        verbose_name_plural = "banners"
        ordering = ("sort_order", "-created_at")

    def save(self, *args, **kwargs):
        if not self.image:
            raise ValidationError(_("La imagen del banner es obligatoria."))
        super().save(*args, **kwargs)

    def clear_image(self):
        """Persist empty image (admin remove). Bypasses required-on-save."""
        if self.image:
            self.image.delete(save=False)
        self.image = ""
        super().save(update_fields=["image"])

    def __str__(self):
        return self.title_for() or f"Banner #{self.pk}"

    def title_for(self, lang=None, fallback_lang=DEFAULT_LANG):
        return resolve_i18n(self.title_i18n, lang, fallback_lang)

    def subtitle_for(self, lang=None, fallback_lang=DEFAULT_LANG):
        return resolve_i18n(self.subtitle_i18n, lang, fallback_lang)

    def is_visible_now(self, at=None):
        at = at or timezone.now()
        if not self.active:
            return False
        if self.starts_at and at < self.starts_at:
            return False
        if self.ends_at and at > self.ends_at:
            return False
        return True

    def image_url(self, request=None):
        if not self.image:
            return ""
        url = self.image.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url


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
    description = models.TextField(
        blank=True, default="", help_text="Descripcion de la cancha visible para los clientes"
    )
    court_type = models.CharField(
        max_length=10, choices=CourtType.choices, default=CourtType.TECHADA
    )
    has_lighting = models.BooleanField(default=False)
    price_base = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(
        upload_to="courts/%Y/%m/", blank=True, null=True, help_text="Foto de la cancha"
    )
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
            models.UniqueConstraint(fields=("court", "weekday"), name="uniq_court_weekday"),
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
