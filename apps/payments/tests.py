from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.fixture
def confirmed_booking(court, user):
    from apps.bookings.services import BookingService
    from apps.courts.models import CourtSchedule

    for wd in range(7):
        CourtSchedule.objects.create(court=court, weekday=wd, open_time="08:00", close_time="22:00")
    day = timezone.localdate() + timedelta(days=2)
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


class TestPaymentSafetyBounds:
    """Refund/transfer paths must refuse double-processing and bad amounts."""

    def test_refund_rejects_amount_above_captured(self, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_cash(confirmed_booking, confirmed_booking.price)
        with pytest.raises(ValueError, match="No se puede reembolsar"):
            PaymentService.refund(payment, confirmed_booking.price + 100)

    def test_refund_rejects_non_positive_amount(self, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_cash(confirmed_booking, confirmed_booking.price)
        for bad in (0, -5):
            with pytest.raises(ValueError, match="mayor que cero"):
                PaymentService.refund(payment, bad)

    def test_refund_is_idempotent(self, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_cash(confirmed_booking, confirmed_booking.price)
        PaymentService.refund(payment, confirmed_booking.price)
        with pytest.raises(ValueError, match="ya fue reembolsado"):
            PaymentService.refund(payment, confirmed_booking.price)

    def test_confirm_transfer_is_idempotent(self, confirmed_booking):
        from apps.notifications.models import Notification
        from apps.payments.services import PaymentService

        payment = PaymentService.record_transfer(confirmed_booking, "REF-001")
        PaymentService.confirm_transfer(payment)
        PaymentService.confirm_transfer(payment)
        payment.refresh_from_db()
        assert payment.status == "captured"
        assert (
            Notification.objects.filter(
                user=confirmed_booking.user, event_type="transfer_confirmed"
            ).count()
            == 1
        )

    def test_reject_transfer_refuses_processed_payment(self, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_cash(confirmed_booking, confirmed_booking.price)
        with pytest.raises(ValueError, match="ya fue procesado"):
            PaymentService.reject_transfer(payment, "tarde")

    def test_cash_on_arrival_leaves_no_orphan_on_failed_transition(self, court, user):
        from apps.bookings.models import Booking
        from apps.payments.models import Payment
        from apps.payments.services import PaymentService

        booking = Booking.objects.create(
            user=user,
            court=court,
            date=timezone.localdate() + timedelta(days=1),
            start_time="10:00",
            end_time="11:00",
            duration_minutes=60,
            players=4,
            price="10.00",
            status="pending_payment",
        )
        # The race the atomic block guards: the booking cannot be confirmed
        # (cancelled underneath us, illegal transition, lock timeout, ...).
        before = Payment.objects.count()
        with mock.patch.object(
            Booking, "transition_to", side_effect=ValueError("Transicion ilegal")
        ):
            with pytest.raises(ValueError):
                PaymentService.record_cash_on_arrival(booking, booking.price)
        assert Payment.objects.count() == before
