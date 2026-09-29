"""Template for the local-as-production mode (``padel.settings.prod_local``).

Copy to ``docker/backend/secrets.py`` when running ``make up-localprod``.

This file is deliberately stricter than ``secrets.example.py`` in one way and
looser in another:

* **Stricter:** Stripe must be test-mode and SECRET_KEY must be real. The
  localprod settings module refuses live keys at import, so a laptop run
  cannot charge a real card.
* **Looser:** SMTP is left empty and demo seeding is allowed. Email goes to a
  local outbox directory instead of a customer's inbox.

``PROD_DOMAIN`` is deliberately **absent**. localprod answers to
``local.andespadel.test`` only; it must never know a real hostname.
"""

import secrets as _std

# Real random key — the `dev-only-` placeholder is refused here, same as prod.
SECRET_KEY = _std.token_hex(32)

DB_NAME = "padel"
DB_USER = "padel"
DB_PASSWORD = "padel_dev"
DB_HOST = "db"
DB_PORT = 5432

REDIS_URL = "redis://redis:6379/0"

# No PROD_DOMAIN here on purpose. See the module docstring.

# Email is forced to the file-based backend by prod_local; these stay empty so
# nothing can be configured to reach an SMTP relay by accident.
EMAIL_HOST = ""
EMAIL_PORT = 587
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
# Where file-based mail is written. Mounted as ./artifacts/outbox in compose.
EMAIL_FILE_PATH = "/app/artifacts/outbox"

# TEST keys only. `sk_live_` / `pk_live_` raise on import in prod_local.
STRIPE_SECRET_KEY = "sk_test_replace_me"
STRIPE_PUBLISHABLE_KEY = "pk_test_replace_me"
STRIPE_WEBHOOK_SECRET = ""

# Demo data for a production-shaped stack. prod_local sets ALLOW_DEMO_SEED=True;
# this is documentation of intent, not a switch read by the settings module.
ALLOW_DEMO_SEED = True
