from datetime import timedelta

import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="u@test.com", password="pass12345")


class TestInAppNotifications:
    def test_notify_creates_inapp_record(self, user, mailoutbox):
        from apps.notifications.services import NotificationService

        NotificationService.notify(user, "booking_confirmed", "Reserva confirmada", "Detalle")
        from apps.notifications.models import Notification

        n = Notification.objects.get(user=user)
        assert n.event_type == "booking_confirmed"
        assert n.title == "Reserva confirmada"
        assert n.read_at is None

    def test_mark_read(self, user):
        from apps.notifications.models import Notification
        from apps.notifications.services import NotificationService

        NotificationService.notify(user, "booking_confirmed", "T", "D")
        n = Notification.objects.get(user=user)
        n.mark_read()
        assert n.read_at is not None

    def test_opt_out_push_but_keep_email(self, user):
        from apps.notifications.models import NotificationPreference
        from apps.notifications.services import NotificationService

        NotificationPreference.objects.create(
            user=user, event_type="marketing", channel="push", enabled=False
        )
        result = NotificationService.channels_for(user, "marketing")
        assert "push" not in result
        assert "email" in result

    def test_marketing_opt_out_keeps_transactional(self, user):
        from apps.notifications.models import NotificationPreference
        from apps.notifications.services import NotificationService

        NotificationPreference.objects.create(
            user=user, event_type="marketing", channel="email", enabled=False
        )
        assert "email" in NotificationService.channels_for(user, "booking_confirmed")
        assert "email" not in NotificationService.channels_for(user, "marketing")


class TestDeviceTokens:
    def test_register_device_token(self, user):
        from apps.notifications.models import DeviceToken

        dt = DeviceToken.objects.create(user=user, platform="android", token="fcm-abc")
        assert dt.token == "fcm-abc"
        assert dt.is_active is True

    def test_unique_token(self, user):
        from django.db import IntegrityError

        from apps.notifications.models import DeviceToken

        DeviceToken.objects.create(user=user, platform="android", token="fcm-abc")
        with pytest.raises(IntegrityError):
            DeviceToken.objects.create(user=user, platform="ios", token="fcm-abc")


class TestTaskDispatch:
    def test_task_sends_email_when_preferred(self, user, mailoutbox):
        from apps.notifications.tasks import notify_task

        notify_task.delay(user.id, "booking_confirmed", "Titulo", "Cuerpo", {})
        from apps.notifications.models import Notification

        assert Notification.objects.filter(user=user).exists()
        assert len(mailoutbox) == 1


class TestLocalizedMessages:
    def test_spanish_by_default(self, user, mailoutbox):
        from apps.notifications.models import Notification
        from apps.notifications.services import NotificationService

        NotificationService.notify(
            user,
            "booking_confirmed",
            data={"court": "C1", "date": "2026-08-15", "time": "10:00", "booking_id": 1},
        )
        n = Notification.objects.get(user=user, event_type="booking_confirmed")
        assert n.title == "Reserva confirmada"
        assert "C1" in n.body and "2026-08-15" in n.body

    def test_english_when_language_code_en(self, user, mailoutbox):
        from apps.notifications.models import Notification
        from apps.notifications.services import NotificationService

        user.language_code = "en"
        user.save(update_fields=["language_code"])
        NotificationService.notify(
            user,
            "booking_confirmed",
            data={"court": "C1", "date": "2026-08-15", "time": "10:00", "booking_id": 1},
        )
        n = Notification.objects.get(user=user, event_type="booking_confirmed")
        assert n.title == "Booking confirmed"
        assert "is confirmed" in n.body

    def test_unknown_event_type_stores_empty_strings(self, user, mailoutbox):
        from apps.notifications.models import Notification
        from apps.notifications.services import NotificationService

        NotificationService.notify(user, "custom_event")
        n = Notification.objects.get(user=user, event_type="custom_event")
        assert n.title == ""
        assert n.body == ""

    def _make_booking(self, user, day, start):
        from apps.bookings.models import Booking
        from apps.courts.models import Court, CourtSchedule, Venue

        venue = Venue.objects.get_or_create(name="V", timezone="UTC", currency="USD")[0]
        court = Court.objects.get_or_create(venue=venue, name="C1", price_base="10.00")[0]
        CourtSchedule.objects.get_or_create(
            court=court, weekday=day.weekday(), open_time="00:00", close_time="23:59"
        )
        return Booking.objects.create(
            user=user,
            court=court,
            date=day,
            start_time=start,
            end_time="23:59",
            duration_minutes=60,
            players=4,
            price="10.00",
            status=Booking.Status.CONFIRMED,
        )

    def test_2h_reminder_still_fires_across_midnight(self, user, mailoutbox):
        """A booking 1h after midnight must be reminded at 23:30.

        The old query filtered `date=today` with `start_time__gte=now.time()`
        and `start_time__lte=in_2h.time()`. At 23:30 the cutoff is 01:30, so
        23:30 <= t <= 01:30 matched nothing and the booking was never
        mentioned — including the date rollover case.
        """
        from datetime import datetime as dt
        from unittest import mock

        from django.utils import timezone
        from django.utils.timezone import make_aware

        from apps.notifications.models import Notification
        from apps.notifications.tasks import send_booking_reminders_2h

        tz = timezone.get_current_timezone()
        frozen_now = make_aware(dt(2026, 10, 28, 23, 30), tz)
        target_day = frozen_now.date() + timedelta(days=1)  # 2026-10-29
        self._make_booking(user, target_day, "01:00")

        with mock.patch(
            "apps.notifications.tasks.timezone.localtime", return_value=frozen_now
        ):
            sent = send_booking_reminders_2h()

        assert sent == 1, (
            "2h reminder missed a booking 75 minutes out across midnight"
        )
        assert Notification.objects.filter(
            user=user, event_type="booking_reminder_2h"
        ).exists()

    def test_2h_reminder_same_day_window_still_matches(self, user, mailoutbox):
        from datetime import datetime as dt
        from unittest import mock

        from django.utils import timezone
        from django.utils.timezone import make_aware

        from apps.notifications.tasks import send_booking_reminders_2h

        tz = timezone.get_current_timezone()
        frozen_now = make_aware(dt(2026, 10, 28, 10, 0), tz)
        self._make_booking(user, frozen_now.date(), "11:00")  # 1h out

        with mock.patch(
            "apps.notifications.tasks.timezone.localtime", return_value=frozen_now
        ):
            sent = send_booking_reminders_2h()

        assert sent == 1

    def test_2h_reminder_ignores_a_booking_outside_the_window(self, user, mailoutbox):
        from datetime import datetime as dt
        from unittest import mock

        from django.utils import timezone
        from django.utils.timezone import make_aware

        from apps.notifications.tasks import send_booking_reminders_2h

        tz = timezone.get_current_timezone()
        frozen_now = make_aware(dt(2026, 10, 28, 10, 0), tz)
        self._make_booking(user, frozen_now.date(), "18:00")  # 8h out

        with mock.patch(
            "apps.notifications.tasks.timezone.localtime", return_value=frozen_now
        ):
            sent = send_booking_reminders_2h()

        assert sent == 0

    def test_reminder_task_counts_confirmed_bookings(self, user, mailoutbox):
        from django.utils import timezone

        from apps.bookings.models import Booking
        from apps.courts.models import Court, CourtSchedule, Venue
        from apps.notifications.tasks import send_booking_reminders

        venue = Venue.objects.create(name="V", timezone="UTC", currency="USD")
        court = Court.objects.create(venue=venue, name="C1", price_base="10.00")
        CourtSchedule.objects.create(court=court, weekday=0, open_time="08:00", close_time="22:00")
        Booking.objects.create(
            user=user,
            court=court,
            date=timezone.localdate() + timedelta(days=1),
            start_time="10:00",
            end_time="11:00",
            duration_minutes=60,
            players=4,
            price="10.00",
            status=Booking.Status.CONFIRMED,
        )
        sent = send_booking_reminders()
        assert sent == 1
        from apps.notifications.models import Notification

        n = Notification.objects.get(user=user, event_type="booking_reminder")
        assert "C1" in n.body
