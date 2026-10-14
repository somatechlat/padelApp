import logging
from urllib.request import urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.events.models import Event

logger = logging.getLogger(__name__)

# Unsplash source URLs — stable, no API key needed, redirect to actual photos.
# Using specific photo IDs for deterministic results.
PADEL_IMAGES = {
    "Clinica de verano": "https://images.unsplash.com/photo-1554068865-24cecd4e34b8?w=800&q=80",
    "Torneo social mensual": "https://images.unsplash.com/photo-1622279457486-62dcc4a431d6?w=800&q=80",
    "Padel y amigos": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=800&q=80",
}


class Command(BaseCommand):
    help = "Download Unsplash padel images for demo events (idempotent — skips events that already have an image)."

    def handle(self, *args, **options):
        events = Event.objects.filter(image__isnull=True)
        updated = 0
        for event in events:
            url = PADEL_IMAGES.get(event.title)
            if not url:
                continue
            try:
                resp = urlopen(url, timeout=15)
                data = resp.read()
                ext = "jpg"
                filename = f"demo_{event.pk or event.title.lower().replace(' ', '_')}.{ext}"
                event.image.save(filename, ContentFile(data), save=True)
                updated += 1
                self.stdout.write(f"  + {event.title} -> {filename}")
            except Exception:
                logger.warning("Could not download image for '%s'", event.title, exc_info=True)
        self.stdout.write(self.style.SUCCESS(f"Seeded images: {updated} events updated."))
