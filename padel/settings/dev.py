"""Development settings. Never use in production."""

from padel.settings.base import *  # noqa: F403
from padel.settings.base import BASE_DIR

DEBUG = True
ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

INTERNAL_IPS = ["127.0.0.1", "0.0.0.0"]

MEDIA_ROOT = BASE_DIR / "media"
