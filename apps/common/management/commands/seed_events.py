"""Seed Andes Padel events, tournaments and open matches (quedadas).

This is content seeding for a live club calendar — not demo/test fixtures. It
is idempotent (get_or_create on the natural key) so re-running it does not
duplicate rows, and it is safe to run in production.

Dates are scheduled relative to "now" so the mobile app always shows upcoming
events rather than a calendar stuck in the past.
"""

from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.events.models import Event, OpenMatch, Tournament
from apps.users.models import User

EVENTS = [
    {
        "key": "clinica-verano",
        "title": "Summer Clinic",
        "title_es": "Clínica de Verano",
        "description": "Guided training for all levels with certified coaches.",
        "description_es": "Entrenamiento guiado para todos los niveles con instructores certificados.",
        "days": 3,
        "start": time(18, 0),
        "hours": 2,
        "location": "Cancha C1",
        "category": Event.Category.ACADEMIA,
    },
    {
        "key": "quedada-viernes",
        "title": "Friday Social Match",
        "title_es": "Quedada de los Viernes",
        "description": "Open play by level. Meet players and join the community.",
        "description_es": "Quedada por niveles. Conoce jugadores y forma parte de la comunidad.",
        "days": 5,
        "start": time(19, 0),
        "hours": 2,
        "location": "Cancha C2",
        "category": Event.Category.QUEDADA,
    },
    {
        "key": "torneo-abierto",
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
        "key": "liga-interna",
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
        "key": "abierto-mixto",
        "name": "Mixed Open",
        "name_es": "Abierto Mixto",
        "description": "Mixed doubles, all levels welcome.",
        "description_es": "Dobles mixto, todos los niveles.",
        "start_days": 14,
        "duration_days": 2,
        "capacity": 16,
        "price": "40.00",
    },
    {
        "key": "copa-andes",
        "name": "Andes Cup",
        "name_es": "Copa Andes",
        "description": "Our flagship club tournament.",
        "description_es": "Nuestro torneo insignia del club.",
        "start_days": 28,
        "duration_days": 3,
        "capacity": 24,
        "price": "60.00",
    },
]

OPEN_MATCHES = [
    {"days": 2, "start": time(18, 0), "notes": "Nivel intermedio. Faltan 2.", "notes_alt": "Intermediate level. 2 spots left."},
    {"days": 4, "start": time(19, 30), "notes": "Nivel avanzado. Solo 1 lugar.", "notes_alt": "Advanced level. 1 spot left."},
    {"days": 6, "start": time(10, 0), "notes": "Principiantes bienvenidos.", "notes_alt": "Beginners welcome."},
]


class Command(BaseCommand):
    help = "Seed club events, tournaments and open matches (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        author = (
            User.objects.filter(role__in=["superadmin", "dueno", "gerente"]).order_by("id").first()
            or User.objects.order_by("id").first()
        )
        if author is None:
            self.stderr.write("No user exists yet — create an admin first.")
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
                f"{'created' if created else 'exists '} event  {obj.title_es}  ({start:%a %d %b %H:%M})"
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
                f"{'created' if created else 'exists '} tourney {obj.name_es}  ({start_d:%d %b})"
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

        self.stdout.write(self.style.SUCCESS("Event calendar seeded."))
