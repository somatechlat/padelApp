from django.db import transaction
from django.utils import timezone

from apps.gdpr.models import ConsentRecord
from apps.security.services import log_event


def record_consent(user, version, granted, source="app"):
    record = ConsentRecord.objects.create(
        user=user, version=version, granted=granted, source=source
    )
    user.consent_version = version
    user.consent_ts = timezone.now()
    user.save(update_fields=["consent_version", "consent_ts"])
    return record


def export_user_data(user):
    from apps.bookings.models import Booking
    from apps.notifications.models import Notification
    from apps.payments.models import Payment
    from apps.security.models import AuditLog

    profile = {
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "language_code": user.language_code,
        "role": user.role,
        "created_at": user.date_joined.isoformat() if user.date_joined else None,
        "consent_version": user.consent_version,
        "consent_ts": user.consent_ts.isoformat() if user.consent_ts else None,
    }
    return {
        "profile": profile,
        "bookings": list(Booking.objects.filter(user=user).values(
            "id", "court__name", "date", "start_time", "end_time", "price", "status", "created_at"
        )),
        "payments": list(Payment.objects.filter(user=user).values(
            "id", "method", "amount", "currency", "status", "created_at"
        )),
        "notifications": list(Notification.objects.filter(user=user).values(
            "id", "event_type", "title", "created_at"
        )),
        "consent_records": list(ConsentRecord.objects.filter(user=user).values(
            "version", "granted", "source", "created_at"
        )),
        "audit_logs": list(AuditLog.objects.filter(user=user).values(
            "action", "entity", "entity_id", "created_at"
        )),
    }


def erase_user(user, ip=None):
    """Anonymize the account per GDPR right to erasure (anonymization)."""
    from apps.notifications.models import DeviceToken
    from apps.users.models import Status as UserStatus

    with transaction.atomic():
        DeviceToken.objects.filter(user=user).delete()
        user.email = f"erased-{user.id}@example.com"
        user.full_name = "Usuario eliminado"
        user.phone = ""
        user.avatar = ""
        user.status = UserStatus.DELETED
        user.is_active = False
        user.email_verified = False
        user.consent_version = None
        user.consent_ts = None
        user.save()
        ConsentRecord.objects.filter(user=user).update(granted=False)
        log_event(user, "gdpr.erase", "User", user.id, ip=ip)
    return user
