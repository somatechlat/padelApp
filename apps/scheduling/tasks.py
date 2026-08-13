from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def release_expired_holds(self):
    """Cancel pending bookings whose hold expired and free their slots."""
    from apps.bookings.models import Booking
    from apps.bookings.services import BookingService
    from apps.scheduling.models import BookingHold

    expired_slot_ids = list(
        BookingHold.objects.filter(expires_at__lte=timezone.now())
        .values_list("slot_id", flat=True)
        .distinct()
    )
    if not expired_slot_ids:
        return 0
    pending = (
        Booking.objects.filter(
            status=Booking.Status.PENDING_PAYMENT,
            slots__slot_id__in=expired_slot_ids,
        )
        .select_related("user", "court")
        .distinct()
    )
    released = 0
    for booking in pending:
        try:
            BookingService.cancel(booking)
            released += 1
        except Exception:
            continue
    return released
