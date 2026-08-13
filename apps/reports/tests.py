import pytest
from django.utils import timezone

from apps.bookings.models import Booking
from apps.courts.models import Court, Venue
from apps.payments.models import Payment
from apps.reports.services import ReportService

pytestmark = pytest.mark.django_db


@pytest.fixture
def venue():
    return Venue.objects.create(name="Andes Padel")


@pytest.fixture
def court(venue):
    return Court.objects.create(venue=venue, name="Cancha 1", price_base="10.00")


@pytest.fixture
def user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="c@test.com", password="pass12345")


def _make_booking(user, court, day, price, status=Booking.Status.COMPLETED):
    return Booking.objects.create(
        user=user,
        court=court,
        date=day,
        start_time=timezone.datetime.strptime("10:00", "%H:%M").time(),
        end_time=timezone.datetime.strptime("11:00", "%H:%M").time(),
        duration_minutes=60,
        players=4,
        price=price,
        status=status,
    )


class TestRevenueReports:
    def test_revenue_by_day(self, venue, court, user):
        today = timezone.localdate()
        b1 = _make_booking(user, court, today, "20.00")
        Payment.objects.create(
            booking=b1, user=user, method=Payment.Method.CASH,
            amount="20.00", status=Payment.Status.CAPTURED,
        )
        rows = ReportService.revenue_by_period(today, today, period="day")
        assert sum(float(r["total"]) for r in rows) == 20.0

    def test_ignores_refunded_and_pending(self, venue, court, user):
        today = timezone.localdate()
        b1 = _make_booking(user, court, today, "10.00")
        b2 = _make_booking(user, court, today, "15.00")
        Payment.objects.create(
            booking=b1, user=user, method=Payment.Method.CASH,
            amount="10.00", status=Payment.Status.REFUNDED,
        )
        Payment.objects.create(
            booking=b2, user=user, method=Payment.Method.TRANSFER,
            amount="15.00", status=Payment.Status.PENDING_TRANSFER,
        )
        rows = ReportService.revenue_by_period(today, today, period="day")
        assert sum(float(r["total"]) for r in rows) == 0.0

    def test_revenue_by_court_and_method(self, venue, court, user):
        today = timezone.localdate()
        b1 = _make_booking(user, court, today, "20.00")
        Payment.objects.create(
            booking=b1, user=user, method=Payment.Method.STRIPE,
            amount="20.00", status=Payment.Status.CAPTURED,
        )
        by_court = ReportService.revenue_by_court(today, today)
        assert by_court[0]["court"] == "Cancha 1"
        assert float(by_court[0]["total"]) == 20.0
        by_method = ReportService.revenue_by_method(today, today)
        assert by_method[0]["method"] == "stripe"


class TestOperationalReports:
    def test_occupancy_percentage(self, venue, court, user):
        today = timezone.localdate()
        from apps.scheduling.models import TimeSlot

        for t in ("10:00", "10:30", "11:00", "11:30"):
            TimeSlot.objects.create(
                court=court, date=today,
                start=timezone.datetime.strptime(t, "%H:%M").time(),
                end=timezone.datetime.strptime(
                    timezone.datetime.strptime(t, "%H:%M").replace(minute=30).strftime("%H:%M"),
                    "%H:%M",
                ).time(),
                status=TimeSlot.Status.AVAILABLE,
            )
        TimeSlot.objects.filter(start__in=("10:00", "10:30")).update(
            status=TimeSlot.Status.BOOKED
        )
        result = ReportService.occupancy_percentage(today, today)
        assert result["booked"] == 2
        assert result["total"] == 4
        assert result["pct"] == 50.0

    def test_top_customers(self, venue, court, user):
        today = timezone.localdate()
        b1 = _make_booking(user, court, today, "20.00")
        Payment.objects.create(
            booking=b1, user=user, method=Payment.Method.CASH,
            amount="20.00", status=Payment.Status.CAPTURED,
        )
        top = ReportService.top_customers(today, today)
        assert top[0]["email"] == "c@test.com"
        assert top[0]["revenue"] == 20.0
        assert top[0]["bookings"] == 1

    def test_cancellation_and_no_show_rates(self, venue, court, user):
        today = timezone.localdate()
        _make_booking(user, court, today, "10.00", status=Booking.Status.CANCELLED)
        _make_booking(user, court, today, "10.00", status=Booking.Status.NO_SHOW)
        _make_booking(user, court, today, "10.00", status=Booking.Status.COMPLETED)
        result = ReportService.cancellation_rate(today, today)
        assert result["cancelled"] == 1
        assert result["total"] == 3
        assert result["pct"] == pytest.approx(33.33, abs=0.1)
        ns = ReportService.no_show_rate(today, today)
        assert ns["no_show"] == 1
