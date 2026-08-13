"""Base settings for PadelApp (Andes Padel).

Shared by all environments. Secrets (SECRET_KEY, DB credentials, Stripe keys)
live in ``runsecrets/secrets.py`` (mounted from ``docker/backend`` at runtime)
and are NOT tracked by git (constraint C2/C3). No secrets are read from
environment variables.
"""

from pathlib import Path

from django.utils.translation import gettext_lazy as _

from runsecrets import secrets

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = secrets.SECRET_KEY

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
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": secrets.DB_NAME,
        "USER": secrets.DB_USER,
        "PASSWORD": secrets.DB_PASSWORD,
        "HOST": secrets.DB_HOST,
        "PORT": secrets.DB_PORT,
    }
}

# --- Password hashing / validation (constraint C4) ------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "users.User"

# --- i18n (constraint C8) ---------------------------------------------------
LANGUAGE_CODE = "es"
LANGUAGES = [
    ("es", _("Espanol")),
    ("en", _("English")),
    ("pt", _("Portugues")),
    ("ca", _("Catalan")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True
TIME_ZONE = "UTC"  # storage in UTC (constraint C9); presentation via venue tz

# --- Celery / Redis (JWT blacklist + broker) --------------------------------
CELERY_BROKER_URL = secrets.REDIS_URL
CELERY_RESULT_BACKEND = secrets.REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULE = {
    "tournament-reminder-daily": {
        "task": "apps.events.tasks.tournament_reminder_task",
        "schedule": 86400.0,
    },
    "booking-reminder-daily": {
        "task": "apps.notifications.tasks.send_booking_reminders",
        "schedule": 86400.0,
    },
    "release-expired-holds": {
        "task": "apps.scheduling.tasks.release_expired_holds",
        "schedule": 300.0,
    },
}

# --- Push (FCM, open source SDK). Optional: without a service-account file
# the push channel is silently skipped (in-app + email still work).
FIREBASE_CREDENTIALS_PATH = getattr(
    secrets, "FIREBASE_CREDENTIALS_PATH", "/app/runsecrets/firebase-service-account.json"
)

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
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
        "anon": "100/min",
        "user": "1000/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
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
DEFAULT_FROM_EMAIL = "no-reply@andespadel.com"

# --- Media / static ------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
