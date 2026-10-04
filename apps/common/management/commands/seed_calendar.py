"""Seed a fully bookable club calendar: schedules, time slots and events.

The mobile app filters courts through ``GET /api/courts/<id>/availability/``,
which only returns rows from ``TimeSlot``. Those rows are produced from
``CourtSchedule`` by ``SlotService.generate_day``. A club with courts but no
schedules therefore renders as "No hay canchas disponibles en este momento"
even though the courts exist — which is exactly what was happening.

This command is idempotent and safe to re-run. It:

1. ensures a venue and the club's courts exist,
2. writes an active ``CourtSchedule`` for every weekday on every active court,
3. generates ``TimeSlot`` rows for the next N days through ``SlotService``
   (the same code path production booking uses, so the data cannot drift),
4. seeds upcoming events, tournaments and open matches (quedadas).

Dates are relative to "now" so the calendar never falls into the past.
"""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.courts.models import Court, CourtSchedule, Venue
from apps.events.models import Event, OpenMatch, Tournament
from apps.scheduling.services import SlotService
from apps.users.models import User

OPEN_TIME = time(8, 0)
CLOSE_TIME = time(22, 0)

COURTS = [
    {
        "name": "Cancha 1",
        "court_type": Court.CourtType.TECHADA,
        "has_lighting": True,
        "description": (
            "Cancha techada con piso de cristal premium. Iluminacion LED "
            "profesional y paredes panoramicas. Ideal para partidos "
            "competitivos y entrenamientos."
        ),
    },
    {
        "name": "Cancha 2",
        "court_type": Court.CourtType.ABIERTA,
        "has_lighting": True,
        "description": (
            "Cancha abierta con vista a la ciudad. Piso de cesped sintetico "
            "de ultima generacion, iluminacion nocturna y graderias cubiertas."
        ),
    },
    {
        "name": "Cancha 3",
        "court_type": Court.CourtType.ABIERTA,
        "has_lighting": True,
        "description": (
            "Cancha abierta con iluminacion LED de alta potencia. Cercada y "
            "con zona de descanso. Excelente para jugar de noche."
        ),
    },
    {
        "name": "Cancha 4",
        "court_type": Court.CourtType.TECHADA,
        "has_lighting": True,
        "description": (
            "Cancha techada para juego en cualquier clima. Confort termico, "
            "piso de cristal y torre de iluminacion profesional."
        ),
    },
]

EVENTS = [
    {
        "title": "Summer Clinic",
        "title_es": "Clínica de Verano",
        "description": "Guided training for all levels with certified coaches.",
        "description_es": "Entrenamiento guiado para todos los niveles con instructores certificados.",
        "days": 3,
        "start": time(18, 0),
        "hours": 2,
        "location": "Cancha 1",
        "category": Event.Category.ACADEMIA,
    },
    {
        "title": "Friday Social Match",
        "title_es": "Quedada de los Viernes",
        "description": "Open play by level. Meet players and join the community.",
        "description_es": "Quedada por niveles. Conoce jugadores y forma parte de la comunidad.",
        "days": 5,
        "start": time(19, 0),
        "hours": 2,
        "location": "Cancha 2",
        "category": Event.Category.QUEDADA,
    },
    {
        "title": "Saturday Social Match",
        "title_es": "Quedada del Sábado",
        "description": "Weekend open play. All levels welcome.",
        "description_es": "Quedada de fin de semana. Todos los niveles bienvenidos.",
        "days": 6,
        "start": time(10, 0),
        "hours": 2,
        "location": "Cancha 3",
        "category": Event.Category.QUEDADA,
    },
    {
        "title": "Open Tournament 2026",
        "title_es": "Torneo Abierto 2026",
        "description": "Registration open for all categories.",
        "description_es": "Inscripciones abiertas para todas las categorías.",
        "days": 12,
        "start": time(9, 0),
        "hours": 8,
        "location": "Andes Padel Club",
        "category": Event.Category.TORNEO,
    },
    {
        "title": "Internal League — Season 2026",
        "title_es": "Liga Interna — Temporada 2026",
        "description": "Compete in our internal league by category. Rankings and prizes.",
        "description_es": "Compite en nuestra liga interna por categorías. Rankings y premios.",
        "days": 19,
        "start": time(18, 30),
        "hours": 3,
        "location": "Andes Padel Club",
        "category": Event.Category.LIGA,
    },
]

TOURNAMENTS = [
    {
        "name": "Mixed Open",
        "name_es": "Abierto Mixto",
        "description": "Mixed doubles, all levels welcome.",
        "description_es": "Dobles mixto, todos los niveles.",
        "start_days": 14,
        "duration_days": 2,
        "capacity": 16,
        "price": Decimal("40.00"),
    },
    {
        "name": "Andes Cup",
        "name_es": "Copa Andes",
        "description": "Our flagship club tournament.",
        "description_es": "Nuestro torneo insignia del club.",
        "start_days": 28,
        "duration_days": 3,
        "capacity": 24,
        "price": Decimal("60.00"),
    },
]

OPEN_MATCHES = [
    {"days": 2, "start": time(18, 0), "notes": "Nivel intermedio. Faltan 2 jugadores."},
    {"days": 4, "start": time(19, 30), "notes": "Nivel avanzado. Queda 1 lugar."},
    {"days": 6, "start": time(10, 0), "notes": "Principiantes bienvenidos."},
    {"days": 8, "start": time(17, 0), "notes": "Quedada abierta. 4 lugares."},
]

SLOT_DAYS = 21


class Command(BaseCommand):
    help = "Seed a fully bookable calendar: court schedules, time slots, events."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=SLOT_DAYS,
            help=f"Days of time slots to generate (default {SLOT_DAYS}).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        today = timezone.localdate()
        days = max(1, int(options["days"]))

        venue = Venue.objects.filter(active=True).order_by("id").first()
        if venue is None:
            venue = Venue.objects.create(
                name="Andes Padel Club",
                address="Rodríguez Labandera y Ernesto Albán, Quito",
                timezone="America/Guayaquil",
                currency="USD",
            )
            self.stdout.write(f"created venue  {venue.name}")
        else:
            self.stdout.write(f"exists  venue  {venue.name}")

        for spec in COURTS:
            court, created = Court.objects.get_or_create(
                venue=venue,
                name=spec["name"],
                defaults={
                    "court_type": spec["court_type"],
                    "has_lighting": spec["has_lighting"],
                    "price_base": Decimal("10.00"),
                    "description": spec["description"],
                    "status": Court.Status.ACTIVE,
                },
            )
            self.stdout.write(f"{'created' if created else 'exists '} court  {court.name}")

            for weekday in range(7):
                schedule, s_created = CourtSchedule.objects.get_or_create(
                    court=court,
                    weekday=weekday,
                    defaults={
                        "open_time": OPEN_TIME,
                        "close_time": CLOSE_TIME,
                        "is_active": True,
                    },
                )
                if not s_created and not schedule.is_active:
                    schedule.is_active = True
                    schedule.save(update_fields=["is_active"])
            self.stdout.write(
                f"         schedules 7/7 weekdays {OPEN_TIME:%H:%M}-{CLOSE_TIME:%H:%M}"
            )

        # Generate slots through SlotService so seeded data is byte-identical
        # to what the booking flow reads at runtime.
        slot_total = 0
        for court in Court.objects.filter(status=Court.Status.ACTIVE):
            for offset in range(days):
                day = today + timedelta(days=offset)
                before = court.slots.count()
                SlotService.generate_day(court, day)
                after = court.slots.count()
                slot_total += max(0, after - before)
        self.stdout.write(
            self.style.SUCCESS(f"generated {slot_total} new time slots across {days} days")
        )

        author = (
            User.objects.filter(role__in=["superadmin", "dueno", "gerente"]).order_by("id").first()
            or User.objects.order_by("id").first()
        )
        if author is None:
            self.stderr.write("No user exists yet — skipping events.")
            return

        for spec in EVENTS:
            start = timezone.make_aware(
                datetime.combine((now + timedelta(days=spec["days"])).date(), spec["start"])
            )
            end = start + timedelta(hours=spec["hours"])
            obj, created = Event.objects.get_or_create(
                title_es=spec["title_es"],
                defaults={
                    "title": spec["title"],
                    "description": spec["description"],
                    "description_es": spec["description_es"],
                    "start_at": start,
                    "end_at": end,
                    "location": spec["location"],
                    "category": spec["category"],
                    "status": Event.Status.PUBLISHED,
                    "capacity": 32,
                    "allow_registration": True,
                    "created_by": author,
                },
            )
            self.stdout.write(
                f"{'created' if created else 'exists '} event  {obj.title_es} ({start:%a %d %b %H:%M})"
            )

        for spec in TOURNAMENTS:
            start_d = (now + timedelta(days=spec["start_days"])).date()
            end_d = start_d + timedelta(days=spec["duration_days"])
            deadline = timezone.make_aware(
                datetime.combine(start_d - timedelta(days=2), time(23, 59))
            )
            obj, created = Tournament.objects.get_or_create(
                name_es=spec["name_es"],
                defaults={
                    "name": spec["name"],
                    "description": spec["description"],
                    "description_es": spec["description_es"],
                    "start_date": start_d,
                    "end_date": end_d,
                    "capacity": spec["capacity"],
                    "price": spec["price"],
                    "registration_deadline": deadline,
                    "status": Tournament.Status.OPEN,
                    "created_by": author,
                },
            )
            self.stdout.write(
                f"{'created' if created else 'exists '} tourney {obj.name_es} ({start_d:%d %b})"
            )

        skill = getattr(author, "skill_level", None)
        for spec in OPEN_MATCHES:
            day = (now + timedelta(days=spec["days"])).date()
            obj, created = OpenMatch.objects.get_or_create(
                created_by=author,
                date=day,
                start_time=spec["start"],
                defaults={
                    "duration_minutes": 90,
                    "max_players": 4,
                    "notes": spec["notes"],
                    "status": OpenMatch.Status.OPEN,
                    "skill_level": skill,
                },
            )
            self.stdout.write(
                f"{'created' if created else 'exists '} quedada {day:%a %d %b} {spec['start']:%H:%M}"
            )

        self.stdout.write(self.style.SUCCESS("Club calendar seeded."))
