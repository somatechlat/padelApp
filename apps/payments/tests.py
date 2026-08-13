from unittest import mock

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
def confirmed_booking(court, user):
    from apps.bookings.services import BookingService
    from apps.courts.models import CourtSchedule

    for wd in range(7):
        CourtSchedule.objects.create(
            court=court, weekday=wd, open_time="08:00", close_time="22:00"
        )
    day = timezone.localdate() + timezone.timedelta(days=2)
    booking = BookingService.hold(user, court, day, "10:00", 60)
    BookingService.confirm(booking)
    booking.refresh_from_db()
    return booking


class TestStripePayments:
    @mock.patch("stripe.PaymentIntent.create")
    def test_create_intent_returns_client_secret(self, mock_create, confirmed_booking):
        from apps.payments.services import PaymentService

        mock_create.return_value = mock.Mock(id="pi_123", client_secret="cs_secret")
        payment = PaymentService.create_intent(confirmed_booking)
        assert payment.method == "stripe"
        assert payment.status == "pending"
        assert payment.stripe_payment_intent_id == "pi_123"
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["amount"] == int(confirmed_booking.price * 100)
        assert mock_create.call_args.kwargs["currency"] == "usd"

    def test_confirm_captures_payment(self, confirmed_booking):
        from apps.payments.models import Payment
        from apps.payments.services import PaymentService

        payment = Payment.objects.create(
            booking=confirmed_booking,
            user=confirmed_booking.user,
            method="stripe",
            amount=confirmed_booking.price,
            currency="USD",
            stripe_payment_intent_id="pi_123",
        )
        PaymentService.confirm(payment)
        payment.refresh_from_db()
        assert payment.status == "captured"

    def test_refund_marks_payment_refunded(self, confirmed_booking):
        from apps.payments.models import Payment
        from apps.payments.services import PaymentService

        payment = Payment.objects.create(
            booking=confirmed_booking,
            user=confirmed_booking.user,
            method="stripe",
            amount=confirmed_booking.price,
            currency="USD",
            status="captured",
        )
        PaymentService.refund(payment, confirmed_booking.price)
        payment.refresh_from_db()
        assert payment.status == "refunded"


class TestTransferAndCash:
    def test_record_transfer_creates_pending(self, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_transfer(confirmed_booking, "REF-001")
        assert payment.method == "transfer"
        assert payment.status == "pending_transfer"
        assert payment.reference == "REF-001"

    def test_confirm_transfer(self, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_transfer(confirmed_booking, "REF-001")
        PaymentService.confirm_transfer(payment)
        payment.refresh_from_db()
        assert payment.status == "captured"

    def test_record_cash(self, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_cash(confirmed_booking, confirmed_booking.price)
        assert payment.method == "cash"
        assert payment.status == "captured"
