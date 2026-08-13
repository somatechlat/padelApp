from django.conf import settings
from django.core.mail import send_mail

from apps.notifications.models import (
    DeviceToken,
    Notification,
    NotificationPreference,
)

TRANSACTIONAL_EVENTS = {
    "booking_confirmed",
    "booking_cancelled",
    "booking_reminder",
    "no_show_penalty",
    "payment_success",
    "payment_failed",
    "transfer_confirmed",
    "password_reset",
}
DEFAULT_CHANNELS = ("email", "push", "inapp")


class NotificationService:
    @staticmethod
    def channels_for(user, event_type):
        channels = set(DEFAULT_CHANNELS)
        prefs = NotificationPreference.objects.filter(user=user, event_type=event_type)
        for pref in prefs:
            if not pref.enabled:
                channels.discard(pref.channel)
        if event_type in TRANSACTIONAL_EVENTS:
            # Transactional notifications cannot be fully silenced.
            channels.add("inapp")
            channels.add("email")
        return channels

    @staticmethod
    def notify(user, event_type, title, body="", data=None):
        data = data or {}
        Notification.objects.create(
            user=user, event_type=event_type, title=title, body=body, data=data
        )
        channels = NotificationService.channels_for(user, event_type)
        if "email" in channels:
            try:
                send_mail(
                    title,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
        if "push" in channels:
            NotificationService._send_push(user, title, body, data)
        return Notification.objects.filter(user=user, event_type=event_type).latest("created_at")

    @staticmethod
    def _send_push(user, title, body, data):
        tokens = list(
            DeviceToken.objects.filter(user=user, is_active=True).values_list("token", flat=True)
        )
        if not tokens:
            return
        try:
            import firebase_admin
            from firebase_admin import messaging

            if not firebase_admin._apps:
                return
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={str(k): str(v) for k, v in (data or {}).items()},
                tokens=tokens,
            )
            messaging.send_each_for_multicast(message)
        except Exception:
            pass
