"""Local SQLite settings for running tests without Docker/PostgreSQL.

Usage:
    pytest --ds=padel.settings.local_sqlite apps/courts apps/adminpanel
"""

from padel.settings.dev import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "local_test.sqlite3",  # noqa: F405
    }
}
