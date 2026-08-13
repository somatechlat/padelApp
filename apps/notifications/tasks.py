from celery import shared_task
from django.utils import timezone

from apps.notifications.services import NotificationService


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
def send_booking_reminders(self):
    """Notify confirmed players the day before their booking."""
    from apps.bookings.models import Booking

    tomorrow = timezone.localdate() + timezone.timedelta(days=1)
    bookings = (
        Booking.objects.filter(date=tomorrow, status=Booking.Status.CONFIRMED)
        .select_related("user", "court")
        .only("id", "user_id", "court__name", "date", "start_time")
    )
    sent = 0
    for booking in bookings:
        try:
            NotificationService.notify(
                booking.user,
                "booking_reminder",
                data={
                    "court": booking.court.name,
                    "time": str(booking.start_time),
                    "booking_id": booking.id,
                },
            )
            sent += 1
        except Exception:
            continue
    return sent
