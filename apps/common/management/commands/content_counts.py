"""Row counts for the club content that ``mirror_content`` copies.

Run on both sides — production and local — and diff the output. Identical
counts are what "the mirror is in sync" means; anything else shows up as a
number rather than as a bug report three screens into the app.
"""

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

# Same models, same order as mirror_content.CONTENT_MODELS.
CONTENT_MODELS = (
    "users.SkillLevel",
    "courts.Venue",
    "courts.Court",
    "courts.CourtSchedule",
    "courts.PromoBanner",
    "pricing.PriceRule",
    "pricing.Holiday",
    "policies.CancellationPolicy",
    "events.Event",
    "events.Tournament",
    "events.OpenMatch",
    "events.NewsPost",
)


class Command(BaseCommand):
    help = "Print row counts for the mirrored club content, one per line."

    def handle(self, *args, **options):
        for label in CONTENT_MODELS:
            count = django_apps.get_model(label).objects.count()
            self.stdout.write(f"{label:34s} {count}")
