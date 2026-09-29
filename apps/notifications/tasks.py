import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def notify_task(self, user_id, event_type, title="", body="", data=None):
    from django.contrib.auth import get_user_model

    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        return None
    try:
        NotificationService.notify(user, event_type, title, body, data or {})
    except Exception as exc:
        raise self.retry(exc=exc) from exc
    return user_id


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def notify_admins_task(self, event_type, data=None, title="", body=""):
    """Push + email the club admins (settings > aviso de reservas)."""
    try:
        NotificationService.notify_admins(event_type, data or {}, title, body)
    except Exception as exc:
        raise self.retry(exc=exc) from exc
    return event_type


def _notify_booking_window(bookings, event_type, dedup=False):
    """Notify each booking's user; skip ones already notified when ``dedup``."""
    from apps.notifications.models import Notification

    sent = 0
    for booking in bookings:
        if dedup and Notification.objects.filter(
            user=booking.user,
            event_type=event_type,
            data__booking_id=booking.id,
        ).exists():
            continue
        try:
            NotificationService.notify(
                booking.user,
                event_type,
                data={
                    "court": booking.court.name,
                    "time": str(booking.start_time),
                    "booking_id": booking.id,
                },
            )
            sent += 1
        except Exception:
            logger.exception(
                "Failed to send %s for booking %s", event_type, booking.id
            )
    return sent


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_booking_reminders(self):
    """Notify confirmed players the day before their booking (24h reminder)."""
    from apps.bookings.models import Booking

    tomorrow = timezone.localdate() + timedelta(days=1)
    bookings = (
        Booking.objects.filter(date=tomorrow, status=Booking.Status.CONFIRMED)
        .select_related("user", "court")
        .only("id", "user_id", "court__name", "date", "start_time")
    )
    return _notify_booking_window(bookings, "booking_reminder")


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_booking_reminders_2h(self):
    """Notify confirmed players 2 hours before their booking starts."""
    from datetime import timedelta

    from apps.bookings.models import Booking

    now = timezone.localtime()
    in_2h = now + timedelta(hours=2)
    bookings = (
        Booking.objects.filter(
            date=now.date(),
            status=Booking.Status.CONFIRMED,
            start_time__gte=now.time(),
            start_time__lte=in_2h.time(),
        )
        .select_related("user", "court")
        .only("id", "user_id", "court__name", "date", "start_time")
    )
    return _notify_booking_window(bookings, "booking_reminder_2h", dedup=True)
