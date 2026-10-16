"""Base settings for PadelApp (Andes Padel).

Shared by all environments. Configuration — hosts, ports, database names,
club links, the API origin — lives here and in the per-environment modules.
Secrets live in one file per value under ``/run/secrets`` (Docker secrets,
mounted by compose) and are read through ``padel.settings._secrets``. They are
NOT tracked by git (constraint C2/C3) and are NOT read from environment
variables, which any process that can run ``docker inspect`` would see.
"""

from pathlib import Path

from django.utils.translation import gettext_lazy as _

from padel.settings._secrets import read as read_secret

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = read_secret("secret-key")

DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "django_filters",
    # local apps
    "apps.common",
    "apps.users",
    "apps.verification",
    "apps.courts",
    "apps.scheduling",
    "apps.pricing",
    "apps.bookings",
    "apps.payments",
    "apps.policies",
    "apps.notifications",
    "apps.adminpanel",
    "apps.reports",
    "apps.events",
    "apps.security",
    "apps.gdpr",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "padel.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "padel.wsgi.application"
ASGI_APPLICATION = "padel.asgi.application"

# --- Database (PostgreSQL only, constraint C10) ---------------------------
# Topology, not secrets: name, user, host and port are configuration and
# belong in settings. Only the password is a secret.
DB_NAME = "padel"
DB_USER = "padel"
DB_HOST = "db"
DB_PORT = 5432

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": read_secret("db-password"),
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}

# --- Password hashing / validation (constraint C4) ------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "users.User"

# --- i18n (constraint C8) ---------------------------------------------------
LANGUAGE_CODE = "es"
LANGUAGES = [
    ("es", _("Espanol")),
    ("en", _("English")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True
# Club is in Quito (America/Guayaquil, UTC-5). Wall-clock TimeFields (bookings,
# schedules) and "is this slot in the past?" checks must use this zone — not UTC.
TIME_ZONE = "America/Guayaquil"

# --- Celery / Redis (JWT blacklist + broker) --------------------------------
# No credentials on this broker, so the URL is configuration, not a secret.
REDIS_URL = "redis://redis:6379/0"
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Guayaquil"
CELERY_BEAT_SCHEDULE = {
    "tournament-reminder-daily": {
        "task": "apps.events.tasks.tournament_reminder_task",
        "schedule": 86400.0,
    },
    "booking-reminder-daily": {
        "task": "apps.notifications.tasks.send_booking_reminders",
        "schedule": 86400.0,
    },
    "booking-reminder-2h": {
        "task": "apps.notifications.tasks.send_booking_reminders_2h",
        "schedule": 1800.0,  # every 30 minutes
    },
    "release-expired-holds": {
        "task": "apps.scheduling.tasks.release_expired_holds",
        "schedule": 300.0,
    },
}

# --- Push (FCM, open source SDK). Optional: without a service-account file
# the push channel is silently skipped (in-app + email still work).
FIREBASE_CREDENTIALS_PATH = "/run/secrets/firebase-service-account.json"

# --- Stripe -------------------------------------------------------------------
# Optional here so a laptop or CI run works with no payment credentials at
# all; prod and localprod refuse to start without them (see their validation).
STRIPE_SECRET_KEY = read_secret("stripe-secret-key", default="")
STRIPE_PUBLISHABLE_KEY = read_secret("stripe-publishable-key", default="")
STRIPE_WEBHOOK_SECRET = read_secret("stripe-webhook-secret", default="")

# --- JWT (SimpleJWT, rotating + blacklist, constraint F-0072) ----------------
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# --- DRF ---------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
        "anon": "100/min",
        "user": "1000/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Andes Padel API",
    "DESCRIPTION": "REST API para la reservacion de canchas de padel de Andes Padel.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- Email -------------------------------------------------------------------
# Real SMTP config belongs in dev/prod; tests use the locmem backend.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "Andes Pádel <no-reply@andespadelclub.com>"
# Public origin used to build one-click verification / reset links in emails.
# prod.py re-derives this from PROD_DOMAIN, so it is the single source for
# every absolute link the backend emits — templates must not spell out hosts.
SITE_BASE_URL = "http://127.0.0.1:28003"

# Origin (scheme://host[:port], no path) for management commands that walk the
# API. They run inside the backend container, where gunicorn answers on 8000 —
# the host port SITE_BASE_URL uses (nginx) does not exist there. Dev accepts the
# loopback Host because ALLOWED_HOSTS is ["*"], and localprod keeps 127.0.0.1 in
# its allowlist; only prod, whose allowlist is domain-only, re-points it at the
# public origin (see prod.py).
API_ORIGIN = "http://127.0.0.1:8000"

# --- Club profile used by outbound email ---------------------------------------
# Display values mirror landing/index.html. Settings own them so a deployment
# changes one place: prod inherits these and only swaps SITE_BASE_URL above.
CLUB_CITY = "Quito, Ecuador"
CLUB_ADDRESS = "Rodríguez Labandera y Ernesto Albán esquina"
CLUB_WHATSAPP = "099 267 6842"
CLUB_WHATSAPP_URL = "https://wa.me/593992676842"
CLUB_EMAIL = "andespadelclub@gmail.com"
CLUB_INSTAGRAM = "@andespadelec"
CLUB_INSTAGRAM_URL = "https://instagram.com/andespadelec"
CLUB_MAPS_URL = "https://maps.google.com/?q=Rodriguez+Labandera+y+Ernesto+Alban+Quito+Ecuador"

# --- Media / static ------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/adminpanel/login/"
LOGIN_REDIRECT_URL = "/adminpanel/"
