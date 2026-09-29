"""Shared seed helpers for Andes Padel club profile and promo banners."""

from pathlib import Path

from django.core.files import File

from apps.courts.models import PromoBanner, Venue

SEED_ASSETS = Path(__file__).resolve().parent / "seed_assets" / "banners"

CLUB_DEFAULTS = {
    "address": "Rodríguez Labandera y Ernesto Albán esquina, Quito",
    "maps_query": "Rodríguez Labandera y Ernesto Albán esquina, Quito",
    "maps_url": (
        "https://www.google.com/maps/search/?api=1&query="
        "Rodr%C3%ADguez+Labandera+y+Ernesto+Alb%C3%A1n+esquina%2C+Quito"
    ),
    "phone": "099 267 6842",
    "email": "andespadelclub@gmail.com",
    "whatsapp_number": "593992676842",
    "whatsapp_message": "Hola, quiero reservar una cancha en Andes Padel.",
    "instagram_url": "https://instagram.com/andespadelec",
    "home_section_title_i18n": {
        "es": "Reserva tu cancha",
        "en": "Book your court",
        "pt": "Reserve sua quadra",
        "ca": "Reserva la teva pista",
    },
    "home_greeting_tagline_i18n": {
        "es": "Reserva tu cancha de pádel",
        "en": "Book your padel court",
        "pt": "Reserve sua quadra de pádel",
        "ca": "Reserva la teva pista de pàdel",
    },
    "bank_name": "Banco Pichincha",
    "bank_account_number": "21001234567890",
    "bank_account_holder": "Andes Pádel S.A.",
    "bank_account_code": "ANDESPADEL",
    "bank_extra": "Cuenta de ahorros",
}

BANNER_SEEDS = [
    {
        "slug": "banner_torneo_verano.png",
        "title_i18n": {
            "es": "Torneo de Verano",
            "en": "Summer Tournament",
            "pt": "Torneio de Verão",
            "ca": "Torneig d'Estiu",
        },
        "subtitle_i18n": {
            "es": "Inscripciones abiertas",
            "en": "Registration open",
            "pt": "Inscrições abertas",
            "ca": "Inscripcions obertes",
        },
        "link_type": PromoBanner.LinkType.EVENT,
        "link_url": "",
        "sort_order": 10,
    },
    {
        "slug": "banner_quedadas.png",
        "title_i18n": {
            "es": "Quedadas de Pádel",
            "en": "Padel Meetups",
            "pt": "Encontros de Pádel",
            "ca": "Trobades de Pàdel",
        },
        "subtitle_i18n": {
            "es": "Cada semana",
            "en": "Every week",
            "pt": "Toda semana",
            "ca": "Cada setmana",
        },
        "link_type": PromoBanner.LinkType.NONE,
        "link_url": "",
        "sort_order": 20,
    },
    {
        "slug": "banner_academia.png",
        "title_i18n": {
            "es": "Academia Andes",
            "en": "Andes Academy",
            "pt": "Academia Andes",
            "ca": "Acadèmia Andes",
        },
        "subtitle_i18n": {
            "es": "Clases y entrenamiento",
            "en": "Lessons and training",
            "pt": "Aulas e treino",
            "ca": "Classes i entrenament",
        },
        "link_type": PromoBanner.LinkType.NONE,
        "link_url": "",
        "sort_order": 30,
    },
    {
        "slug": "banner_ligas.png",
        "title_i18n": {
            "es": "Ligas Internas",
            "en": "Internal Leagues",
            "pt": "Ligas Internas",
            "ca": "Lligues Internes",
        },
        "subtitle_i18n": {
            "es": "Temporada en curso",
            "en": "Season in progress",
            "pt": "Temporada em andamento",
            "ca": "Temporada en curs",
        },
        "link_type": PromoBanner.LinkType.NONE,
        "link_url": "",
        "sort_order": 40,
    },
]


def seed_club_profile(name="Andes Padel"):
    """Upsert the singleton-like Venue with real Andes Padel contact/bank data."""
    venue, _created = Venue.objects.get_or_create(name=name, defaults={})
    changed = False
    for field, value in CLUB_DEFAULTS.items():
        current = getattr(venue, field)
        if not current:
            setattr(venue, field, value)
            changed = True
    if changed:
        venue.save()
    return venue


def seed_promo_banners():
    """Create demo promo banners from synthetic assets under seed_assets/banners."""
    created = 0
    for row in BANNER_SEEDS:
        title_es = row["title_i18n"].get("es", "")
        existing = PromoBanner.objects.filter(
            title_i18n__es=title_es
        ).first()
        if existing:
            continue
        source = SEED_ASSETS / row["slug"]
        if not source.exists():
            continue
        banner = PromoBanner(
            title_i18n=row["title_i18n"],
            subtitle_i18n=row["subtitle_i18n"],
            link_type=row["link_type"],
            link_url=row["link_url"],
            active=True,
            sort_order=row["sort_order"],
        )
        with source.open("rb") as handle:
            banner.image.save(row["slug"], File(handle), save=False)
        banner.save()
        created += 1
    return created
