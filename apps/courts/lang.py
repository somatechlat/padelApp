"""Single Accept-Language resolver for the whole Django project.

Both the public club/banners APIs and the auth registration flow resolve the
client language here. Do not add another parser.
"""

from django.conf import settings


def resolve_request_lang(request, default="es"):
    """Resolve client language from ?lang= or the Accept-Language header.

    Only tags the app actually supports (``settings.LANGUAGES``) are returned,
    so a browser asking for an unsupported language falls back to *default*
    instead of leaking that tag into the UI. Pass ``default=None`` to get
    ``None`` when nothing supported was requested (e.g. registration seeding,
    which must not overwrite the user's language for a missing header).
    """
    supported = {code for code, _label in settings.LANGUAGES}
    param = (request.query_params.get("lang") or request.GET.get("lang") or "").strip()
    if param:
        code = param.split("-")[0].lower()
        if code in supported:
            return code
    accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for part in accept.split(","):
        code = part.split(";")[0].strip().split("-")[0].lower()
        if code in supported:
            return code
    return default
