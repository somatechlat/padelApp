"""Local-as-production settings: real security posture, local destinations.

This is a *separate module* rather than a set of flags on ``prod.py`` on
purpose. ``prod.py`` stays fail-closed and boring — every conditional in it is
a chance to ship a relaxed setting to the real server. The relaxed values live
here so they are reviewable in one file and greppable. It therefore imports
``_posture`` (the settings both production-shaped modes share) rather than
``prod`` itself: importing prod would demand a real ``PROD_DOMAIN`` and
non-empty SMTP credentials, which this mode deliberately does not have.

The two modes differ only in **where things go** (payments, email, push, data)
and **which host names they answer to**. They do not differ in security
posture: DEBUG is off, gunicorn serves the app, cookies are Secure, and the
app runs behind TLS.

Restrictions enforced here, so a laptop cannot reach real systems:

* Stripe keys must be test-mode; live keys are refused at import.
* Email is file-based, never SMTP — nothing is delivered to a customer.
* Push is disabled — no FCM send, in-app notifications still work.
* HSTS is off. A one-year HSTS header on a laptop hostname is a footgun, and
  HSTS *preload* is effectively irreversible for a real domain. Never enable
  it here.
"""

from padel.settings._checks import validate_localprod_secrets
from padel.settings._posture import *  # noqa: F401, F403
from padel.settings._secrets import read as read_secret

# --- Host -------------------------------------------------------------------
# Never a real domain. `local.` + `.test` is reserved by RFC 6761 for local
# names and cannot be resolved on the public internet.
LOCALPROD_DOMAIN = "local.andespadel.test"

# prod.py derives these from PROD_DOMAIN; here we answer to the local names
# only, so a stray browser on the laptop cannot reach this stack by a real
# hostname and vice versa.
ALLOWED_HOSTS = [LOCALPROD_DOMAIN, "localhost", "127.0.0.1"]
PROD_ORIGINS = [f"https://{LOCALPROD_DOMAIN}", "https://localhost"]
CORS_ALLOWED_ORIGINS = PROD_ORIGINS
CSRF_TRUSTED_ORIGINS = PROD_ORIGINS

# Base for one-click email links and any absolute URL this mode emits. Add
# `127.0.0.1 local.andespadel.test` to /etc/hosts to browse the stack by this
# name; `https://localhost:<nginx port>` works either way.
SITE_BASE_URL = f"https://{LOCALPROD_DOMAIN}"
# API_ORIGIN stays at base's gunicorn loopback: 127.0.0.1 is in ALLOWED_HOSTS
# above, unlike prod's domain-only allowlist, so journey_check can walk the
# API from inside the container without hairpinning through nginx.

# --- Transport security -----------------------------------------------------
# Keep the TLS posture from prod.py: Secure cookies and the SSL redirect are
# correct because nginx terminates TLS here too (self-signed).
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS off locally. PRELOAD must stay False unconditionally — see module doc.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# --- Destinations that must never be real ----------------------------------
# File-based, not console: console mail vanishes with the request, so a
# password reset cannot be inspected after the fact.
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "/app/artifacts/outbox"

# No real push. In-app notification rows are still written by the services.
PUSH_DISABLED = True

# Demo data may be seeded while DEBUG stays False — the whole point of this
# mode is a production-shaped stack with demo data in it.
ALLOW_DEMO_SEED = True

# --- Fail fast on anything that could take real money -----------------------
validate_localprod_secrets(
    {
        "SECRET_KEY": read_secret("secret-key"),
        "DB_PASSWORD": read_secret("db-password"),
        "STRIPE_SECRET_KEY": read_secret("stripe-secret-key"),
        "STRIPE_PUBLISHABLE_KEY": read_secret("stripe-publishable-key"),
    }
)
