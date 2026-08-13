"""
Template for runtime secrets. Copy to ``secrets.py`` and fill real values.

Keep this file and ``secrets.py`` OUT of git. This example ships so the
deployment can be reproduced; real secrets.py is never committed.
"""

import secrets as _std

SECRET_KEY = "dev-only-" + _std.token_hex(32)

DB_NAME = "padel"
DB_USER = "padel"
DB_PASSWORD = "padel_dev"
DB_HOST = "db"
DB_PORT = 5432

REDIS_URL = "redis://redis:6379/0"

EMAIL_HOST = ""
EMAIL_PORT = 587
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""

STRIPE_SECRET_KEY = "sk_test_..."
STRIPE_PUBLISHABLE_KEY = "pk_test_..."
STRIPE_WEBHOOK_SECRET = ""
