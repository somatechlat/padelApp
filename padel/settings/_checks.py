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
        raise RuntimeError(f"Missing required secrets in settings/secrets.py: {', '.join(missing)}")
    if str(values.get("SECRET_KEY")).startswith("dev-only-"):
        raise RuntimeError("Production SECRET_KEY must not be the dev placeholder (constraint C2).")


def validate_production_host(domain):
    """Fail fast when the production hostname has not been supplied.

    The previous host and its domains are retired. A new server + domain
    replace them and the values must be set in settings/secrets.py — they are
    deliberately not hard-coded anywhere in the tree, so a deploy cannot
    silently bind to a name someone else now controls.
    """
    if not domain or not str(domain).strip():
        raise RuntimeError(
            "PROD_DOMAIN is not set. Production is moving to a new server and "
            "domain; put the new hostname in settings/secrets.py as PROD_DOMAIN "
            "before deploying. Do not reuse a retired hostname."
        )
    domain = str(domain).strip()
    if domain.startswith(("http://", "https://")):
        raise RuntimeError("PROD_DOMAIN must be a bare hostname, not a URL.")
    return domain
