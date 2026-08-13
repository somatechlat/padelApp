from celery import shared_task

from apps.notifications.services import NotificationService


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def notify_task(self, user_id, event_type, title, body="", data=None):
    from django.contrib.auth import get_user_model

    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        return None
    try:
        NotificationService.notify(user, event_type, title, body, data or {})
    except Exception as exc:
        raise self.retry(exc=exc)
    return user_id
