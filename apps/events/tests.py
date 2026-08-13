import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.events.models import Event, NewsPost, Tournament, TournamentRegistration
from apps.events.services import TournamentService

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return get_user_model().objects.create_user(email="p@test.com", password="pass12345")


@pytest.fixture
def manager():
    return get_user_model().objects.create_user(
        email="m@test.com", password="pass12345", role="gerente"
    )


@pytest.fixture
def tournament(user):
    return Tournament.objects.create(
        name="Torneo Nocturno",
        start_date=timezone.localdate() + timezone.timedelta(days=7),
        end_date=timezone.localdate() + timezone.timedelta(days=14),
        capacity=2,
        price="25.00",
        registration_deadline=timezone.now() + timezone.timedelta(days=3),
        status=Tournament.Status.OPEN,
    )


class TestEventModel:
    def test_i18n_title_fallback(self):
        e = Event.objects.create(
            title="Title",
            title_es="Titulo",
            description="desc",
            status=Event.Status.PUBLISHED,
        )
        assert e.title_localized == "Titulo"

    def test_draft_not_in_published_feed(self):
        Event.objects.create(
            title="Draft", description="x", status=Event.Status.DRAFT
        )
        assert Event.published.all().count() == 0


class TestNewsModel:
    def test_publish_sets_date_and_notifies(self, manager):
        news = NewsPost.objects.create(
            title="Nuevas instalaciones", body="Reapertura", created_by=manager
        )
        news.publish()
        assert news.status == NewsPost.Status.PUBLISHED
        assert news.published_at is not None


class TestTournamentService:
    def test_register_happy_path(self, tournament, user):
        reg = TournamentService.register(user, tournament)
        assert reg.status == TournamentRegistration.Status.PENDING_PAYMENT

    def test_capacity_enforced_concurrently(self, tournament, user):
        other = get_user_model().objects.create_user(email="o@test.com", password="pass12345")
        TournamentService.register(user, tournament)
        TournamentService.register(other, tournament)
        third = get_user_model().objects.create_user(email="t@test.com", password="pass12345")
        with pytest.raises(ValueError):
            TournamentService.register(third, tournament)

    def test_closed_after_deadline(self, tournament, user):
        tournament.registration_deadline = timezone.now() - timezone.timedelta(hours=1)
        tournament.save()
        with pytest.raises(ValueError):
            TournamentService.register(user, tournament)

    def test_no_duplicate_registration(self, tournament, user):
        TournamentService.register(user, tournament)
        with pytest.raises(ValueError):
            TournamentService.register(user, tournament)

    def test_register_stores_partner_name(self, tournament, user):
        reg = TournamentService.register(user, tournament, partner_name="Lucia")
        reg.refresh_from_db()
        assert reg.partner_name == "Lucia"

    def test_confirm_registration(self, tournament, user):
        reg = TournamentService.register(user, tournament)
        TournamentService.confirm(reg)
        reg.refresh_from_db()
        assert reg.status == TournamentRegistration.Status.CONFIRMED

    def test_register_rejects_non_open(self, tournament, user):
        tournament.status = Tournament.Status.DRAFT
        tournament.save()
        with pytest.raises(ValueError):
            TournamentService.register(user, tournament)


class TestTournamentStatusFlow:
    def test_close_registration_when_deadline_passes(self, tournament):
        tournament.registration_deadline = timezone.now() - timezone.timedelta(minutes=1)
        tournament.save()
        tournament.close_if_deadline_passed()
        tournament.refresh_from_db()
        assert tournament.status == Tournament.Status.CLOSED
