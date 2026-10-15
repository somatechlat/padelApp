from datetime import time as dtime
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError

from apps.courts.models import PromoBanner, Venue, resolve_i18n

pytestmark = pytest.mark.django_db


@pytest.fixture
def venue():

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

    def test_venue_club_fields_default_blank(self, venue):
        assert venue.phone == ""
        assert venue.email == ""
        assert venue.whatsapp_number == ""
        assert venue.instagram_url == ""
        assert venue.bank_name == ""
        assert venue.home_section_title_i18n == {}
        assert venue.home_greeting_tagline_i18n == {}

    def test_home_section_title_for_lang_and_fallback(self, venue):
        venue.home_section_title_i18n = {
            "es": "Reserva tu cancha",
            "en": "Book your court",
            "pt": "Reserve sua quadra",
            "ca": "Reserva la teva pista",
        }
        venue.save()
        assert venue.home_section_title_for("es") == "Reserva tu cancha"
        assert venue.home_section_title_for("en") == "Book your court"
        assert venue.home_section_title_for("pt") == "Reserve sua quadra"
        assert venue.home_section_title_for("ca") == "Reserva la teva pista"

    def test_home_section_title_fallback_to_es(self, venue):
        venue.home_section_title_i18n = {"es": "Solo español"}
        venue.save()
        assert venue.home_section_title_for("en") == "Solo español"
        assert venue.home_section_title_for("fr") == "Solo español"
        assert venue.home_section_title_for() == "Solo español"

    def test_home_greeting_tagline_for_lang(self, venue):
        venue.home_greeting_tagline_i18n = {
            "es": "Reserva tu cancha de pádel",
            "en": "Book your padel court",
        }
        venue.save()
        assert venue.home_greeting_tagline_for("en") == "Book your padel court"
        assert venue.home_greeting_tagline_for("ca") == "Reserva tu cancha de pádel"

    def test_resolve_i18n_falls_back_to_first_value(self):
        assert resolve_i18n({"pt": "Olá"}, "de", fallback_lang="es") == "Olá"
        assert resolve_i18n({}, "es") == ""
        assert resolve_i18n("plain", "es") == "plain"

    def test_resolve_i18n_strips_region(self):
        data = {"es": "Hola", "en": "Hello"}
        assert resolve_i18n(data, "en-US") == "Hello"
        assert resolve_i18n(data, "ES-MX") == "Hola"


class TestPromoBanner:
    def test_title_subtitle_fallback(self):
        banner = PromoBanner(
            title_i18n={"es": "Torneo de Verano", "en": "Summer Tournament"},
            subtitle_i18n={"es": "Inscripciones abiertas"},
        )
        assert banner.title_for("es") == "Torneo de Verano"
        assert banner.title_for("en") == "Summer Tournament"
        assert banner.title_for("ca") == "Torneo de Verano"
        assert banner.subtitle_for("en") == "Inscripciones abiertas"
        assert banner.subtitle_for("es") == "Inscripciones abiertas"

    def test_is_visible_now_respects_active_and_window(self):
        from django.utils import timezone

        now = timezone.now()
        banner = PromoBanner(
            title_i18n={"es": "x"},
            active=True,
            starts_at=now - timedelta(days=1),
            ends_at=now + timedelta(days=1),
        )
        assert banner.is_visible_now() is True
        banner.active = False
        assert banner.is_visible_now() is False
        banner.active = True
        banner.starts_at = now + timedelta(days=2)
        assert banner.is_visible_now() is False
        banner.starts_at = None
        banner.ends_at = now - timedelta(hours=1)
        assert banner.is_visible_now() is False

    def test_banner_str_uses_title(self):
        banner = PromoBanner(title_i18n={"es": "Banner X"})
        assert str(banner) == "Banner X"


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


class TestClubHoursAreASetting:
    """The club day lives on the Venue and every schedule is validated to it.

    Nothing about 06:00/22:00 may be baked into a model: these tests change
    the hours and expect the rules to move with them.
    """

    def test_shipped_default_is_0600_to_2200(self, venue):
        from apps.courts.models import club_hours

        assert venue.hours_label == "06:00 – 22:00"
        assert club_hours() == (venue.daily_open, venue.daily_close)
        assert f"{venue.daily_open:%H:%M}" == "06:00"
        assert f"{venue.daily_close:%H:%M}" == "22:00"

    def test_hours_are_changeable(self, venue):
        from apps.courts.models import club_hours

        venue.daily_open = dtime(7, 0)
        venue.daily_close = dtime(23, 0)
        venue.save()
        venue.refresh_from_db()
        assert club_hours() == (dtime(7, 0), dtime(23, 0))
        assert venue.hours_label == "07:00 – 23:00"

    def test_schedule_must_stay_inside_the_club_hours(self, court, venue):
        from apps.courts.models import CourtSchedule

        venue.daily_close = dtime(21, 0)
        venue.save()

        with pytest.raises(ValidationError) as exc:
            CourtSchedule(court=court, weekday=0, open_time="06:00", close_time="22:00").save()
        assert "21:00" in str(exc.value)  # the message quotes the live setting

        CourtSchedule(court=court, weekday=0, open_time="06:00", close_time="21:00").save()
        assert CourtSchedule.objects.filter(court=court).count() == 1

    def test_widening_the_club_hours_unlocks_the_new_range(self, court, venue):
        from apps.courts.models import CourtSchedule

        venue.daily_open = dtime(5, 0)
        venue.save()
        CourtSchedule(court=court, weekday=0, open_time="05:00", close_time="22:00").save()
        assert CourtSchedule.objects.filter(court=court).count() == 1

    def test_closing_before_opening_is_rejected(self, court):
        from apps.courts.models import CourtSchedule

        with pytest.raises(ValidationError):
            CourtSchedule(court=court, weekday=0, open_time="22:00", close_time="06:00").save()

    def test_hours_off_the_half_hour_are_rejected(self, court):
        """Every court must share one 30-min grid, or bookings can overlap."""
        from apps.courts.models import CourtSchedule

        with pytest.raises(ValidationError):
            CourtSchedule(court=court, weekday=0, open_time="06:15", close_time="22:00").save()
