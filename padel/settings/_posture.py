"""Security posture shared by both production-shaped modes.

Reads no secrets and derives no hosts. It is the part of production that a
laptop run must keep byte-identical: DEBUG off, Secure cookies, the TLS
redirect, and the clickjacking / sniffing / referrer headers.

``prod.py`` layers the real domain, SMTP and the fail-closed secret check on
top; ``prod_local.py`` layers local destinations and its own validation. This
module exists so prod_local does not have to ``from prod import *`` — which
would drag in PROD_DOMAIN validation and the SMTP requirement that localprod's
secrets deliberately leave empty. Keeping the posture here means neither mode
can quietly relax the other: anything added to this file is on by default in
both, and turning it off stays a visible override in ``prod_local.py``.

HSTS is the one setting both modes declare and prod_local deliberately turns
off — a one-year HSTS header on a laptop hostname is a footgun, and *preload*
is effectively irreversible for a real domain.
"""

from padel.settings.base import *  # noqa: F401, F403

DEBUG = False

# TLS is terminated upstream of gunicorn in both modes (the host vhost in
# prod, the localprod nginx with its self-signed cert), so Django must trust
# the proxy's scheme header and redirect plain-http requests itself.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# prod_local turns all three back off. See its module docstring.
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
