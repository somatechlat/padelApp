from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.scheduling.models import MaintenanceWindow, TimeSlot

SLOT_MINUTES = 30


class SlotService:
    @staticmethod
    def generate_day(court, day):
        """Create the 30-min slots `court` sells on `day`, reconciled to today's schedule.

        This is what makes a schedule change reach availability. It compares
        what the active ``CourtSchedule`` implies with the rows already stored
        instead of returning early when the day was generated before:

        * free rows outside the new window are deleted, so nothing outside
          opening hours can be picked up afterwards;
        * rows the new window implies are created;
        * rows that are not free (booked / held / blocked) are never touched —
          a reservation already sold survives the club changing its hours.

        Both writes are idempotent, so two concurrent requests for the same
        day converge on the same grid (``ignore_conflicts`` on the unique
        ``(court, date, start)`` constraint).
        """
        if day < timezone.localdate():
            return []
        schedules = court.schedules.filter(is_active=True, weekday=day.weekday())
        desired = []  # (start, end) pairs the schedule implies
        for schedule in schedules:
            t = schedule.open_time
            end_limit = schedule.close_time
            while True:
                end = (datetime.combine(day, t) + timedelta(minutes=SLOT_MINUTES)).time()
                if t >= end_limit or end > end_limit:
                    break
                desired.append((t, end))
                t = end

        existing = list(TimeSlot.objects.filter(court=court, date=day))
        stored = {(s.start, s.end) for s in existing}
        wanted = set(desired)
        stale_free = [
            s.id
            for s in existing
            if (s.start, s.end) not in wanted and s.status == TimeSlot.Status.AVAILABLE
        ]
        missing = [
            TimeSlot(court=court, date=day, start=start, end=end)
            for start, end in desired
            if (start, end) not in stored
        ]
        with transaction.atomic():
            if stale_free:
                TimeSlot.objects.filter(id__in=stale_free).delete()
            if missing:
                TimeSlot.objects.bulk_create(missing, ignore_conflicts=True)
        return list(TimeSlot.objects.filter(court=court, date=day).order_by("start"))

    @staticmethod
    def _is_in_maintenance(slot, windows):
        slot_start = datetime.combine(slot.date, slot.start, tzinfo=timezone.get_current_timezone())
        slot_end = datetime.combine(slot.date, slot.end, tzinfo=timezone.get_current_timezone())
        for w in windows:
            if slot_start < w.end and slot_end > w.start:
                return True
        return False

    @staticmethod
    def available_slots(court, day):
        slots = TimeSlot.objects.filter(
            court=court, date=day, status=TimeSlot.Status.AVAILABLE
        ).order_by("start")
        now = timezone.localtime()
        windows = list(
            MaintenanceWindow.objects.filter(court=court).filter(
                start__date__lte=day, end__date__gte=day
            )
        )
        result = []
        tz = timezone.get_current_timezone()
        for s in slots:
            start_dt = datetime.combine(s.date, s.start, tzinfo=tz)
            if day == now.date() and start_dt <= now:
                continue
            if SlotService._is_in_maintenance(s, windows):
                continue
            result.append(s)
        return result

    @staticmethod
    def slots_in_range(court, day, start_time, duration_minutes):
        count = duration_minutes // SLOT_MINUTES
        start_dt = datetime.combine(day, start_time)
        ids = []
        for i in range(count):
            st = (start_dt + timedelta(minutes=SLOT_MINUTES * i)).time()
            slot = TimeSlot.objects.filter(court=court, date=day, start=st).first()
            if slot:
                ids.append(slot.id)
        return list(TimeSlot.objects.filter(id__in=ids).order_by("start"))
