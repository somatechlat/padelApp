from django.db import transaction

from apps.events.models import Tournament, TournamentRegistration


class TournamentService:
    @staticmethod
    def register(user, tournament, payment_reference=None):
        if tournament.status != Tournament.Status.OPEN:
            raise ValueError("El torneo no acepta inscripciones")
        from django.utils import timezone

        if timezone.now() > tournament.registration_deadline:
            tournament.close_if_deadline_passed()
            raise ValueError("Inscripciones cerradas")
        with transaction.atomic():
            locked = Tournament.objects.select_for_update().get(pk=tournament.pk)
            existing = TournamentRegistration.objects.filter(
                tournament=locked, user=user
            ).exists()
            if existing:
                raise ValueError("Ya estas inscrito en este torneo")
            used = TournamentRegistration.objects.filter(
                tournament=locked,
                status__in=(
                    TournamentRegistration.Status.PENDING_PAYMENT,
                    TournamentRegistration.Status.CONFIRMED,
                ),
            ).count()
            if used >= locked.capacity:
                raise ValueError("Torneo lleno")
            return TournamentRegistration.objects.create(
                tournament=locked, user=user
            )

    @staticmethod
    def confirm(registration):
        registration.status = TournamentRegistration.Status.CONFIRMED
        registration.save(update_fields=["status"])
        return registration
