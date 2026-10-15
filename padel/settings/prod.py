"""Production settings. Fail fast if secrets are missing or dev-only."""

# Production hostname comes from a mounted secret (the bare apex). The old
# host and domains are retired and deliberately not present in this tree —
# see validate_production_host() for why this is not hard-coded.
from padel.settings._checks import (  # noqa: E402
    derive_prod_hosts,
    validate_production_host,
    validate_production_secrets,
)
from padel.settings._posture import *  # noqa: F401, F403
from padel.settings._secrets import read as read_secret

# Stored as the bare apex so the www/app forms are derived once, here.
PROD_DOMAIN = validate_production_host(read_secret("prod-domain"))
ALLOWED_HOSTS = derive_prod_hosts(PROD_DOMAIN)
PROD_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

CORS_ALLOWED_ORIGINS = PROD_ORIGINS
# Django 4+ rejects POST without this, so the staff panel 403s on every
# form submit if it is missing while CORS_ALLOWED_ORIGINS is set.
CSRF_TRUSTED_ORIGINS = PROD_ORIGINS

# --- Database ----------------------------------------------------------------
# Topology is configuration; only the password is a secret.
DB_NAME = "padel_prod"
DB_USER = "padel"
DB_HOST = "db"
DB_PORT = 5432

# --- Email -------------------------------------------------------------------
# SMTP here, not console or file: this is the environment that must deliver.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = read_secret("email-host")
EMAIL_HOST_USER = read_secret("email-host-user")
EMAIL_HOST_PASSWORD = read_secret("email-host-password")
# Port 465 is implicit TLS (SMTPS) and speaks no STARTTLS upgrade; port 587 is
# plaintext that upgrades via STARTTLS. Hardcoding EMAIL_USE_TLS made 465 fail
# with "Connection unexpectedly closed", and the other way round would break
# 587 — so the mode is derived from the port the operator configured.
EMAIL_PORT = 465
EMAIL_USE_SSL = EMAIL_PORT == 465
EMAIL_USE_TLS = EMAIL_PORT == 587
EMAIL_TIMEOUT = 30
# Display name matters in the inbox: "Andes Pádel <no-reply@...>" not bare.
_raw_from = read_secret("email-from", default=EMAIL_HOST_USER)
DEFAULT_FROM_EMAIL = _raw_from if "<" in _raw_from else f"Andes Pádel <{_raw_from}>"
# One-click verification / reset links in transactional email.
SITE_BASE_URL = f"https://app.{PROD_DOMAIN}"
# ALLOWED_HOSTS above is a domain allowlist with no loopback, so in-container
# API walks (journey_check) must speak to the public origin instead.
API_ORIGIN = SITE_BASE_URL

# --- Fail-fast secret check (constraint C2/C3, NFR-0008) --------------------
validate_production_secrets(
    {
        "SECRET_KEY": read_secret("secret-key", default=None),
        "DB_PASSWORD": read_secret("db-password", default=None),
        "EMAIL_HOST": EMAIL_HOST,
        "EMAIL_HOST_USER": EMAIL_HOST_USER,
        "EMAIL_HOST_PASSWORD": EMAIL_HOST_PASSWORD,
        "STRIPE_SECRET_KEY": read_secret("stripe-secret-key", default=None),
        "STRIPE_PUBLISHABLE_KEY": read_secret("stripe-publishable-key", default=None),
    }
)
