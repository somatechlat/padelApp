from django.core.management.base import BaseCommand

from apps.common.seed_helpers import seed_club_profile, seed_promo_banners
from apps.courts.models import Court, CourtSchedule, club_hours


class Command(BaseCommand):
    help = "Seed venues, courts and their schedules idempotently."

    def handle(self, *args, **options):
        venue = seed_club_profile()
        seed_promo_banners()
        open_at, close_at = club_hours()
        created_courts = 0
        for name, court_type, price in (
            ("Cancha Ambacar", Court.CourtType.TECHADA, "12.00"),
            ("Cancha 2", Court.CourtType.ABIERTA, "10.00"),
            ("Cancha 3", Court.CourtType.ABIERTA, "10.00"),
        ):
            court, created = Court.objects.get_or_create(
                venue=venue,
                name=name,
                defaults={"court_type": court_type, "price_base": price},
            )
            if created:
                created_courts += 1
            # Synced every run: the seed reproduces the hours the club
            # configured (Venue.daily_open/daily_close), never its own copy.
            for weekday in range(7):
                CourtSchedule.objects.update_or_create(
                    court=court,
                    weekday=weekday,
                    defaults={"open_time": open_at, "close_time": close_at, "is_active": True},
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded venue (club profile + banners), {created_courts} courts, "
                f"schedules {open_at:%H:%M}-{close_at:%H:%M} for all courts."
            )
        )
