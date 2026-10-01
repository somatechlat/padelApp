"""Production settings. Fail fast if secrets are missing or dev-only."""

from padel.settings._checks import validate_production_secrets
from padel.settings.base import *  # noqa: F401, F403
from runsecrets import secrets

DEBUG = False

# Production hostname comes from settings/secrets.py (PROD_DOMAIN). The old
# host and domains are retired and deliberately not present in this tree —
# see validate_production_host() for why this is not hard-coded.
from padel.settings._checks import derive_prod_hosts, validate_production_host  # noqa: E402

# Stored as the bare apex so the www/app forms can be derived once, here.
PROD_DOMAIN = validate_production_host(getattr(secrets, "PROD_DOMAIN", ""))
ALLOWED_HOSTS = derive_prod_hosts(PROD_DOMAIN)
PROD_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

CORS_ALLOWED_ORIGINS = PROD_ORIGINS
# Django 4+ rejects POST without this, so the staff panel 403s on every
# form submit if it is missing while CORS_ALLOWED_ORIGINS is set.
CSRF_TRUSTED_ORIGINS = PROD_ORIGINS

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = secrets.EMAIL_HOST
EMAIL_PORT = secrets.EMAIL_PORT
EMAIL_USE_TLS = True
EMAIL_HOST_USER = secrets.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = secrets.EMAIL_HOST_PASSWORD

# --- Fail-fast secret check (constraint C2/C3, NFR-0008) --------------------
validate_production_secrets(
    {
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
)
