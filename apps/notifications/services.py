import logging
import os

from django.conf import settings
from django.core.mail import send_mail
from django.utils import translation
from django.utils.translation import gettext, gettext_noop

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
    "event_registered",
    "admin_booking_created",
    "admin_cash_booking",
    "open_match_created",
}
DEFAULT_CHANNELS = ("email", "push", "inapp")

# Message templates keyed by event type. The msgid (English) is the canonical
# string; titles/bodies are localized with ``gettext`` using the user's
# ``language_code`` and then interpolated with the event ``data`` params.
MESSAGE_TEMPLATES = {
    "booking_confirmed": (
        gettext_noop("Booking confirmed"),
        gettext_noop("Your booking for {court} on {date} at {time} is confirmed."),
    ),
    "booking_cancelled": (
        gettext_noop("Booking cancelled"),
        gettext_noop("Your booking for {court} on {date} at {time} was cancelled."),
    ),
    "booking_reminder": (
        gettext_noop("Booking reminder"),
        gettext_noop("Reminder: {court} tomorrow at {time}."),
    ),
    "booking_reminder_2h": (
        gettext_noop("Booking starting soon"),
        gettext_noop("Your booking for {court} starts in 2 hours at {time}."),
    ),
    "booking_modified": (
        gettext_noop("Booking modified"),
        gettext_noop("Your booking for {court} has been rescheduled to {date} at {time}."),
    ),
    "no_show_penalty": (
        gettext_noop("No-show penalty"),
        gettext_noop("You did not attend your booking for {court}. A penalty of {amount} has been applied."),
    ),
    "payment_success": (
        gettext_noop("Payment received"),
        gettext_noop("We received your payment of {amount}."),
    ),
    "payment_failed": (
        gettext_noop("Payment failed"),
        gettext_noop("Your payment of {amount} could not be processed. Please try again or contact support."),
    ),
    "payment_refunded": (
        gettext_noop("Payment refunded"),
        gettext_noop("A refund of {amount} was processed."),
    ),
    "transfer_confirmed": (
        gettext_noop("Transfer confirmed"),
        gettext_noop("Your bank transfer of {amount} was confirmed."),
    ),
    "transfer_rejected": (
        gettext_noop("Transfer rejected"),
        gettext_noop("Your bank transfer of {amount} was rejected. Reason: {reason}"),
    ),
    "tournament_reminder": (
        gettext_noop("Tournament reminder"),
        gettext_noop("The tournament {tournament} starts tomorrow."),
    ),
    "tournament_confirmed": (
        gettext_noop("Tournament registration confirmed"),
        gettext_noop("You are registered for {tournament}."),
    ),
    "tournament_registered": (
        gettext_noop("Tournament registration"),
        gettext_noop("Your registration for {tournament} has been received."),
    ),
    "news_published": (
        gettext_noop("New announcement"),
        gettext_noop("{title}"),
    ),
    "event_published": (
        gettext_noop("New event"),
        gettext_noop("{title}"),
    ),
    "event_registered": (
        gettext_noop("Inscripcion confirmada"),
        gettext_noop("Te apuntaste a: {title}"),
    ),
    "admin_booking_created": (
        gettext_noop("Nueva reserva"),
        gettext_noop("Nueva reserva de {user}: {court} el {date} a las {time} ({duration} min)."),
    ),
    "admin_cash_booking": (
        gettext_noop("Reserva pago en el establecimiento"),
        gettext_noop("{user} reservó {court} el {date} a las {time} y pagará en el establecimiento."),
    ),
    "open_match_created": (
        gettext_noop("Nuevo partido en tu categoría"),
        gettext_noop("{title}"),
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

    @staticmethod
    def notify_admins(event_type, data=None, title="", body=""):
        """Alert club admins by push + in-app and the alert email from settings.

        The reservation alert email is configured in Admin > Ajustes
        (`Venue.booking_alert_email`). Push goes to every active staff account
        that has a registered device when `booking_alert_push` is on.
        """
        from django.contrib.auth import get_user_model

        from apps.courts.models import Venue

        data = data or {}
        if not title and not body:
            # Localize with Spanish (club ops language) so admins always read
            # the alert in the club default.
            title, body = NotificationService._localize(
                type("U", (), {"language_code": "es"})(), event_type, data
            )

        User = get_user_model()
        admins = User.objects.filter(
            role__in=("recepcionista", "gerente", "dueno", "superadmin"),
            is_active=True,
        )
        venue = Venue.objects.first()
        push_enabled = venue.booking_alert_push if venue else True

        for admin in admins:
            Notification.objects.create(
                user=admin, event_type=event_type, title=title, body=body, data=data
            )
            if push_enabled:
                NotificationService._send_push(admin, title, body, data)

        if venue and venue.booking_alert_email:
            try:
                send_mail(
                    title,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [venue.booking_alert_email],
                    fail_silently=False,
                )
            except Exception:
                logging.getLogger(__name__).exception(
                    "Failed to send admin booking alert email to %s",
                    venue.booking_alert_email,
                )
