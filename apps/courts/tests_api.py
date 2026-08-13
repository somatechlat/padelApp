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


class TestCourtList:
    def test_public_can_list_courts(self, api_client, court):
        resp = api_client.get("/api/courts/")
        assert resp.status_code == status.HTTP_200_OK
        assert any(c["name"] == "Cancha 1" for c in resp.data["results"])

    def test_court_detail(self, api_client, court):
        resp = api_client.get(f"/api/courts/{court.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["price_base"] == "12.00"

    def test_client_cannot_create_court(self, client, court):
        resp = client.post("/api/courts/", {"name": "X", "court_type": "abierta", "price_base": "10.00", "venue": court.venue_id})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_can_create_court(self, staff_client, court):
        resp = staff_client.post(
            "/api/courts/",
            {"name": "Cancha 2", "court_type": "abierta", "price_base": "10.00", "venue": court.venue_id},
        )
        assert resp.status_code == status.HTTP_201_CREATED

    def test_staff_can_archive_court(self, staff_client, court):
        resp = staff_client.patch(f"/api/courts/{court.id}/", {"status": "archived"})
        assert resp.status_code == status.HTTP_200_OK
        court.refresh_from_db()
        assert court.status == "archived"


class TestAvailabilityAPI:
    def test_availability_returns_free_slots(self, api_client, court):
        from apps.courts.models import CourtSchedule

        for wd in range(7):
            CourtSchedule.objects.create(court=court, weekday=wd, open_time="08:00", close_time="22:00")
        day = timezone.localdate() + timezone.timedelta(days=2)
        resp = api_client.get(f"/api/courts/{court.id}/availability/", {"date": day.isoformat()})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 28

    def test_availability_excludes_taken_slots(self, api_client, court, client_user):
        from apps.bookings.services import BookingService
        from apps.courts.models import CourtSchedule

        for wd in range(7):
            CourtSchedule.objects.create(court=court, weekday=wd, open_time="08:00", close_time="22:00")
        day = timezone.localdate() + timezone.timedelta(days=2)
        BookingService.hold(client_user, court, day, "10:00", 60)
        resp = api_client.get(f"/api/courts/{court.id}/availability/", {"date": day.isoformat()})
        assert resp.status_code == status.HTTP_200_OK
        starts = {s["start"] for s in resp.data}
        assert "10:00:00" not in starts
