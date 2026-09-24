from datetime import time, timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.bookings.models import Booking, BookingSlot
from apps.pricing.services import TariffService
from apps.scheduling.models import BookingHold, TimeSlot
from apps.scheduling.services import SlotService

SLOT_MINUTES = 30
HOLD_MINUTES = 10
MAX_HOLDS_PER_USER = 5


class BookingService:
    @staticmethod
    def preview(court, day, start_time, duration_minutes):
        return TariffService.compute(court, day, duration_minutes)

    @staticmethod
    def hold(user, court, day, start_time, duration_minutes, players=4):
        start_time = time.fromisoformat(str(start_time)) if isinstance(start_time, str) else start_time
        now = timezone.localtime()
        start_dt = timezone.make_aware(
            timezone.datetime.combine(day, start_time), timezone.get_current_timezone()
        )
        if day < now.date() or (day == now.date() and start_dt <= now):
            raise ValueError(_("La hora ya paso"))

        with transaction.atomic():
            # Limit is per BOOKING (one checkout), never per 30-min slot row.
            # Counting slot-level holds made a single 120-min booking (4 slots)
            # trip "Limite de reservas temporales superado" immediately.
            hold_minutes, max_holds = BookingService._hold_settings()
            active_holds = (
                BookingHold.objects.filter(
                    user=user, expires_at__gt=timezone.now()
                )
                .values("slot__bookings__booking_id")
                .distinct()
                .count()
            )
            if active_holds >= max_holds:
                raise ValueError(_("Limite de reservas temporales superado"))

            SlotService.generate_day(court, day)
            slots = list(SlotService.slots_in_range(court, day, start_time, duration_minutes))
            if len(slots) < duration_minutes // SLOT_MINUTES:
                raise ValueError(_("Horario no disponible"))
            locked = list(
                TimeSlot.objects.select_for_update()
                .filter(id__in=[s.id for s in slots])
                .order_by("start")
            )
            if any(s.status != TimeSlot.Status.AVAILABLE for s in locked):
                raise ValueError(_("La cancha no esta disponible en ese horario"))

            price = TariffService.compute(court, day, duration_minutes)
            booking = Booking.objects.create(
                user=user,
                court=court,
                date=day,
                start_time=start_time,
                end_time=(timezone.datetime.combine(day, start_time) + timedelta(minutes=duration_minutes)).time(),
                duration_minutes=duration_minutes,
                players=players,
                price=price,
            )
            BookingSlot.objects.bulk_create(
                [BookingSlot(booking=booking, slot=s) for s in locked]
            )
            TimeSlot.objects.filter(id__in=[s.id for s in locked]).update(
                status=TimeSlot.Status.HELD
            )
            for slot in locked:
                BookingHold.objects.create(
                    court=court,
                    slot=slot,
                    user=user,
                    expires_at=timezone.now() + timedelta(minutes=hold_minutes),
                )
        from apps.security.services import log_event

        log_event(user, "booking.hold", "Booking", booking.id, after={"price": str(booking.price)})
        return booking

    @staticmethod
    def _hold_settings():
        """(hold_minutes, max_holds_per_user) from the active policy, with defaults."""
        from apps.policies.models import CancellationPolicy

        policy = (
            CancellationPolicy.objects.filter(active=True).order_by("-id").first()
        )
        if policy is None:
            return HOLD_MINUTES, MAX_HOLDS_PER_USER
        hold_minutes = policy.hold_minutes or HOLD_MINUTES
        max_holds = getattr(policy, "max_holds_per_user", 0) or MAX_HOLDS_PER_USER
        return hold_minutes, max_holds

    @staticmethod
    def confirm(booking):
        with transaction.atomic():
            booking_slots = list(booking.slots.select_related("slot").all())
            if any(s.slot.status != TimeSlot.Status.HELD for s in booking_slots):
                raise ValueError(_("Las franjas ya no estan disponibles"))
            slot_ids = [s.slot_id for s in booking_slots]
            TimeSlot.objects.filter(id__in=slot_ids).update(status=TimeSlot.Status.BOOKED)
            BookingHold.objects.filter(slot_id__in=slot_ids).delete()
            booking.transition_to(Booking.Status.CONFIRMED)
        from apps.security.services import log_event

        log_event(booking.user, "booking.confirm", "Booking", booking.id)
        from apps.notifications.tasks import notify_admins_task, notify_task

        notify_task.delay(
            booking.user_id,
            "booking_confirmed",
            "",
            "",
            {
                "court": booking.court.name,
                "date": str(booking.date),
                "time": str(booking.start_time),
                "booking_id": booking.id,
            },
        )
        # Admin alert: push + email on every confirmed reservation.
        notify_admins_task.delay(
            "admin_booking_created",
            {
                "user": booking.user.email,
                "court": booking.court.name,
                "date": str(booking.date),
                "time": str(booking.start_time),
                "duration": booking.duration_minutes,
                "booking_id": booking.id,
            },
        )
        return booking
        with transaction.atomic():
            slot_ids = list(booking.slots.values_list("slot_id", flat=True))
            # Free the BookingSlot rows so the slots can be booked again
            # (uniq_slot_booked_once would otherwise block a re-booking).
            booking.slots.all().delete()
            TimeSlot.objects.filter(id__in=slot_ids).update(status=TimeSlot.Status.AVAILABLE)
            BookingHold.objects.filter(slot_id__in=slot_ids).delete()
            booking.transition_to(Booking.Status.CANCELLED)
        from apps.security.services import log_event

        log_event(booking.user, "booking.cancel", "Booking", booking.id)
        from apps.notifications.tasks import notify_task

        notify_task.delay(
            booking.user_id,
            "booking_cancelled",
            "",
            "",
            {
                "court": booking.court.name,
                "date": str(booking.date),
                "time": str(booking.start_time),
                "booking_id": booking.id,
            },
        )
        return booking

    @staticmethod
    def complete(booking):
        return booking.transition_to(Booking.Status.COMPLETED)

    @staticmethod
    def mark_no_show(booking):
        booking.transition_to(Booking.Status.NO_SHOW)
        from apps.security.services import log_event
        log_event(booking.user, "booking.no_show", "Booking", booking.id)
        from apps.notifications.tasks import notify_task
        notify_task.delay(
            booking.user_id,
            "no_show_penalty",
            "",
            "",
            {
                "court": booking.court.name,
                "date": str(booking.date),
                "time": str(booking.start_time),
                "amount": f"${booking.price}",
                "booking_id": booking.id,
            },
        )
        return booking

    @staticmethod
    def reschedule(booking, new_date, new_start_time):
        from datetime import timedelta as td

        with transaction.atomic():
            old_date = str(booking.date)
            old_time = str(booking.start_time)
            slot_ids = list(booking.slots.values_list("slot_id", flat=True))
            booking.slots.all().delete()
            TimeSlot.objects.filter(id__in=slot_ids).update(status=TimeSlot.Status.AVAILABLE)
            BookingHold.objects.filter(slot_id__in=slot_ids).delete()

            SlotService.generate_day(booking.court, new_date)
            new_slots = list(
                SlotService.slots_in_range(
                    booking.court, new_date, new_start_time, booking.duration_minutes
                )
            )
            expected = booking.duration_minutes // SLOT_MINUTES
            if len(new_slots) < expected:
                raise ValueError(_("Horario no disponible para reprogramar"))

            locked = list(
                TimeSlot.objects.select_for_update()
                .filter(id__in=[s.id for s in new_slots])
                .order_by("start")
            )
            if any(s.status != TimeSlot.Status.AVAILABLE for s in locked):
                raise ValueError(_("La cancha no esta disponible en ese horario"))

            booking.date = new_date
            booking.start_time = new_start_time
            booking.end_time = (
                timezone.datetime.combine(new_date, new_start_time) + td(minutes=booking.duration_minutes)
            ).time()
            booking.save(update_fields=["date", "start_time", "end_time", "updated_at"])

            BookingSlot.objects.bulk_create(
                [BookingSlot(booking=booking, slot=s) for s in locked]
            )
            TimeSlot.objects.filter(id__in=[s.id for s in locked]).update(
                status=TimeSlot.Status.HELD
            )
            for slot in locked:
                BookingHold.objects.create(
                    court=booking.court,
                    slot=slot,
                    user=booking.user,
                    expires_at=timezone.now() + td(minutes=HOLD_MINUTES),
                )

        from apps.security.services import log_event
        log_event(booking.user, "booking.reschedule", "Booking", booking.id,
                  before={"date": old_date, "time": old_time},
                  after={"date": str(new_date), "time": str(new_start_time)})
        from apps.notifications.tasks import notify_task
        notify_task.delay(
            booking.user_id,
            "booking_modified",
            "",
            "",
            {
                "court": booking.court.name,
                "date": str(new_date),
                "time": str(new_start_time),
                "booking_id": booking.id,
            },
        )
        return booking
