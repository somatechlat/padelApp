"""Language resolution helpers for public club/banners APIs."""


def resolve_request_lang(request, default="es"):
    """Resolve client language from ?lang= or Accept-Language header."""
    lang = (request.query_params.get("lang") or request.GET.get("lang") or "").strip()
    if not lang:
        accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        if accept:
            lang = accept.split(",")[0].split(";")[0].strip()
    lang = (lang or "").split("-")[0].lower()
    return lang or default
