import threading
from decimal import Decimal

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.fixture
def venue():
    from apps.courts.models import Venue

    return Venue.objects.create(name="Andes Padel", timezone="America/Guayaquil", currency="USD")


@pytest.fixture
def court(venue):
    from apps.courts.models import Court

    return Court.objects.create(
        venue=venue, name="Cancha 1", court_type="techada", price_base="12.00"
    )


@pytest.fixture
def user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="u@test.com", password="pass12345")


@pytest.fixture
def scheduled_court(court):
    from apps.courts.models import CourtSchedule

    for wd in range(7):
        CourtSchedule.objects.create(
            court=court, weekday=wd, open_time="08:00", close_time="22:00"
        )
    return court


def _future_day():
    return timezone.localdate() + timezone.timedelta(days=1)


class TestBookingCreation:
    def test_hold_creates_draft_booking_and_marks_slot(self, scheduled_court, user):
        from apps.bookings.services import BookingService

        booking = BookingService.hold(user, scheduled_court, _future_day(), "10:00", 60)
        assert booking.status == "pending_payment"
        assert booking.duration_minutes == 60
        assert booking.players == 4
        assert booking.court == scheduled_court
        assert booking.price > 0
        assert booking.slots.count() == 2

    def test_price_preview_matches_tariff(self, scheduled_court, user):
        from apps.bookings.services import BookingService

        price = BookingService.preview(scheduled_court, _future_day(), "10:00", 60)
        assert price == Decimal("12.00")

    def test_hold_rejects_already_held_slot(self, scheduled_court, user):
        from django.contrib.auth import get_user_model
        from apps.bookings.services import BookingService

        BookingService.hold(user, scheduled_court, _future_day(), "10:00", 60)
        other = get_user_model().objects.create_user(email="o@test.com", password="pass12345")
        with pytest.raises(Exception, match="disponible"):
            BookingService.hold(other, scheduled_court, _future_day(), "10:00", 60)

    def test_hold_rejects_past_time(self, scheduled_court, user):
        from apps.bookings.services import BookingService

        with pytest.raises(Exception, match="paso"):
            BookingService.hold(user, scheduled_court, timezone.localdate() - timezone.timedelta(days=1), "08:00", 60)

    def test_confirm_booking(self, scheduled_court, user):
        from apps.bookings.services import BookingService

        booking = BookingService.hold(user, scheduled_court, _future_day(), "10:00", 60)
        BookingService.confirm(booking)
        booking.refresh_from_db()
        assert booking.status == "confirmed"
        assert all(s.slot.status == "booked" for s in booking.slots.all())

    def test_cancel_releases_slots(self, scheduled_court, user):
        from apps.bookings.services import BookingService

        booking = BookingService.hold(user, scheduled_court, _future_day(), "10:00", 60)
        BookingService.cancel(booking)
        booking.refresh_from_db()
        assert booking.status == "cancelled"
        assert all(s.slot.status == "available" for s in booking.slots.all())


class TestStateMachine:
    def test_illegal_transition_rejected(self, scheduled_court, user):
        from apps.bookings.models import Booking
        from apps.bookings.services import BookingService

        booking = BookingService.hold(user, scheduled_court, _future_day(), "10:00", 60)
        with pytest.raises(Exception):
            booking.transition_to("completed")

    def test_transition_history_audited(self, scheduled_court, user):
        from apps.bookings.services import BookingService

        booking = BookingService.hold(user, scheduled_court, _future_day(), "10:00", 60)
        BookingService.confirm(booking)
        events = booking.events.all()
        assert events.count() == 1
        assert events[0].to_status == "confirmed"


class TestConcurrency:
    @pytest.mark.django_db(transaction=True)
    def test_no_double_booking_under_race(self, scheduled_court, user):
        from apps.bookings.services import BookingService
        from django.contrib.auth import get_user_model

        results = []

        def worker(worker_id):
            import django

            django.db.connections.close_all()
            try:
                u = get_user_model().objects.create_user(
                    email=f"race{worker_id}@test.com", password="pass12345"
                )
                b = BookingService.hold(u, scheduled_court, _future_day(), "14:00", 60)
                results.append(b)
            except Exception as e:  # noqa: BLE001
                results.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) == 1
