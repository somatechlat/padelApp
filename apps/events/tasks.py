from celery import shared_task
from django.utils import timezone

from apps.events.models import Tournament, TournamentRegistration
from apps.notifications.services import NotificationService


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def tournament_reminder_task(self):
    """Notify confirmed participants one day before the tournament starts."""
    start = timezone.now() + timezone.timedelta(days=1)
    start_day = start.date()
    tournaments = Tournament.objects.filter(
        status__in=(Tournament.Status.OPEN, Tournament.Status.IN_PROGRESS),
        start_date=start_day,
    )
    sent = 0
    for tournament in tournaments:
        regs = tournament.registrations.filter(
            status=TournamentRegistration.Status.CONFIRMED
        ).select_related("user")
        for reg in regs:
            try:
                NotificationService.notify(
                    reg.user,
                    "tournament_reminder",
                    data={
                        "tournament": tournament.name_localized,
                        "tournament_id": tournament.id,
                    },
                )
                sent += 1
            except Exception:
                continue
    return sent
