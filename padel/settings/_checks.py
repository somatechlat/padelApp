# Names of the mounted files under /run/secrets that production cannot start
# without. Topology (DB name/user/host, the redis URL) is configuration and
# lives in the settings modules — only real secrets are listed here.
REQUIRED_PROD_SECRETS = (
    "SECRET_KEY",
    "DB_PASSWORD",
    "EMAIL_HOST",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
)

# Values that ship as examples in the templates and must never reach a real
# deployment. They are the shape of a secret, not one, and a box running on
# them looks healthy right up until it hits Stripe or Postgres.
PLACEHOLDER_SECRET_VALUES = {
    "sk_test_replace_me",
    "pk_test_replace_me",
    "padel_prod_change_me",
    "change_me",
    "replace_me",
}


def validate_production_secrets(values):
    """Fail fast on blank, dev-only or placeholder production secrets (C2/C3)."""
    missing = [k for k in REQUIRED_PROD_SECRETS if not values.get(k)]
    if missing:
        raise RuntimeError(
            "Missing required secrets. Provision them as Docker secrets before "
            f"starting (files under /run/secrets): {', '.join(missing)}"
        )
    if str(values.get("SECRET_KEY")).startswith("dev-only-"):
        raise RuntimeError("Production SECRET_KEY must not be the dev placeholder (constraint C2).")
    placeholder = sorted(
        k for k, v in values.items() if str(v or "").strip() in PLACEHOLDER_SECRET_VALUES
    )
    if placeholder:
        raise RuntimeError(
            "These secrets still hold a value copied from a template: "
            f"{', '.join(placeholder)}. Real values only — provision them under "
            "/run/secrets (make secrets-init generates random ones)."
        )


def validate_production_host(domain):
    """Normalize the production hostname to a bare apex and reject junk.

    Operators paste what the browser shows — ``https://www.example.com/`` — so
    accept that shape rather than making them guess. Strip the scheme, any
    ``www.`` prefix, a port and a path, and return the bare apex. Deriving
    ``ALLOWED_HOSTS`` as ``[apex, f"www.{apex}", f"app.{apex}"]`` then cannot
    produce ``www.www.…``, which is what happens if a www-prefixed value is
    stored as-is and re-prefixed at the call site. An ``app.`` prefix is
    deliberately NOT stripped: that is the live app-facing name and must be
    kept verbatim.

    The value still has to be supplied as a mounted secret (``/run/secrets/
    prod-domain``) — nothing in the tree carries a default, so a deploy cannot
    silently bind to a name someone else now controls. The previous host and
    its domains are retired.
    """
    if not domain or not str(domain).strip():
        raise RuntimeError(
            "prod-domain is not set. Put the bare production apex in "
            "/run/secrets/prod-domain before deploying — for example "
            '"andespadelclub.com". Do not reuse a retired hostname.'
        )
    value = str(domain).strip().lower()
    for scheme in ("https://", "http://"):
        if value.startswith(scheme):
            value = value[len(scheme) :]
    # Host only: drop any path, query, fragment and port the operator pasted.
    value = value.split("/")[0].split("?")[0].split("#")[0].split(":")[0]
    if value.startswith("www."):
        value = value[4:]
    if not value or "." not in value or " " in value or value.startswith("."):
        raise RuntimeError(
            f"PROD_DOMAIN must be a hostname such as andespadelclub.com (got {domain!r})."
        )
    return value


def derive_prod_hosts(domain):
    """Return the full production allowlist for a validated apex.

    Apex + www + app. The mobile apps and the staff panel are served from the
    ``app.`` host; the apex and www live on a different machine and still need
    to be a legal Host/Origin so a stray request cannot 400 and so CORS/CSRF
    cover the origin the apps actually call.

    Pure function so the allowlist shape is testable without importing
    ``padel.settings.prod`` — that module refuses to import without real
    production secrets, which is intentional and must not be relaxed for a
    unit test.
    """
    apex = validate_production_host(domain)
    return [apex, f"www.{apex}", f"app.{apex}"]


def validate_localprod_secrets(values):
    """Refuse anything that could move real money or ship a real secret.

    The local-as-production mode must be production-*shaped* without being
    production. Live Stripe keys are the one thing that would make a laptop
    run charge a real card, so they are rejected at import rather than
    discovered in a statement.
    """
    secret_key = str(values.get("SECRET_KEY") or "")
    if not secret_key:
        raise RuntimeError("localprod requires /run/secrets/secret-key.")
    if secret_key.startswith("dev-only-"):
        raise RuntimeError(
            "localprod requires a real random SECRET_KEY (the dev placeholder "
            "is refused, same as production)."
        )
    for name in ("STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"):
        value = str(values.get(name) or "")
        if not value:
            raise RuntimeError(f"localprod requires /run/secrets/{name.lower().replace('_', '-')}.")
        if value in PLACEHOLDER_SECRET_VALUES:
            raise RuntimeError(
                f"{name} still holds the template value {value!r}. localprod "
                "runs on real test-mode keys, not placeholders."
            )
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
