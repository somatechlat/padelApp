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

# Production hostname — bare apex, no scheme. padel.settings.prod refuses
# to import without it. The value is normalized (a pasted
# "https://www.example.com" is accepted and reduced to "example.com"),
# and ALLOWED_HOSTS / CORS / CSRF origins are derived as apex + www.
# Leave this OUT of localprod — that mode uses LOCALPROD_DOMAIN instead.
PROD_DOMAIN = "andespadelclub.com"

EMAIL_HOST = ""
EMAIL_PORT = 587
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""

STRIPE_SECRET_KEY = "sk_test_..."
STRIPE_PUBLISHABLE_KEY = "pk_test_..."
STRIPE_WEBHOOK_SECRET = ""
