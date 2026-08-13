import pytest
from django.utils import timezone

from apps.bookings.models import Booking
from apps.courts.models import Court, Venue
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_user(db):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="gerente@test.com", password="pass12345", role="gerente"
    )


@pytest.fixture
def client_user(db):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="cli@test.com", password="pass12345", role="cliente"
    )


@pytest.fixture
def authed(api_client, api_user):
    api_client.force_authenticate(api_user)
    return api_client


@pytest.fixture
def court(db):
    venue = Venue.objects.create(name="Andes Padel")
    return Court.objects.create(venue=venue, name="Cancha 1", price_base="10.00")


@pytest.fixture
def paid_booking(api_client, client_user, court):
    today = timezone.localdate()
    booking = Booking.objects.create(
        user=client_user,
        court=court,
        date=today,
        start_time=timezone.datetime.strptime("10:00", "%H:%M").time(),
        end_time=timezone.datetime.strptime("11:00", "%H:%M").time(),
        duration_minutes=60,
        players=4,
        price="20.00",
        status=Booking.Status.COMPLETED,
    )
    Payment.objects.create(
        booking=booking,
        user=client_user,
        method=Payment.Method.CASH,
        amount="20.00",
        status=Payment.Status.CAPTURED,
    )
    return booking


class TestReportsAPI:
    def test_revenue_requires_manager(self, api_client, client_user, paid_booking):
        api_client.force_authenticate(client_user)
        resp = api_client.get("/api/reports/revenue/")
        assert resp.status_code == 403

    def test_revenue_json(self, authed, paid_booking):
        resp = authed.get("/api/reports/revenue/")
        assert resp.status_code == 200
        assert sum(float(r["total"]) for r in resp.data) == 20.0

    def test_revenue_csv(self, authed, paid_booking):
        resp = authed.get("/api/reports/revenue/?output=csv")
        assert resp.status_code == 200
        assert resp["Content-Type"].startswith("text/csv")
        assert "Periodo" in resp.content.decode()

    def test_occupancy(self, authed, paid_booking):
        resp = authed.get("/api/reports/occupancy/")
        assert resp.status_code == 200
        assert "pct" in resp.data

    def test_customers(self, authed, paid_booking):
        resp = authed.get("/api/reports/customers/")
        assert resp.status_code == 200
        assert resp.data[0]["email"] == "cli@test.com"

    def test_cancellations(self, authed, paid_booking):
        resp = authed.get("/api/reports/cancellations/")
        assert resp.status_code == 200
        assert "no_show" in resp.data


class TestEventsAPI:
    def test_event_feed_only_published(self, api_client, client_user):
        from apps.events.models import Event

        Event.objects.create(title="Pub", description="x", status=Event.Status.PUBLISHED)
        Event.objects.create(title="Draft", description="x", status=Event.Status.DRAFT)
        api_client.force_authenticate(client_user)
        resp = api_client.get("/api/events/")
        assert resp.status_code == 200
        titles = [e["title"] for e in resp.data["results"]]
        assert titles == ["Pub"]

    def test_staff_can_create_event(self, authed):
        resp = authed.post(
            "/api/events/",
            {"title": "Clinic", "title_es": "Clinica", "description": "abc", "status": "published"},
            format="json",
        )
        assert resp.status_code in (201, 200)
        assert resp.data["title_es"] == "Clinica"

    def test_client_cannot_create_event(self, api_client, client_user):
        api_client.force_authenticate(client_user)
        resp = api_client.post(
            "/api/events/", {"title": "X"}, format="json"
        )
        assert resp.status_code == 403


class TestTournamentsAPI:
    def test_register_flow(self, api_client, client_user):
        from apps.events.models import Tournament

        tournament = Tournament.objects.create(
            name="Torneo",
            start_date=timezone.localdate() + timezone.timedelta(days=7),
            end_date=timezone.localdate() + timezone.timedelta(days=14),
            capacity=2,
            price="25.00",
            registration_deadline=timezone.now() + timezone.timedelta(days=3),
            status=Tournament.Status.OPEN,
        )
        api_client.force_authenticate(client_user)
        resp = api_client.post(f"/api/tournaments/{tournament.id}/register/")
        assert resp.status_code == 201
        assert resp.data["status"] == "pending_payment"
        resp = api_client.post(f"/api/tournaments/{tournament.id}/register/")
        assert resp.status_code == 409

    def test_register_with_partner(self, api_client, client_user):
        from apps.events.models import Tournament

        tournament = Tournament.objects.create(
            name="Torneo",
            start_date=timezone.localdate() + timezone.timedelta(days=7),
            end_date=timezone.localdate() + timezone.timedelta(days=14),
            capacity=2,
            price="25.00",
            registration_deadline=timezone.now() + timezone.timedelta(days=3),
            status=Tournament.Status.OPEN,
        )
        api_client.force_authenticate(client_user)
        resp = api_client.post(
            f"/api/tournaments/{tournament.id}/register/",
            {"partner_name": "Lucia"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["partner_name"] == "Lucia"

    def test_full_tournament_conflict(self, api_client, client_user):
        from django.contrib.auth import get_user_model

        from apps.events.models import Tournament, TournamentRegistration

        tournament = Tournament.objects.create(
            name="Lleno",
            start_date=timezone.localdate() + timezone.timedelta(days=7),
            end_date=timezone.localdate() + timezone.timedelta(days=14),
            capacity=1,
            price="10.00",
            registration_deadline=timezone.now() + timezone.timedelta(days=3),
            status=Tournament.Status.OPEN,
        )
        other = get_user_model().objects.create_user(email="o@test.com", password="pass12345")
        TournamentRegistration.objects.create(tournament=tournament, user=other)
        api_client.force_authenticate(client_user)
        resp = api_client.post(f"/api/tournaments/{tournament.id}/register/")
        assert resp.status_code == 409

    def test_confirm_registration(self, api_client, client_user):
        from apps.events.models import Tournament

        tournament = Tournament.objects.create(
            name="Torneo",
            start_date=timezone.localdate() + timezone.timedelta(days=7),
            end_date=timezone.localdate() + timezone.timedelta(days=14),
            capacity=2,
            price="25.00",
            registration_deadline=timezone.now() + timezone.timedelta(days=3),
            status=Tournament.Status.OPEN,
        )
        api_client.force_authenticate(client_user)
        api_client.post(f"/api/tournaments/{tournament.id}/register/")
        resp = api_client.post(f"/api/tournaments/{tournament.id}/confirm/")
        assert resp.status_code == 200
        assert resp.data["status"] == "confirmed"


class TestNewsAPI:
    def test_news_feed(self, api_client, client_user):
        from apps.events.models import NewsPost

        NewsPost.objects.create(
            title="Noticia", body="Body", status=NewsPost.Status.PUBLISHED
        )
        api_client.force_authenticate(client_user)
        resp = api_client.get("/api/news/")
        assert resp.status_code == 200
        assert resp.data["results"][0]["title_localized"] == "Noticia"
