"""User account lifecycle helpers.

Business logic lives here, not in views/serializers (AGENTS.md §3).
"""

from apps.users.models import Status


def set_user_status(user, status):
    """Set account status and keep ``is_active`` in sync.

    SimpleJWT rejects inactive users on every request, so flipping
    ``is_active`` is what actually kills outstanding JWTs when an admin
    suspends an account. Leaving the two fields free to drift is the
    suspended-user-keeps-a-valid-JWT bug.
    """
    if status not in Status.values:
        raise ValueError(f"Estado invalido: {status}")
    user.status = status
    user.is_active = status == Status.ACTIVE
    user.save(update_fields=["status", "is_active"])
    return user
