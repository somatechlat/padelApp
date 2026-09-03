import logging
import os

from django.conf import settings
from django.core.mail import send_mail
from django.utils import translation
from django.utils.translation import gettext

from apps.notifications.models import (
    DeviceToken,
    Notification,
    NotificationPreference,
)

TRANSACTIONAL_EVENTS = {
    "booking_confirmed",
    "booking_cancelled",
    "booking_reminder",
    "booking_modified",
    "no_show_penalty",
    "payment_success",
    "payment_failed",
    "payment_refunded",
    "transfer_confirmed",
    "transfer_rejected",
    "password_reset",
    "tournament_reminder",
    "tournament_confirmed",
    "tournament_registered",
    "news_published",
    "event_published",
}
DEFAULT_CHANNELS = ("email", "push", "inapp")

# Message templates keyed by event type. The msgid (English) is the canonical
# string; titles/bodies are localized with ``gettext`` using the user's
# ``language_code`` and then interpolated with the event ``data`` params.
MESSAGE_TEMPLATES = {
    "booking_confirmed": (
        "Booking confirmed",
        "Your booking for {court} on {date} at {time} is confirmed.",
    ),
    "booking_cancelled": (
        "Booking cancelled",
        "Your booking for {court} on {date} at {time} was cancelled.",
    ),
    "booking_reminder": (
        "Booking reminder",
        "Reminder: {court} tomorrow at {time}.",
    ),
    "booking_reminder_2h": (
        "Booking starting soon",
        "Your booking for {court} starts in 2 hours at {time}.",
    ),
    "booking_modified": (
        "Booking modified",
        "Your booking for {court} has been rescheduled to {date} at {time}.",
    ),
    "no_show_penalty": (
        "No-show penalty",
        "You did not attend your booking for {court}. A penalty of {amount} has been applied.",
    ),
    "payment_success": (
        "Payment received",
        "We received your payment of {amount}.",
    ),
    "payment_failed": (
        "Payment failed",
        "Your payment of {amount} could not be processed. Please try again or contact support.",
    ),
    "payment_refunded": (
        "Payment refunded",
        "A refund of {amount} was processed.",
    ),
    "transfer_confirmed": (
        "Transfer confirmed",
        "Your bank transfer of {amount} was confirmed.",
    ),
    "transfer_rejected": (
        "Transfer rejected",
        "Your bank transfer of {amount} was rejected. Reason: {reason}",
    ),
    "tournament_reminder": (
        "Tournament reminder",
        "The tournament {tournament} starts tomorrow.",
    ),
    "tournament_confirmed": (
        "Tournament registration confirmed",
        "You are registered for {tournament}.",
    ),
    "tournament_registered": (
        "Tournament registration",
        "Your registration for {tournament} has been received.",
    ),
    "news_published": (
        "New announcement",
        "{title}",
    ),
    "event_published": (
        "New event",
        "{title}",
    ),
}


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
    def _localize(user, event_type, data):
        template = MESSAGE_TEMPLATES.get(event_type)
        if not template:
            return "", ""
        lang = getattr(user, "language_code", None) or "es"
        with translation.override(lang):
            title = gettext(template[0])
            body = gettext(template[1])
            try:
                body = body.format(**data)
            except (KeyError, IndexError) as e:
                logging.getLogger(__name__).warning(
                    "Notification template format error for %s: %s", event_type, e
                )
        return title, body

    @staticmethod
    def notify(user, event_type, title="", body="", data=None):
        data = data or {}
        if not title and not body:
            title, body = NotificationService._localize(user, event_type, data)
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
                    fail_silently=False,
                )
            except Exception:
                logging.getLogger(__name__).exception(
                    "Failed to send email notification to %s for event %s",
                    user.email, event_type,
                )
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
            from firebase_admin import credentials, messaging

            if not firebase_admin._apps:
                path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", "")
                if not path or not os.path.exists(path):
                    return
                firebase_admin.initialize_app(credentials.Certificate(path))
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={str(k): str(v) for k, v in (data or {}).items()},
                tokens=tokens,
            )
            messaging.send_each_for_multicast(message)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to send push notification to user %s", user.id,
            )
