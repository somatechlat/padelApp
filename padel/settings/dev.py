"""Development settings. Never use in production."""

from padel.settings.base import *  # noqa: F401, F403  # noqa: F403
from padel.settings.base import BASE_DIR

DEBUG = True
ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

# Run Celery tasks synchronously in dev/tests; the worker container uses prod
# settings with the real broker.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# 0.0.0.0 here is a debug-toolbar client address, not a socket bind.
# bandit reads it as one (B104); it is not.
INTERNAL_IPS = ["127.0.0.1", "0.0.0.0"]  # nosec B104

MEDIA_ROOT = BASE_DIR / "media"
