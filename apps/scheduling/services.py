from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.scheduling.models import MaintenanceWindow, TimeSlot

SLOT_MINUTES = 30


class SlotService:
    @staticmethod
    def generate_day(court, day):
        if day < timezone.localdate():
            return []
        if TimeSlot.objects.filter(court=court, date=day).exists():
            return list(TimeSlot.objects.filter(court=court, date=day).order_by("start"))
        schedules = court.schedules.filter(is_active=True, weekday=day.weekday())
        if not schedules.exists():
            return []
        slots = []
        for schedule in schedules:
            t = schedule.open_time
            end_limit = schedule.close_time
            while True:
                end = (timezone.datetime.combine(day, t) + timedelta(minutes=SLOT_MINUTES)).time()
                if t >= end_limit or end > end_limit:
                    break
                slots.append(TimeSlot(court=court, date=day, start=t, end=end))
                t = end
        with transaction.atomic():
            created = TimeSlot.objects.bulk_create(slots, ignore_conflicts=True)
        created_ids = [s.id for s in created]
        existing = TimeSlot.objects.filter(court=court, date=day).order_by("start")
        if created_ids:
            existing = existing.exclude(id__in=created_ids)
        return list(existing.order_by("start"))

    @staticmethod
    def _is_in_maintenance(slot, windows):
        slot_start = timezone.datetime.combine(slot.date, slot.start, tzinfo=timezone.get_current_timezone())
        slot_end = timezone.datetime.combine(slot.date, slot.end, tzinfo=timezone.get_current_timezone())
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
            MaintenanceWindow.objects.filter(court=court)
            .filter(start__date__lte=day, end__date__gte=day)
        )
        result = []
        tz = timezone.get_current_timezone()
        for s in slots:
            start_dt = timezone.datetime.combine(s.date, s.start, tzinfo=tz)
            if day == now.date() and start_dt <= now:
                continue
            if SlotService._is_in_maintenance(s, windows):
                continue
            result.append(s)
        return result

    @staticmethod
    def block(court, day, start_time, duration_minutes, status=TimeSlot.Status.BLOCKED):
        slots = SlotService.slots_in_range(court, day, start_time, duration_minutes)
        TimeSlot.objects.filter(id__in=[s.id for s in slots]).update(status=status)
        return slots

    @staticmethod
    def slots_in_range(court, day, start_time, duration_minutes):
        count = duration_minutes // SLOT_MINUTES
        start_dt = timezone.datetime.combine(day, start_time)
        ids = []
        for i in range(count):
            st = (start_dt + timedelta(minutes=SLOT_MINUTES * i)).time()
            slot = TimeSlot.objects.filter(court=court, date=day, start=st).first()
            if slot:
                ids.append(slot.id)
        return list(TimeSlot.objects.filter(id__in=ids).order_by("start"))
