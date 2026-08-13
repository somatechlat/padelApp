from dataclasses import dataclass
from decimal import Decimal

from django.utils import timezone

from apps.bookings.models import Booking
from apps.policies.models import CancellationPolicy


@dataclass
class PenaltyResult:
    ratio: Decimal
    amount: Decimal


class PolicyService:
    @staticmethod
    def get_policy(booking):
        return (
            CancellationPolicy.objects.filter(venue=booking.court.venue, active=True)
            .first()
        )

    @staticmethod
    def evaluate(booking, now=None):
        now = now or timezone.now()
        policy = PolicyService.get_policy(booking)
        if policy is None:
            return PenaltyResult(Decimal("0"), Decimal("0"))
        if now > booking.start_at:
            ratio = policy.no_show_ratio
        elif (booking.start_at - now).total_seconds() / 3600 >= policy.free_window_hours:
            ratio = Decimal("0")
        else:
            ratio = policy.penalty_ratio
        amount = (booking.price * ratio).quantize(Decimal("0.01"))
        return PenaltyResult(ratio=ratio, amount=amount)

    @staticmethod
    def mark_no_show(booking):
        # Server time is authoritative (SRS: never trust the client clock).
        booking.transition_to(Booking.Status.NO_SHOW)
        return booking
