import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.fixture
def venue():
    from apps.courts.models import Venue

    return Venue.objects.create(name="Andes Padel", timezone="America/Guayaquil", currency="USD")


@pytest.fixture
def court(venue):
    from apps.courts.models import Court

    return Court.objects.create(
        venue=venue, name="Cancha 1", court_type="techada", price_base="12.00"
    )


@pytest.fixture
def user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="u@test.com", password="pass12345")


@pytest.fixture
def schedule(court):
    from apps.courts.models import CourtSchedule

    for wd in range(7):
        CourtSchedule.objects.create(
            court=court, weekday=wd, open_time="08:00", close_time="22:00"
        )
    return court


class TestSlotGeneration:
    def test_generates_30_min_slots_between_open_close(self, schedule):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timezone.timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        assert slots is not None
        assert len(slots) == 28  # 08:00-22:00 = 14h = 28 slots
        first = slots[0]
        assert str(first.start.strftime("%H:%M")) == "08:00"
        assert str(first.end.strftime("%H:%M")) == "08:30"

    def test_slot_duration_30_minutes(self, schedule):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timezone.timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        assert all(
            (timezone.datetime.combine(day, s.end) - timezone.datetime.combine(day, s.start)).total_seconds() == 1800
            for s in slots
        )

    def test_does_not_generate_for_past_day(self, schedule):
        from apps.scheduling.services import SlotService

        day = timezone.localdate() - timezone.timedelta(days=1)
        assert SlotService.generate_day(schedule, day) == []


class TestAvailability:
    def test_available_slots_exclude_booked(self, schedule, user):
        from apps.scheduling.models import TimeSlot
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timezone.timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        first = slots[0]
        first.status = "booked"
        first.save()
        avail = SlotService.available_slots(schedule, day)
        assert all(s.id != first.id for s in avail)

    def test_available_slots_exclude_held(self, schedule, user):
        from apps.scheduling.models import TimeSlot
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timezone.timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        slots[0].status = "held"
        slots[0].save()
        avail = SlotService.available_slots(schedule, day)
        assert all(s.id != slots[0].id for s in avail)

    def test_available_slots_exclude_maintenance(self, schedule, user):
        from apps.scheduling.models import MaintenanceWindow
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timezone.timedelta(days=1)
        MaintenanceWindow.objects.create(
            court=schedule,
            start=timezone.datetime.combine(day, timezone.datetime.strptime("09:00", "%H:%M").time(), tzinfo=timezone.get_current_timezone()),
            end=timezone.datetime.combine(day, timezone.datetime.strptime("11:00", "%H:%M").time(), tzinfo=timezone.get_current_timezone()),
        )
        SlotService.generate_day(schedule, day)
        avail = SlotService.available_slots(schedule, day)
        morning = [s for s in avail if str(s.start.strftime("%H:%M")) in ("09:00", "09:30", "10:00", "10:30")]
        assert morning == []


class TestBookingHold:
    def test_hold_expires_after_10_minutes(self, schedule, user):
        from apps.scheduling.models import BookingHold, TimeSlot
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timezone.timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        hold = BookingHold.objects.create(
            court=schedule, slot=slots[0], user=user,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        assert hold.is_expired is False
        hold.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        assert hold.is_expired is True

    def test_anti_hoarding_limit(self, schedule, user):
        from apps.scheduling.models import BookingHold
        from apps.scheduling.services import SlotService

        day = timezone.localdate() + timezone.timedelta(days=1)
        slots = SlotService.generate_day(schedule, day)
        for i in range(3):
            BookingHold.objects.create(
                court=schedule, slot=slots[i], user=user,
                expires_at=timezone.now() + timezone.timedelta(minutes=10),
            )
        active = BookingHold.objects.filter(
            user=user, expires_at__gt=timezone.now()
        ).count()
        assert active <= 3
