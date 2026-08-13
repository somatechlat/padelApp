import pytest

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


class TestVenue:
    def test_venue_defaults(self, venue):
        assert venue.active is True
        assert venue.timezone == "America/Guayaquil"
        assert venue.currency == "USD"


class TestCourt:
    def test_create_court(self, court):
        assert court.name == "Cancha 1"
        assert court.status == "active"

    def test_archive_court(self, court):
        court.status = "archived"
        court.save()
        assert court.status == "archived"

    def test_unique_name_per_venue(self, venue):
        from django.db import IntegrityError

        from apps.courts.models import Court

        Court.objects.create(venue=venue, name="Cancha X", price_base="12.00")
        with pytest.raises(IntegrityError):
            Court.objects.create(venue=venue, name="Cancha X", price_base="12.00")

    def test_court_str(self, court):
        assert str(court) == "Cancha 1"


class TestCourtSchedule:
    def test_schedule_daily(self, court):
        from apps.courts.models import CourtSchedule

        schedule = CourtSchedule.objects.create(
            court=court, weekday=0, open_time="08:00", close_time="22:00"
        )
        schedule.refresh_from_db()
        assert schedule.is_active is True
        assert schedule.open_time.strftime("%H:%M") == "08:00"
        assert schedule.close_time.strftime("%H:%M") == "22:00"

    def test_weekday_in_range(self, court):
        from apps.courts.models import CourtSchedule

        for wd in range(7):
            CourtSchedule.objects.create(
                court=court, weekday=wd, open_time="08:00", close_time="22:00"
            )
        assert CourtSchedule.objects.filter(court=court).count() == 7
