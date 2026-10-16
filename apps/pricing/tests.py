from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
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
def pico_weekend_rule(venue):
    from apps.pricing.models import PriceRule

    return PriceRule.objects.create(
        venue=venue,
        name="Pico fin de semana",
        zone="pico",
        day_of_week=6,
        court_type="techada",
        multiplier="1.50",
        priority=10,
    )


class TestTariffService:
    def test_default_price_when_no_rules(self, court):
        from apps.pricing.services import TariffService

        day = timezone.localdate() + timedelta(days=1)
        price = TariffService.compute(court, day, 60)
        assert price == Decimal("12.00")

    def test_pico_weekend_multiplier_applies(self, court, pico_weekend_rule):
        from apps.pricing.services import TariffService

        saturday = _next_weekday(6)
        price = TariffService.compute(court, saturday, 60)
        assert price == Decimal("18.00")  # 12 x 1.50

    def test_weekday_not_affected_by_weekend_rule(self, court, pico_weekend_rule):
        from apps.pricing.services import TariffService

        monday = _next_weekday(0)
        price = TariffService.compute(court, monday, 60)
        assert price == Decimal("12.00")

    def test_duration_scales_price(self, court):
        from apps.pricing.services import TariffService

        day = timezone.localdate() + timedelta(days=1)
        assert TariffService.compute(court, day, 90) == Decimal("18.00")
        assert TariffService.compute(court, day, 120) == Decimal("24.00")

    def test_valle_rule_discount(self, court):
        from apps.pricing.models import PriceRule
        from apps.pricing.services import TariffService

        PriceRule.objects.create(
            venue=court.venue,
            name="Valle manana",
            zone="valle",
            day_of_week=None,
            court_type=None,
            multiplier="0.80",
            priority=5,
        )
        day = timezone.localdate() + timedelta(days=1)
        assert TariffService.compute(court, day, 60) == Decimal("9.60")

    def test_inactive_rule_ignored(self, court, pico_weekend_rule):
        from apps.pricing.services import TariffService

        pico_weekend_rule.active = False
        pico_weekend_rule.save()
        saturday = _next_weekday(6)
        assert TariffService.compute(court, saturday, 60) == Decimal("12.00")

    def test_highest_priority_rule_wins(self, court):
        from apps.pricing.models import PriceRule
        from apps.pricing.services import TariffService

        PriceRule.objects.create(
            venue=court.venue,
            name="Low prio",
            zone="valle",
            day_of_week=None,
            court_type=None,
            multiplier="1.10",
            priority=1,
        )
        PriceRule.objects.create(
            venue=court.venue,
            name="High prio",
            zone="valle",
            day_of_week=None,
            court_type=None,
            multiplier="1.90",
            priority=99,
        )
        day = timezone.localdate() + timedelta(days=1)
        assert TariffService.compute(court, day, 60) == Decimal("22.80")  # 12 x 1.90


class TestTimeBands:
    """A band is a day + a window + one price, all of it read from the rule row."""

    @pytest.fixture
    def morning_band(self, venue):
        from apps.pricing.models import PriceRule

        return PriceRule.objects.create(
            venue=venue,
            name="Franja mañana",
            zone="valle",
            scope="weekdays",
            start_time=time(6, 0),
            end_time=time(9, 0),
            price="24.00",
            priority=20,
        )

    def test_absolute_price_inside_the_window(self, court, morning_band):
        from apps.pricing.services import TariffService

        monday = _next_weekday(0)
        assert TariffService.compute(court, monday, 60, time(7, 0)) == Decimal("24.00")

    def test_window_is_exclusive_of_start_only(self, court, morning_band):
        from apps.pricing.services import TariffService

        monday = _next_weekday(0)
        # 06:00 is inside (start inclusive), 09:00 is not (end exclusive).
        assert TariffService.compute(court, monday, 60, time(6, 0)) == Decimal("24.00")
        assert TariffService.compute(court, monday, 60, time(9, 0)) == Decimal("12.00")

    def test_band_does_not_apply_outside_its_window(self, court, morning_band):
        from apps.pricing.services import TariffService

        monday = _next_weekday(0)
        assert TariffService.compute(court, monday, 60, time(10, 0)) == Decimal("12.00")
        assert TariffService.compute(court, monday, 60, time(5, 30)) == Decimal("12.00")

    def test_band_without_start_time_does_not_apply_at_any_hour(self, court, morning_band):
        """`preview` may be called without a start time; a windowed rule must not leak."""
        from apps.pricing.services import TariffService

        monday = _next_weekday(0)
        assert TariffService.compute(court, monday, 60) == Decimal("12.00")

    def test_weekday_scope_excludes_the_weekend(self, court, morning_band):
        from apps.pricing.services import TariffService

        saturday = _next_weekday(5)
        assert TariffService.compute(court, saturday, 60, time(7, 0)) == Decimal("12.00")

    def test_weekend_scope_covers_both_days(self, court):
        from apps.pricing.models import PriceRule
        from apps.pricing.services import TariffService

        PriceRule.objects.create(
            venue=court.venue,
            name="Fin de semana",
            zone="pico",
            scope="weekend",
            price="40.00",
            priority=30,
        )
        for target in (5, 6):
            day = _next_weekday(target)
            assert TariffService.compute(court, day, 60, time(20, 0)) == Decimal("40.00")
        assert TariffService.compute(court, _next_weekday(0), 60, time(20, 0)) == Decimal("12.00")

    def test_absolute_price_scales_with_duration(self, court, morning_band):
        from apps.pricing.services import TariffService

        monday = _next_weekday(0)
        assert TariffService.compute(court, monday, 90, time(7, 0)) == Decimal("36.00")
        assert TariffService.compute(court, monday, 30, time(7, 0)) == Decimal("12.00")

    def test_a_rule_with_no_window_matches_at_any_hour(self, court):
        from apps.pricing.models import PriceRule
        from apps.pricing.services import TariffService

        PriceRule.objects.create(
            venue=court.venue,
            name="Todo el día",
            zone="valle",
            multiplier="2.00",
            priority=5,
        )
        monday = _next_weekday(0)
        assert TariffService.compute(court, monday, 60, time(23, 0)) == Decimal("24.00")

    def test_explicit_day_beats_the_scope(self, court):
        from apps.pricing.models import PriceRule
        from apps.pricing.services import TariffService

        PriceRule.objects.create(
            venue=court.venue,
            name="Sábado puntual",
            zone="pico",
            day_of_week=5,
            scope="weekdays",  # ignored: day_of_week wins
            price="50.00",
            priority=40,
        )
        saturday = _next_weekday(5)
        assert TariffService.compute(court, saturday, 60, time(9, 0)) == Decimal("50.00")
        assert TariffService.compute(court, _next_weekday(6), 60, time(9, 0)) == Decimal("12.00")

    def test_highest_priority_wins_between_two_bands(self, court):
        from apps.pricing.models import PriceRule
        from apps.pricing.services import TariffService

        PriceRule.objects.create(
            venue=court.venue,
            name="Banda ancha",
            zone="valle",
            start_time=time(6, 0),
            end_time=time(23, 0),
            price="15.00",
            priority=10,
        )
        PriceRule.objects.create(
            venue=court.venue,
            name="Banda estrecha",
            zone="pico",
            start_time=time(18, 0),
            end_time=time(23, 0),
            price="30.00",
            priority=20,
        )
        monday = _next_weekday(0)
        assert TariffService.compute(court, monday, 60, time(19, 0)) == Decimal("30.00")
        assert TariffService.compute(court, monday, 60, time(12, 0)) == Decimal("15.00")

    def test_band_accepts_a_time_string(self, court, morning_band):
        """The booking service passes 'HH:MM' strings as often as time objects."""
        from apps.pricing.services import TariffService

        monday = _next_weekday(0)
        assert TariffService.compute(court, monday, 60, "07:00") == Decimal("24.00")
        assert TariffService.compute(court, monday, 60, "10:00") == Decimal("12.00")

    def test_booking_preview_passes_the_start_time(self, court, morning_band):
        from apps.bookings.services import BookingService

        monday = _next_weekday(0)
        assert BookingService.preview(court, monday, time(7, 0), 60) == Decimal("24.00")
        assert BookingService.preview(court, monday, time(10, 0), 60) == Decimal("12.00")


class TestPriceRuleValidation:
    def _rule(self, venue, **kwargs):
        from apps.pricing.models import PriceRule

        defaults = {"venue": venue, "name": "Regla"}
        defaults.update(kwargs)
        return PriceRule(**defaults)

    def test_price_and_multiplier_cannot_both_be_set(self, venue):
        with pytest.raises(ValidationError):
            self._rule(venue, price="24.00", multiplier="1.50").full_clean()

    def test_price_or_multiplier_is_required(self, venue):
        with pytest.raises(ValidationError):
            self._rule(venue).full_clean()

    def test_price_alone_is_valid(self, venue):
        self._rule(venue, price="24.00").full_clean()

    def test_multiplier_alone_is_valid(self, venue):
        self._rule(venue, multiplier="1.50").full_clean()

    def test_half_a_time_window_is_rejected(self, venue):
        with pytest.raises(ValidationError):
            self._rule(venue, price="24.00", start_time=time(6, 0)).full_clean()

    def test_end_before_start_is_rejected(self, venue):
        with pytest.raises(ValidationError):
            self._rule(
                venue, price="24.00", start_time=time(18, 0), end_time=time(6, 0)
            ).full_clean()

    def test_a_valid_band_cleans(self, venue):
        self._rule(
            venue, price="24.00", scope="weekdays", start_time=time(6, 0), end_time=time(9, 0)
        ).full_clean()

    def test_display_helpers_substitute_no_amount(self, venue):
        by_price = self._rule(venue, price="24.00")
        by_price.full_clean()
        assert by_price.price_display == "24.00"
        assert by_price.multiplier_display == ""
        by_mult = self._rule(venue, multiplier="1.500")
        by_mult.full_clean()
        assert by_mult.price_display == ""
        assert by_mult.multiplier_display == "x1.500"

    def test_day_scope_display_prefers_an_explicit_day(self, venue):
        from apps.pricing.models import PriceRule

        assert self._rule(venue, price="1.00").day_scope_display == PriceRule.Scope.ALL.label
        assert self._rule(venue, price="1.00", day_of_week=5).day_scope_display == "Sábado"
        assert (
            self._rule(venue, price="1.00", scope="weekend").day_scope_display
            == PriceRule.Scope.WEEKEND.label
        )


def _next_weekday(target: int):
    day = timezone.localdate() + timedelta(days=1)
    while day.weekday() != target:
        day += timedelta(days=1)
    return day
