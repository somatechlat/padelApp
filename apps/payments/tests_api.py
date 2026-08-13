from unittest import mock

import pytest
from django.utils import timezone
from rest_framework import status

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
def client_user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="c@test.com", password="pass12345")


@pytest.fixture
def client(api_client, client_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(client_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.fixture
def confirmed_booking(court, client_user):
    from apps.bookings.services import BookingService
    from apps.courts.models import CourtSchedule

    for wd in range(7):
        CourtSchedule.objects.create(court=court, weekday=wd, open_time="08:00", close_time="22:00")
    day = timezone.localdate() + timezone.timedelta(days=3)
    b = BookingService.hold(client_user, court, day, "10:00", 60)
    BookingService.confirm(b)
    b.refresh_from_db()
    return b


@pytest.fixture
def staff_user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="staff@test.com", password="pass12345", role="recepcionista"
    )


@pytest.fixture
def staff_client(api_client, staff_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(staff_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


class TestPaymentAPI:
    @mock.patch("stripe.PaymentIntent.create")
    def test_create_payment_intent(self, mock_create, client, confirmed_booking):
        mock_create.return_value = mock.Mock(id="pi_123", client_secret="cs_sec")
        resp = client.post(f"/api/bookings/{confirmed_booking.id}/payments/")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["method"] == "stripe"
        assert resp.data["amount"] == "12.00"

    def test_client_cannot_confirm_transfer(self, client, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_transfer(confirmed_booking, "REF-1")
        resp = client.post(f"/api/payments/{payment.id}/confirm-transfer/")
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_staff_can_confirm_transfer(self, staff_client, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_transfer(confirmed_booking, "REF-1")
        resp = staff_client.post(f"/api/payments/{payment.id}/confirm-transfer/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "captured"

    def test_staff_can_record_cash(self, staff_client, confirmed_booking):
        resp = staff_client.post(
            f"/api/bookings/{confirmed_booking.id}/payments/",
            {"method": "cash", "amount": "12.00"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["status"] == "captured"

    def test_staff_can_refund(self, staff_client, confirmed_booking):
        from apps.payments.services import PaymentService

        payment = PaymentService.record_cash(confirmed_booking, confirmed_booking.price)
        resp = staff_client.post(
            f"/api/payments/{payment.id}/refund/", {"amount": str(payment.amount)}
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "refunded"
