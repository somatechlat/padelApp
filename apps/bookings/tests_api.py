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
def scheduled_court(court):
    from apps.courts.models import CourtSchedule

    for wd in range(7):
        CourtSchedule.objects.create(court=court, weekday=wd, open_time="08:00", close_time="22:00")
    return court


def _future_day():
    return timezone.localdate() + timezone.timedelta(days=3)


class TestBookingAPI:
    def test_preview_returns_price(self, client, scheduled_court):
        resp = client.post(
            "/api/bookings/preview/",
            {"court": scheduled_court.id, "date": _future_day().isoformat(), "start_time": "10:00", "duration_minutes": 60},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["price"] == "12.00"

    def test_create_booking(self, client, scheduled_court):
        resp = client.post(
            "/api/bookings/",
            {"court": scheduled_court.id, "date": _future_day().isoformat(), "start_time": "10:00", "duration_minutes": 60, "players": 4},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["status"] == "pending_payment"

    def test_confirm_booking(self, client, scheduled_court):
        created = client.post(
            "/api/bookings/",
            {"court": scheduled_court.id, "date": _future_day().isoformat(), "start_time": "10:00", "duration_minutes": 60},
        ).data
        resp = client.post(f"/api/bookings/{created['id']}/confirm/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "confirmed"

    def test_cancel_booking(self, client, scheduled_court):
        created = client.post(
            "/api/bookings/",
            {"court": scheduled_court.id, "date": _future_day().isoformat(), "start_time": "10:00", "duration_minutes": 60},
        ).data
        resp = client.post(f"/api/bookings/{created['id']}/cancel/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "cancelled"

    def test_list_my_bookings(self, client, scheduled_court):
        client.post(
            "/api/bookings/",
            {"court": scheduled_court.id, "date": _future_day().isoformat(), "start_time": "10:00", "duration_minutes": 60},
        )
        resp = client.get("/api/bookings/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1

    def test_other_user_cannot_access_booking(self, client, scheduled_court):
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import RefreshToken

        created = client.post(
            "/api/bookings/",
            {"court": scheduled_court.id, "date": _future_day().isoformat(), "start_time": "10:00", "duration_minutes": 60},
        ).data
        other = get_user_model().objects.create_user(email="o@test.com", password="pass12345")
        from rest_framework.test import APIClient

        oc = APIClient()
        oc.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
        resp = oc.get(f"/api/bookings/{created['id']}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_booking_requires_auth(self, api_client, scheduled_court):
        resp = api_client.post(
            "/api/bookings/",
            {"court": scheduled_court.id, "date": _future_day().isoformat(), "start_time": "10:00", "duration_minutes": 60},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
