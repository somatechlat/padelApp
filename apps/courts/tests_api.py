from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

pytestmark = pytest.mark.django_db


@pytest.fixture
def venue():
    from apps.courts.models import Venue

    return Venue.objects.create(
        name="Andes Padel",
        address="Rodríguez Labandera y Ernesto Albán esquina, Quito",
        phone="099 267 6842",
        email="andespadelclub@gmail.com",
        whatsapp_number="593992676842",
        whatsapp_message="Hola, quiero reservar",
        instagram_url="https://instagram.com/andespadelec",
        maps_query="Rodríguez Labandera y Ernesto Albán esquina, Quito",
        maps_url="https://www.google.com/maps/search/?api=1&query=Quito",
        home_section_title_i18n={
            "es": "Reserva tu cancha",
            "en": "Book your court",
            "pt": "Reserve sua quadra",
            "ca": "Reserva la teva pista",
        },
        home_greeting_tagline_i18n={
            "es": "Reserva tu cancha de pádel",
            "en": "Book your padel court",
        },
        bank_name="Banco Pichincha",
        bank_account_number="21001234567890",
        bank_account_holder="Andes Pádel S.A.",
        bank_account_code="ANDESPADEL",
        bank_extra="Cuenta de ahorros",
        timezone="America/Guayaquil",
        currency="USD",
    )


def make_banner_image():
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(
        "banner.png",
        (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
            b"\xc0\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
        ),
        content_type="image/png",
    )


@pytest.fixture
def banner():
    from apps.courts.models import PromoBanner

    b = PromoBanner(
        title_i18n={"es": "Torneo de Verano", "en": "Summer Tournament"},
        subtitle_i18n={"es": "Inscripciones abiertas", "en": "Registration open"},
        link_type="none",
        active=True,
        sort_order=10,
    )
    b.image = make_banner_image()
    b.save()
    return b


class TestClubAPI:
    def test_public_can_get_club(self, api_client, venue):
        resp = api_client.get("/api/club/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["name"] == "Andes Padel"
        assert resp.data["address"] == "Rodríguez Labandera y Ernesto Albán esquina, Quito"
        assert resp.data["phone"] == "099 267 6842"
        assert resp.data["email"] == "andespadelclub@gmail.com"
        assert resp.data["whatsapp_number"] == "593992676842"
        assert resp.data["whatsapp_message"] == "Hola, quiero reservar"
        assert resp.data["instagram_url"] == "https://instagram.com/andespadelec"
        assert resp.data["maps_query"]
        assert resp.data["maps_url"]
        assert resp.data["bank_name"] == "Banco Pichincha"
        assert resp.data["bank_account_number"] == "21001234567890"
        assert resp.data["bank_account_holder"] == "Andes Pádel S.A."
        assert resp.data["bank_account_code"] == "ANDESPADEL"
        assert "logo_url" in resp.data
        assert "home_section_title" in resp.data
        assert "home_greeting_tagline" in resp.data

    def test_club_titles_resolved_by_lang_query(self, api_client, venue):
        resp = api_client.get("/api/club/", {"lang": "en"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["home_section_title"] == "Book your court"
        assert resp.data["home_greeting_tagline"] == "Book your padel court"

        resp = api_client.get("/api/club/", {"lang": "ca"})
        assert resp.data["home_section_title"] == "Reserva la teva pista"

    def test_club_titles_resolved_by_accept_language(self, api_client, venue):
        resp = api_client.get("/api/club/", HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["home_section_title"] == "Reserve sua quadra"

    def test_club_default_lang_is_es(self, api_client, venue):
        resp = api_client.get("/api/club/")
        assert resp.data["home_section_title"] == "Reserva tu cancha"

    def test_club_empty_when_no_venue(self, api_client):
        resp = api_client.get("/api/club/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["id"] is None
        assert resp.data["bank_name"] == ""


class TestBannerAPI:
    def test_public_lists_active_banners(self, api_client, banner):
        resp = api_client.get("/api/banners/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1
        item = resp.data[0]
        assert item["title"] == "Torneo de Verano"
        assert item["subtitle"] == "Inscripciones abiertas"
        assert item["image_url"]
        assert item["link_url"] == ""
        assert item["link_type"] == "none"

    def test_banner_titles_resolved_for_lang(self, api_client, banner):
        resp = api_client.get("/api/banners/", {"lang": "en"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data[0]["title"] == "Summer Tournament"
        assert resp.data[0]["subtitle"] == "Registration open"

    def test_excludes_inactive_banners(self, api_client, banner):
        banner.active = False
        banner.save()
        resp = api_client.get("/api/banners/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == []

    def test_excludes_expired_and_future_banners(self, api_client, banner):
        from apps.courts.models import PromoBanner

        now = timezone.now()
        expired = PromoBanner(
            title_i18n={"es": "Vencido"},
            active=True,
            ends_at=now - timedelta(days=1),
        )
        expired.image = make_banner_image()
        expired.save()
        future = PromoBanner(
            title_i18n={"es": "Futuro"},
            active=True,
            starts_at=now + timedelta(days=3),
        )
        future.image = make_banner_image()
        future.save()
        resp = api_client.get("/api/banners/")
        titles = [b["title"] for b in resp.data]
        assert titles == ["Torneo de Verano"]

    def test_ordered_by_sort_order(self, api_client, banner):
        from apps.courts.models import PromoBanner

        first = PromoBanner(
            title_i18n={"es": "Primero"},
            active=True,
            sort_order=1,
        )
        first.image = make_banner_image()
        first.save()
        resp = api_client.get("/api/banners/")
        assert [b["title"] for b in resp.data] == ["Primero", "Torneo de Verano"]


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
        day = timezone.localdate() + timedelta(days=2)
        resp = api_client.get(f"/api/courts/{court.id}/availability/", {"date": day.isoformat()})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 28

    def test_availability_excludes_taken_slots(self, api_client, court, client_user):
        from apps.bookings.services import BookingService
        from apps.courts.models import CourtSchedule

        for wd in range(7):
            CourtSchedule.objects.create(court=court, weekday=wd, open_time="08:00", close_time="22:00")
        day = timezone.localdate() + timedelta(days=2)
        BookingService.hold(client_user, court, day, "10:00", 60)
        resp = api_client.get(f"/api/courts/{court.id}/availability/", {"date": day.isoformat()})
        assert resp.status_code == status.HTTP_200_OK
        starts = {s["start"] for s in resp.data}
        assert "10:00:00" not in starts
