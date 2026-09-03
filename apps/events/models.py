from django.conf import settings
from django.db import models
from django.utils import timezone


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicado"
        CANCELLED = "cancelled", "Cancelado"

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
