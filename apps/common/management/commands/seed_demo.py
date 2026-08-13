from datetime import time as dtime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import Booking
from apps.bookings.services import BookingService
from apps.courts.models import Court, CourtSchedule, Venue
from apps.events.models import Event, NewsPost, Tournament
from apps.notifications.models import Notification

DEMO_PASSWORD = "Andes12345!"


class Command(BaseCommand):
    help = "Seed an idempotent demo dataset: users, courts, events, tournaments, news, sample bookings."

    def handle(self, *args, **options):
        User = get_user_model()
        created = {"users": 0, "courts": 0, "bookings": 0}

        def get_or_create_user(email, role, full_name, **extra):
            user, was_created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "role": role,
                    "language_code": "es",
                    "email_verified": True,
                    "status": "active",
                    **extra,
                },
            )
            if was_created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                created["users"] += 1
            return user

        admin = get_or_create_user(
            "admin@andespadel.com", "superadmin", "Administrador Andes Padel", is_staff=True, is_superuser=True
        )
        get_or_create_user("gerente@andespadel.com", "gerente", "Gerente Demo")
        get_or_create_user("recepcion@andespadel.com", "recepcionista", "Recepcion Demo")
        cliente = get_or_create_user("cliente@andespadel.com", "cliente", "Cliente Demo")
        get_or_create_user("jugador@andespadel.com", "cliente", "Jugadora Demo")

        venue, _ = Venue.objects.get_or_create(
            name="Andes Padel",
            defaults={"address": "Av. Principal, Quito", "timezone": "America/Guayaquil"},
        )
        for name, court_type, price in (
            ("C1", Court.CourtType.TECHADA, "12.00"),
            ("C2", Court.CourtType.ABIERTA, "10.00"),
        ):
            court, was_created = Court.objects.get_or_create(
                venue=venue,
                name=name,
                defaults={"court_type": court_type, "price_base": price},
            )
            if was_created:
                created["courts"] += 1
            if court.schedules.filter(is_active=True).count() == 0:
                for weekday in range(7):
                    CourtSchedule.objects.update_or_create(
                        court=court,
                        weekday=weekday,
                        defaults={"open_time": "08:00", "close_time": "22:00", "is_active": True},
                    )

        now = timezone.now()
        today = timezone.localdate()
        Event.objects.get_or_create(
            title="Clinica de verano",
            defaults={
                "title_es": "Clínica de verano",
                "description_es": "Entrenamiento guiado para todos los niveles.",
                "start_at": now + timezone.timedelta(days=5),
                "end_at": now + timezone.timedelta(days=5, hours=2),
                "location": "Cancha C1",
                "status": Event.Status.PUBLISHED,
                "created_by": admin,
            },
        )
        Event.objects.get_or_create(
            title="Torneo social mensual",
            defaults={
                "title_es": "Torneo social mensual",
                "description_es": "Dia de partidos informales entre socios.",
                "start_at": now + timezone.timedelta(days=12),
                "end_at": now + timezone.timedelta(days=12, hours=4),
                "location": "Complejo Andes Padel",
                "status": Event.Status.PUBLISHED,
                "created_by": admin,
            },
        )

        Tournament.objects.get_or_create(
            name="Torneo Nocturno",
            defaults={
                "name_es": "Torneo Nocturno",
                "description_es": "Torneo de parejas por la noche. Premios para los finalistas.",
                "start_date": today + timezone.timedelta(days=7),
                "end_date": today + timezone.timedelta(days=14),
                "capacity": 8,
                "price": "15.00",
                "registration_deadline": now + timezone.timedelta(days=5),
                "status": Tournament.Status.OPEN,
                "created_by": admin,
            },
        )
        Tournament.objects.get_or_create(
            name="Torneo del Sabado",
            defaults={
                "name_es": "Torneo del Sábado",
                "description_es": "Torneo express de un dia.",
                "start_date": today + timezone.timedelta(days=30),
                "end_date": today + timezone.timedelta(days=31),
                "capacity": 16,
                "price": "0.00",
                "registration_deadline": now + timezone.timedelta(days=28),
                "status": Tournament.Status.OPEN,
                "created_by": admin,
            },
        )
        Tournament.objects.get_or_create(
            name="Liga interna",
            defaults={
                "name_es": "Liga interna",
                "description_es": "Liga interna de otono en curso.",
                "start_date": today - timezone.timedelta(days=10),
                "end_date": today + timezone.timedelta(days=50),
                "capacity": 32,
                "price": "0.00",
                "registration_deadline": now - timezone.timedelta(days=1),
                "status": Tournament.Status.IN_PROGRESS,
                "created_by": admin,
            },
        )

        NewsPost.objects.get_or_create(
            title="Reapertura de canchas",
            defaults={
                "title_es": "Reapertura de canchas",
                "body_es": "Las canchas renovadas ya estan disponibles para reserva.",
                "status": NewsPost.Status.PUBLISHED,
                "published_at": now - timezone.timedelta(days=2),
                "created_by": admin,
            },
        )
        NewsPost.objects.get_or_create(
            title="Nuevo horario de verano",
            defaults={
                "title_es": "Nuevo horario de verano",
                "body_es": "A partir del lunes abrimos una hora antes.",
                "status": NewsPost.Status.PUBLISHED,
                "published_at": now - timezone.timedelta(days=1),
                "created_by": admin,
            },
        )

        Notification.objects.filter(user=cliente).delete()
        court = Court.objects.first()
        for day_offset, start in ((1, dtime(18, 0)), (3, dtime(20, 0)), (5, dtime(17, 0))):
            day = today + timezone.timedelta(days=day_offset)
            if Booking.objects.filter(court=court, date=day, start_time=start).exists():
                continue
            try:
                booking = BookingService.hold(
                    cliente, court, day, start, 60, players=4
                )
                BookingService.confirm(booking)
                created["bookings"] += 1
            except Exception:
                pass

        self.stdout.write(
            self.style.SUCCESS(
                "Seed demo: "
                f"users={created['users']} courts={created['courts']} bookings={created['bookings']}. "
                "Password for all demo users: Andes12345!"
            )
        )
