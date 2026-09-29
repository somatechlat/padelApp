REQUIRED_PROD_SECRETS = (
    "SECRET_KEY",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "REDIS_URL",
    "EMAIL_HOST",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
)


def validate_production_secrets(values):
    """Fail fast on blank or dev-only production secrets (constraint C2/C3, NFR-0008)."""
    missing = [k for k in REQUIRED_PROD_SECRETS if not values.get(k)]
    if missing:
        raise RuntimeError(f"Missing required secrets in docker/backend/secrets.py (via runsecrets): {', '.join(missing)}")
    if str(values.get("SECRET_KEY")).startswith("dev-only-"):
        raise RuntimeError("Production SECRET_KEY must not be the dev placeholder (constraint C2).")


def validate_production_host(domain):
    """Normalize the production hostname to a bare apex and reject junk.

    Operators paste what the browser shows — ``https://www.example.com/`` — so
    accept that shape rather than making them guess. Strip the scheme, any
    ``www.`` prefix, a port and a path, and return the bare apex. Deriving
    ``ALLOWED_HOSTS`` as ``[apex, f"www.{apex}"]`` then cannot produce
    ``www.www.…``, which is what happens if a www-prefixed value is stored
    as-is and re-prefixed at the call site.

    The value still has to be supplied in docker/backend/secrets.py (via runsecrets) — nothing in the
    tree carries a default, so a deploy cannot silently bind to a name someone
    else now controls. The previous host and its domains are retired.
    """
    if not domain or not str(domain).strip():
        raise RuntimeError(
            "PROD_DOMAIN is not set. Put the production hostname in "
            "docker/backend/secrets.py (via runsecrets) as PROD_DOMAIN before deploying — for "
            "example PROD_DOMAIN = \"andespadelclub.com\". Do not reuse a "
            "retired hostname."
        )
    value = str(domain).strip().lower()
    for scheme in ("https://", "http://"):
        if value.startswith(scheme):
            value = value[len(scheme):]
    # Host only: drop any path, query, fragment and port the operator pasted.
    value = value.split("/")[0].split("?")[0].split("#")[0].split(":")[0]
    if value.startswith("www."):
        value = value[4:]
    if not value or "." not in value or " " in value or value.startswith("."):
        raise RuntimeError(
            "PROD_DOMAIN must be a hostname such as andespadelclub.com "
            f"(got {domain!r})."
        )
    return value


def validate_localprod_secrets(values):
    """Refuse anything that could move real money or ship a real secret.

    The local-as-production mode must be production-*shaped* without being
    production. Live Stripe keys are the one thing that would make a laptop
    run charge a real card, so they are rejected at import rather than
    discovered in a statement.
    """
    secret_key = str(values.get("SECRET_KEY") or "")
    if not secret_key:
        raise RuntimeError("localprod requires SECRET_KEY in docker/backend/secrets.py.")
    if secret_key.startswith("dev-only-"):
        raise RuntimeError(
            "localprod requires a real random SECRET_KEY (the dev placeholder "
            "is refused, same as production)."
        )
    for name in ("STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"):
        value = str(values.get(name) or "")
        if not value:
            raise RuntimeError(f"localprod requires {name} in docker/backend/secrets.py.")
        if value.startswith(("sk_live_", "pk_live_")):
            raise RuntimeError(
                f"{name} is a LIVE Stripe key. localprod refuses live keys — "
                "use sk_test_/pk_test_ so no real card can be charged."
            )
        if not value.startswith(("sk_test_", "pk_test_")):
            raise RuntimeError(
                f"{name} must be a Stripe TEST key (sk_test_/pk_test_), got a "
                "value with neither prefix."
            )
