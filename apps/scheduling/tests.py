from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestSlotGeneration:
    def test_generates_30_min_slots_between_open_close(self, schedule):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        assert slots is not None
        assert len(slots) == 28  # 08:00-22:00 = 14h = 28 slots
        first = slots[0]
        assert str(first.start.strftime("%H:%M")) == "08:00"
        assert str(first.end.strftime("%H:%M")) == "08:30"

    def test_slot_duration_30_minutes(self, schedule):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        end_dt = lambda s: datetime.combine(day, s.end)  # noqa: E731
        start_dt = lambda s: datetime.combine(day, s.start)  # noqa: E731
        durations = [(end_dt(s) - start_dt(s)).total_seconds() for s in slots]
        assert durations and all(d == 1800 for d in durations)

    def test_does_not_generate_for_past_day(self, schedule):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() - timedelta(days=1)
        assert SlotService.generate_day(schedule, day) == []


class TestAvailability:
    def test_available_slots_exclude_booked(self, schedule, user):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        first = slots[0]
        first.status = "booked"
        first.save()
        avail = SlotService.available_slots(schedule, day)
        assert all(s.id != first.id for s in avail)

    def test_available_slots_exclude_held(self, schedule, user):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        slots[0].status = "held"
        slots[0].save()
        avail = SlotService.available_slots(schedule, day)
        assert all(s.id != slots[0].id for s in avail)

    def test_available_slots_exclude_maintenance(self, schedule, user):
        from apps.scheduling.models import MaintenanceWindow
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        tz = timezone.get_current_timezone()
        start = datetime.combine(day, datetime.strptime("09:00", "%H:%M").time(), tzinfo=tz)
        end = datetime.combine(day, datetime.strptime("11:00", "%H:%M").time(), tzinfo=tz)
        MaintenanceWindow.objects.create(court=schedule, start=start, end=end)
        SlotService.generate_day(schedule, day)
        avail = SlotService.available_slots(schedule, day)
        blocked = ("09:00", "09:30", "10:00", "10:30")
        morning = [s for s in avail if str(s.start.strftime("%H:%M")) in blocked]
        assert morning == []


class TestBookingHold:
    def test_hold_expires_after_10_minutes(self, schedule, user):
        from apps.scheduling.models import BookingHold
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        hold = BookingHold.objects.create(
            court=schedule,
            slot=slots[0],
            user=user,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        assert hold.is_expired is False
        hold.expires_at = timezone.now() - timedelta(seconds=1)
        assert hold.is_expired is True

    def test_anti_hoarding_limit(self, schedule, user):
        from apps.scheduling.models import BookingHold
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        for i in range(3):
            BookingHold.objects.create(
                court=schedule,
                slot=slots[i],
                user=user,
                expires_at=timezone.now() + timedelta(minutes=10),
            )
        active = BookingHold.objects.filter(user=user, expires_at__gt=timezone.now()).count()
        assert active <= 3


class TestScheduleChangeReachesAvailability:
    """Changing the hours must change availability, even for a day already generated.

    ``generate_day`` used to return whatever rows it found on the first call,
    so the admin could move the schedule and the app kept selling the old
    grid until the row was deleted by hand. Reservations that were already
    sold must survive the change.
    """

    @staticmethod
    def _set_hours(court, open_str, close_str):
        from apps.courts.models import CourtSchedule

        for row in CourtSchedule.objects.filter(court=court):
            row.open_time = open_str
            row.close_time = close_str
            row.save()

    def test_opening_later_shrinks_a_day_already_generated(self, schedule):
        from apps.scheduling.models import TimeSlot
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        SlotService.generate_day(schedule, day)
        assert TimeSlot.objects.filter(court=schedule, date=day).count() == 28  # 08:00–22:00

        self._set_hours(schedule, "10:00", "22:00")
        slots = SlotService.generate_day(schedule, day)

        assert len(slots) == 24  # 10:00–22:00
        assert slots[0].start.strftime("%H:%M") == "10:00"
        stale = TimeSlot.objects.filter(court=schedule, date=day, start__lt=time(10, 0))
        assert not stale.exists(), "free rows before the new opening time were left on sale"

    def test_opening_earlier_grows_a_day_already_generated(self, schedule):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        SlotService.generate_day(schedule, day)  # 28 rows at 08:00

        self._set_hours(schedule, "06:00", "22:00")
        slots = SlotService.generate_day(schedule, day)

        assert len(slots) == 32  # 06:00–22:00
        assert slots[0].start.strftime("%H:%M") == "06:00"

    def test_a_slot_already_sold_survives_the_change(self, schedule):
        from apps.scheduling.models import TimeSlot
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        sold = SlotService.generate_day(schedule, day)[0]  # 08:00
        sold.status = TimeSlot.Status.BOOKED
        sold.save()

        self._set_hours(schedule, "10:00", "22:00")
        SlotService.generate_day(schedule, day)

        sold.refresh_from_db()
        assert sold.status == TimeSlot.Status.BOOKED, "an existing reservation was dropped"
        still_free_early = TimeSlot.objects.filter(
            court=schedule,
            date=day,
            status=TimeSlot.Status.AVAILABLE,
            start__lt=time(10, 0),
        )
        assert not still_free_early.exists()

    def test_regenerating_the_same_day_does_not_duplicate(self, schedule):
        from apps.scheduling.models import TimeSlot
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timedelta(days=1)
        SlotService.generate_day(schedule, day)
        first = TimeSlot.objects.filter(court=schedule, date=day).count()
        SlotService.generate_day(schedule, day)

        assert TimeSlot.objects.filter(court=schedule, date=day).count() == first
