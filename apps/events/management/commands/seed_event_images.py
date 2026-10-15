import logging

from django.core.management.base import BaseCommand

from apps.events.models import Event

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Report which events have images and which do not. "
        "Images are uploaded by staff through the admin panel — nothing is hardcoded."
    )

    def handle(self, *args, **options):
        with_img = Event.objects.exclude(image="").exclude(image=None)
        without_img = Event.objects.filter(image="") | Event.objects.filter(image=None)
        for e in with_img:
            self.stdout.write(f"  [OK] {e.title} -> {e.image.name}")
        for e in without_img:
            self.stdout.write(self.style.WARNING(f"  [--] {e.title} (no image — upload in admin)"))
        self.stdout.write(
            self.style.SUCCESS(f"Events with image: {with_img.count()} / {Event.objects.count()}")
        )
