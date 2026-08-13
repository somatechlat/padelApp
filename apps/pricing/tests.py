import pytest
from decimal import Decimal
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

        day = timezone.localdate() + timezone.timedelta(days=1)
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

        day = timezone.localdate() + timezone.timedelta(days=1)
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
        day = timezone.localdate() + timezone.timedelta(days=1)
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
            venue=court.venue, name="Low prio", zone="valle",
            day_of_week=None, court_type=None, multiplier="1.10", priority=1,
        )
        PriceRule.objects.create(
            venue=court.venue, name="High prio", zone="valle",
            day_of_week=None, court_type=None, multiplier="1.90", priority=99,
        )
        day = timezone.localdate() + timezone.timedelta(days=1)
        assert TariffService.compute(court, day, 60) == Decimal("22.80")  # 12 x 1.90


def _next_weekday(target: int):
    day = timezone.localdate() + timezone.timedelta(days=1)
    while day.weekday() != target:
        day += timezone.timedelta(days=1)
    return day
