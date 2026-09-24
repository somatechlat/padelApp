from django.conf import settings
from django.db import models
from django.utils import timezone


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicado"
        CANCELLED = "cancelled", "Cancelado"

    class Category(models.TextChoices):
        QUEDADA = "quedada", "Quedada"
        TORNEO = "torneo", "Torneo"
        LIGA = "liga", "Liga"
        ACADEMIA = "academia", "Academia"
        NOTICIA = "noticia", "Noticia"

    class PublishedManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(status=Event.Status.PUBLISHED)

    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.QUEDADA)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="events_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        verbose_name = "evento"
        verbose_name_plural = "eventos"
        ordering = ("-created_at",)

    @property
    def title_localized(self):
        return self.title_es or self.title

    @property
    def description_localized(self):
        return self.description_es or self.description

    def __str__(self):
        return self.title_localized


class Tournament(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        OPEN = "open", "Inscripciones abiertas"
        CLOSED = "closed", "Inscripciones cerradas"
        IN_PROGRESS = "in_progress", "En curso"
        FINISHED = "finished", "Finalizado"

    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    capacity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    registration_deadline = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="tournaments_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "torneo"
        verbose_name_plural = "torneos"
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="chk_tournament_date_order",
            ),
            models.CheckConstraint(
                condition=models.Q(capacity__gt=0),
                name="chk_tournament_capacity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="chk_tournament_price_non_negative",
            ),
        ]

    @property
    def name_localized(self):
        return self.name_es or self.name

    @property
    def confirmed_count(self):
        return TournamentRegistration.objects.filter(
            tournament=self, status=TournamentRegistration.Status.CONFIRMED
        ).count()

    def close_if_deadline_passed(self):
        if (
            self.status == Tournament.Status.OPEN
            and timezone.now() > self.registration_deadline
        ):
            self.status = Tournament.Status.CLOSED
            self.save(update_fields=["status"])
            return True
        return False

    def __str__(self):
        return self.name_localized


class TournamentRegistration(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pendiente de pago"
        CONFIRMED = "confirmed", "Confirmado"
        CANCELLED = "cancelled", "Cancelado"

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tournament_registrations"
    )
    partner_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "inscripcion a torneo"
        verbose_name_plural = "inscripciones a torneos"
        constraints = [
            models.UniqueConstraint(
                fields=("tournament", "user"), name="uniq_tournament_user"
            )
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.tournament.name_localized}"


class OpenMatch(models.Model):
    """Client-created 'armar partido' — notifies everyone in the same category."""

    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        FULL = "full", "Completo"
        CANCELLED = "cancelled", "Cancelado"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="open_matches_created",
    )
    skill_level = models.ForeignKey(
        "users.SkillLevel",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="open_matches",
    )
    date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=90)
    max_players = models.PositiveIntegerField(default=4)
    notes = models.CharField(max_length=280, blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "partido abierto"
        verbose_name_plural = "partidos abiertos"
        ordering = ("date", "start_time")

    @property
    def players_count(self):
        return self.players.count()

    def notify_category(self):
        """Push + in-app a todos los jugadores de la misma categoría."""
        from apps.notifications.tasks import notify_task
        from apps.users.models import User

        title = "Nuevo partido en tu categoría"
        body = (
            f"{self.created_by.full_name or self.created_by.email} "
            f"armó un partido el {self.date} a las {self.start_time.strftime('%H:%M')}."
        )
        targets = User.objects.filter(
            skill_level_id=self.skill_level_id,
            status="active",
            is_active=True,
        ).exclude(id=self.created_by_id)
        for user in targets.iterator():
            notify_task.delay(
                user.id,
                "open_match_created",
                title,
                body,
                {"match_id": self.id, "skill_level": self.skill_level},
            )

    def __str__(self):
        level = self.skill_level.name if self.skill_level_id else "-"
        return f"Partido {self.date} {self.start_time} ({level})"


class OpenMatchPlayer(models.Model):
    match = models.ForeignKey(
        OpenMatch, on_delete=models.CASCADE, related_name="players"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="open_match_players",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "jugador de partido"
        verbose_name_plural = "jugadores de partido"
        constraints = [
            models.UniqueConstraint(
                fields=("match", "user"), name="uniq_openmatch_user"
            )
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.match_id}"


class NewsPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicado"

    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    body_es = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="news_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "noticia"
        verbose_name_plural = "noticias"
        ordering = ("-created_at",)

    @property
    def title_localized(self):
        return self.title_es or self.title

    @property
    def body_localized(self):
        return self.body_es or self.body

    def publish(self):
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at"])
        from apps.notifications.tasks import notify_task
        from django.contrib.auth import get_user_model

        for user in get_user_model().objects.filter(status="active").iterator():
            notify_task.delay(
                user.id,
                "news_published",
                self.title_localized,
                self.body_localized[:200],
                {"news_id": self.id},
            )

    def __str__(self):
        return self.title_localized
