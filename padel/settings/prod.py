"""Production settings. Fail fast if secrets are missing or dev-only."""

from padel.settings.base import *  # noqa: F401, F403
from runsecrets import secrets

DEBUG = False
ALLOWED_HOSTS = ["andespadel.com", "www.andespadel.com"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

CORS_ALLOWED_ORIGINS = [
    "https://andespadel.com",
    "https://www.andespadel.com",
]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = secrets.EMAIL_HOST
EMAIL_PORT = secrets.EMAIL_PORT
EMAIL_USE_TLS = True
EMAIL_HOST_USER = secrets.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = secrets.EMAIL_HOST_PASSWORD

# --- Fail-fast secret check (constraint C2/C3, NFR-0008) --------------------
_req = {
    "SECRET_KEY": secrets.SECRET_KEY,
    "DB_NAME": secrets.DB_NAME,
    "DB_USER": secrets.DB_USER,
    "DB_PASSWORD": secrets.DB_PASSWORD,
    "DB_HOST": secrets.DB_HOST,
    "REDIS_URL": secrets.REDIS_URL,
    "EMAIL_HOST": getattr(secrets, "EMAIL_HOST", None),
    "EMAIL_HOST_USER": getattr(secrets, "EMAIL_HOST_USER", None),
    "EMAIL_HOST_PASSWORD": getattr(secrets, "EMAIL_HOST_PASSWORD", None),
}
_missing = [k for k, v in _req.items() if not v]
if _missing:
    raise RuntimeError(f"Missing required secrets in settings/secrets.py: {', '.join(_missing)}")
if secrets.SECRET_KEY.startswith("dev-only-"):
    raise RuntimeError("Production SECRET_KEY must not be the dev placeholder (constraint C2).")
