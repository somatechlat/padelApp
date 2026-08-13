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
            date=timezone.localdate() + timezone.timedelta(days=1),
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
