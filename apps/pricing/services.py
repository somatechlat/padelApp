from decimal import Decimal

from apps.pricing.models import PriceRule


class TariffService:
    @staticmethod
    def compute(court, day, duration_minutes, start_time=None):
        base = Decimal(court.price_base)
        rules = (
            PriceRule.objects.filter(
                venue=court.venue, active=True
            )
            .filter(
                models_day_or_none(day),
                models_type_or_none(court),
            )
            .order_by("-priority")
        )
        rule = rules.first()
        multiplier = Decimal(rule.multiplier) if rule else Decimal("1")
        hours = Decimal(duration_minutes) / Decimal("60")
        return (base * multiplier * hours).quantize(Decimal("0.01"))


def models_day_or_none(day):
    from django.db.models import Q

    return Q(day_of_week=day.weekday()) | Q(day_of_week__isnull=True)


def models_type_or_none(court):
    from django.db.models import Q

    return Q(court_type=court.court_type) | Q(court_type__isnull=True)
