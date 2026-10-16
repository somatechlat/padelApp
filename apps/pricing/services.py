from decimal import Decimal

from apps.pricing.models import PriceRule


class TariffService:
    """Reads every number it uses out of the database. Nothing is invented here."""

    @staticmethod
    def compute(court, day, duration_minutes, start_time=None):
        rules = (
            PriceRule.objects.filter(venue=court.venue, active=True)
            .filter(
                models_day_matches(day),
                models_type_or_none(court),
                models_time_matches(start_time),
            )
            .order_by("-priority")
        )
        rule = rules.first()
        if rule is None:
            hourly = Decimal(court.price_base)
        elif rule.price is not None:
            hourly = Decimal(rule.price)
        elif rule.multiplier is not None:
            hourly = Decimal(court.price_base) * Decimal(rule.multiplier)
        else:
            hourly = Decimal(court.price_base)
        hours = Decimal(duration_minutes) / Decimal("60")
        return (hourly * hours).quantize(Decimal("0.01"))


def models_day_matches(day):
    from django.db.models import Q

    weekday = day.weekday()
    scopes = (
        [PriceRule.Scope.ALL.value, PriceRule.Scope.WEEKEND.value]
        if weekday >= 5
        else [PriceRule.Scope.ALL.value, PriceRule.Scope.WEEKDAYS.value]
    )
    # An explicit day beats the weekday/weekend scope, which only applies to rules
    # that leave day_of_week empty.
    return Q(day_of_week=weekday) | (Q(day_of_week__isnull=True, scope__in=scopes))


def models_time_matches(start_time):
    from django.db.models import Q

    # Rules with no window apply at any hour; rules with a window apply only when the
    # booking starts inside it. The caller passes the booking's start time.
    if start_time is None:
        return Q(start_time__isnull=True, end_time__isnull=True)
    return Q(start_time__isnull=True, end_time__isnull=True) | Q(
        start_time__lte=start_time,
        end_time__gt=start_time,
    )


def models_type_or_none(court):
    from django.db.models import Q

    return Q(court_type=court.court_type) | Q(court_type__isnull=True)
