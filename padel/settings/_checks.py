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
