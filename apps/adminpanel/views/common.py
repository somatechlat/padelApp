"""Shared helpers for admin panel views."""

from datetime import datetime

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def validate_image_upload(uploaded, field_label="imagen"):
    """Return an error string or None when the upload looks like a valid image."""
    if not uploaded:
        return f"La {field_label} es obligatoria."
    content_type = getattr(uploaded, "content_type", "") or ""
    name = getattr(uploaded, "name", "") or ""
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        return f"Tipo de archivo no permitido ({content_type}). Use JPEG, PNG, WebP o GIF."
    if name and not name.lower().endswith(ALLOWED_IMAGE_EXTS):
        return "Extension de archivo no permitida. Use .jpg, .jpeg, .png, .webp o .gif."
    return None


def i18n_from_post(request, prefix):
    data = {}
    for lang in ("es", "en", "pt", "ca"):
        value = (request.POST.get(f"{prefix}_{lang}") or "").strip()
        if value:
            data[lang] = value
    return data


def parse_dt(value):
    if not value:
        return None
    return datetime.fromisoformat(value)
