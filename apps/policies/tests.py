from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.fixture
def policy(venue):
    from apps.policies.models import CancellationPolicy

    return CancellationPolicy.objects.create(
        venue=venue,
        free_window_hours=24,
        penalty_ratio="0.50",
        no_show_ratio="1.00",
        hold_minutes=10,
    )


@pytest.fixture
def booking(court, user):
    from apps.bookings.services import BookingService
    from apps.courts.models import CourtSchedule

    for wd in range(7):
        CourtSchedule.objects.create(
            court=court, weekday=wd, open_time="08:00", close_time="22:00"
        )
    day = timezone.localdate() + timedelta(days=5)
    b = BookingService.hold(user, court, day, "10:00", 60)
    BookingService.confirm(b)
    b.refresh_from_db()
    return b


class TestPenaltyPolicy:
    def test_free_cancellation_inside_window(self, policy, booking):
        from apps.policies.services import PolicyService

        now = booking.start_at - timedelta(hours=25)
        result = PolicyService.evaluate(booking, now)
        assert result.ratio == 0
        assert result.amount == 0

    def test_penalty_inside_24h(self, policy, booking):
        from apps.policies.services import PolicyService

        now = booking.start_at - timedelta(hours=12)
        result = PolicyService.evaluate(booking, now)
        assert result.ratio == Decimal("0.50")
        assert result.amount == booking.price * Decimal("0.5")

    def test_full_penalty_at_no_show(self, policy, booking):
        from apps.policies.services import PolicyService

        now = booking.start_at + timedelta(minutes=30)
        result = PolicyService.evaluate(booking, now)
        assert result.ratio == Decimal("1.00")
        assert result.amount == booking.price

    def test_no_show_marks_booking_and_charges(self, policy, booking):
        from apps.policies.services import PolicyService

        PolicyService.mark_no_show(booking)
        booking.refresh_from_db()
        assert booking.status == "no_show"
        assert all(s.slot.status == "booked" for s in booking.slots.all())
