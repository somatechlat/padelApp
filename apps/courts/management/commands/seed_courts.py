from django.core.management.base import BaseCommand

from apps.courts.models import Court, CourtSchedule, Venue


class Command(BaseCommand):
    help = "Seed venues, courts and their schedules idempotently."

    def handle(self, *args, **options):
        venue, _ = Venue.objects.get_or_create(
            name="Andes Padel",
            defaults={"address": "Av. Principal, Quito", "timezone": "America/Guayaquil"},
        )
        created_courts = 0
        for name, court_type, price in (
            ("C1", Court.CourtType.TECHADA, "12.00"),
            ("C2", Court.CourtType.ABIERTA, "10.00"),
        ):
            court, created = Court.objects.get_or_create(
                venue=venue,
                name=name,
                defaults={"court_type": court_type, "price_base": price},
            )
            if created:
                created_courts += 1
            if court.schedules.filter(is_active=True).count() == 0:
                for weekday in range(7):
                    CourtSchedule.objects.update_or_create(
                        court=court,
                        weekday=weekday,
                        defaults={"open_time": "08:00", "close_time": "22:00", "is_active": True},
                    )
        self.stdout.write(
            self.style.SUCCESS(f"Seeded venue, {created_courts} courts, schedules for all courts.")
        )
