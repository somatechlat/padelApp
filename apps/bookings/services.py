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
MAX_HOLDS_PER_USER = 3


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
                    expires_at=timezone.now() + timedelta(minutes=HOLD_MINUTES),
                )
            active_holds = BookingHold.objects.filter(
                user=user, expires_at__gt=timezone.now()
            ).count()
            if active_holds > MAX_HOLDS_PER_USER:
                raise ValueError(_("Limite de reservas temporales superado"))
        from apps.security.services import log_event

        log_event(user, "booking.hold", "Booking", booking.id, after={"price": str(booking.price)})
        return booking

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
        from apps.notifications.tasks import notify_task

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
        return booking

    @staticmethod
    def cancel(booking):
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
        return booking.transition_to(Booking.Status.NO_SHOW)
