from apps.security.models import AuditLog


def log_event(user, action, entity, entity_id="", before=None, after=None, ip=None):
    """Append-only audit trail entry."""
    AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
        entity_id=str(entity_id or ""),
        before=before or {},
        after=after or {},
        ip=ip,
    )
