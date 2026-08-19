from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.events.models import Tournament, TournamentRegistration


class TournamentService:
    @staticmethod
    def register(user, tournament, payment_reference=None, partner_name=""):
        if tournament.status != Tournament.Status.OPEN:
            raise ValueError(_("El torneo no acepta inscripciones"))
        if timezone.now() > tournament.registration_deadline:
            tournament.close_if_deadline_passed()
            raise ValueError(_("Inscripciones cerradas"))
        with transaction.atomic():
            locked = Tournament.objects.select_for_update().get(pk=tournament.pk)
            existing = TournamentRegistration.objects.filter(
                tournament=locked, user=user
            ).exists()
            if existing:
                raise ValueError(_("Ya estas inscrito en este torneo"))
            used = TournamentRegistration.objects.filter(
                tournament=locked,
                status__in=(
                    TournamentRegistration.Status.PENDING_PAYMENT,
                    TournamentRegistration.Status.CONFIRMED,
                ),
            ).count()
            if used >= locked.capacity:
                raise ValueError(_("Torneo lleno"))
            reg = TournamentRegistration.objects.create(
                tournament=locked, user=user, partner_name=partner_name
            )
        from apps.security.services import log_event
        log_event(user, "tournament.register", "TournamentRegistration", reg.id)
        from apps.notifications.tasks import notify_task
        notify_task.delay(
            user.id,
            "tournament_registered",
            "",
            "",
            {
                "tournament": tournament.name_localized,
                "tournament_id": tournament.id,
            },
        )
        return reg

    @staticmethod
    def confirm(registration):
        registration.status = TournamentRegistration.Status.CONFIRMED
        registration.save(update_fields=["status"])
        from apps.notifications.services import NotificationService

        NotificationService.notify(
            registration.user,
            "tournament_confirmed",
            data={"tournament": registration.tournament.name_localized, "tournament_id": registration.tournament_id},
        )
        return registration
