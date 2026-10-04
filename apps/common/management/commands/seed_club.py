"""Seed the club's base data: skill levels, staff/demo accounts, venue.

This is the counterpart to ``seed_calendar``. It writes the reference data the
mobile app needs before anything else can load — the registration form reads
``/api/auth/skill-levels/`` and will render an empty picker without them.

Idempotent: ``get_or_create`` on each natural key, and passwords are only set
when the account is created so re-running never clobbers a rotated password.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.courts.models import Venue
from apps.users.models import SkillLevel, User

# Club-standard password for seeded demo/staff accounts. Documented in the
# user manual; change it before any real customer data exists.
SEED_PASSWORD = "Andes12345!"

SKILL_LEVELS = [
    ("Principiante", 0),
    ("Intermedio", 1),
    ("Avanzado", 2),
    ("Profesional", 3),
]

ACCOUNTS = [
    ("admin@andespadel.com", "Admin", "Andes Padel", "superadmin"),
    ("gerente@andespadel.com", "Gerente", "Andes Padel", "gerente"),
    ("recepcion@andespadel.com", "Recepcion", "Andes Padel", "recepcionista"),
    ("cliente@andespadel.com", "Cliente", "Andes Padel", "cliente"),
    ("jugador@andespadel.com", "Jugador", "Andes Padel", "cliente"),
    ("cannachaincosta@gmail.com", "Canna", "Chain", "cliente"),
]

VENUE = {
    "name": "Andes Padel Club",
    "address": "Rodríguez Labandera y Ernesto Albán, Quito",
    "timezone": "America/Guayaquil",
    "currency": "USD",
    "phone": "+593 99 267 6842",
    "email": "reservas@andespadelclub.com",
    "whatsapp_number": "+593992676842",
    "whatsapp_message": "Hola, quiero reservar una cancha",
    "instagram_url": "https://instagram.com/andespadelec",
    "maps_query": "Rodriguez Labandera y Ernesto Alban, Quito, Ecuador",
    "booking_alert_email": "reservas@andespadelclub.com",
    "booking_alert_push": True,
    "bank_name": "Banco Pichincha",
    "bank_account_number": "2200123456",
    "bank_account_holder": "Andes Padel Club",
    "bank_account_code": "CCI",
    "bank_extra": "Enviar comprobante por WhatsApp al 099 267 6842",
}


class Command(BaseCommand):
    help = "Seed skill levels, staff/demo accounts and the club venue (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        created_levels = 0
        for name, order in SKILL_LEVELS:
            _, created = SkillLevel.objects.get_or_create(
                name=name, defaults={"order": order, "is_active": True}
            )
            if created:
                created_levels += 1
        self.stdout.write(
            f"skill levels: {SkillLevel.objects.count()} total ({created_levels} new)"
        )

        created_users = 0
        for email, first, last, role in ACCOUNTS:
            user, created = User.objects.get_or_create(
                email=email.lower(),
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "full_name": f"{first} {last}".strip(),
                    "role": role,
                    "is_active": True,
                    "email_verified": True,
                    "language_code": "es",
                },
            )
            if created:
                user.set_password(SEED_PASSWORD)
                user.email_verified = True
                user.is_active = True
                user.save()
                created_users += 1
            self.stdout.write(f"{'created' if created else 'exists '} {role:14s} {email}")
        self.stdout.write(f"accounts: {User.objects.count()} total ({created_users} new)")

        defaults = {k: v for k, v in VENUE.items() if k != "name"}
        venue, created = Venue.objects.get_or_create(name=VENUE["name"], defaults=defaults)
        if not created:
            changed = []
            for field, value in defaults.items():
                if not getattr(venue, field):
                    setattr(venue, field, value)
                    changed.append(field)
            if changed:
                venue.save(update_fields=changed)
                self.stdout.write(f"venue updated fields: {', '.join(changed)}")
        self.stdout.write(f"{'created' if created else 'exists '} venue  {venue.name}")

        self.stdout.write(self.style.SUCCESS("Club base data seeded."))
