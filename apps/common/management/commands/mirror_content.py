"""Load a production content dump into this database, verbatim.

``make mirror-prod`` dumps the club's content from the running production
container with ``dumpdata`` and pipes it here. Rows keep their original
primary keys, so a court is the same court locally as it is in production —
ids included — and anything keyed by them points at the same object on both
sides.

Before writing, the same models are cleared, so the result is a mirror and not
a merge: a court archived in production does not linger locally, and a count
that matches production's is proof rather than hope. Postgres sequences are
reset afterwards, because inserting rows with production's ids leaves them
behind and the next local insert would collide with a mirrored row.

Personal data is deliberately absent from the dump. Where a row references a
user that only exists in production, the reference is dropped when the field
allows it and repointed to the mirror owner account when it does not.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.core.serializers import deserialize
from django.db import connection, transaction

from apps.users.models import Role, Status, User

# Parents before children. Clearing a parent cascades to the rest, and this
# order keeps the reload legal. users.SkillLevel goes last because open
# matches and user profiles point at it.
CONTENT_MODELS = (
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
    "users.SkillLevel",
)

# Local account that owns production-authored rows whose author does not exist
# here. Unusable password, owner role, named so nobody mistakes it for a
# customer: it exists so an open match can be mirrored at all.
MIRROR_OWNER_EMAIL = "mirror-owner@local.andespadel.test"


def mirror_owner() -> User:
    user = User.objects.filter(email=MIRROR_OWNER_EMAIL).first()
    if user:
        return user
    return User.objects.create_user(
        email=MIRROR_OWNER_EMAIL,
        password=None,
        full_name="Mirror Owner (local)",
        role=Role.DUENO,
        status=Status.ACTIVE,
    )


def repoint_missing_users(obj, owner) -> list[str]:
    """Fix user references that only exist in production. Returns what it did."""
    notes = []
    for field in obj._meta.fields:
        if not (field.is_relation and field.related_model is User):
            continue
        raw_pk = getattr(obj, field.attname)
        if not raw_pk or User.objects.filter(pk=raw_pk).exists():
            continue
        if field.null:
            setattr(obj, field.attname, None)
            notes.append(f"{field.name}: dropped (no such user locally)")
        else:
            setattr(obj, field.attname, owner.pk)
            notes.append(f"{field.name}: repointed to {MIRROR_OWNER_EMAIL}")
    return notes


def reset_sequences(models) -> None:
    """Advance Postgres sequences past the highest mirrored primary key."""
    statements = connection.ops.sequence_reset_sql(no_style(), models)
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


class Command(BaseCommand):
    help = "Replace the club content tables with a dumpdata JSON payload (stdin or --file)."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="-", help="dumpdata JSON; '-' reads stdin.")

    @transaction.atomic
    def handle(self, *args, **options):
        raw = sys.stdin.read() if options["file"] == "-" else Path(options["file"]).read_text()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CommandError(f"payload is not valid JSON: {exc}") from exc
        if not isinstance(payload, list) or not payload:
            raise CommandError("payload is not a non-empty dumpdata list.")

        cleared = []
        for label in CONTENT_MODELS:
            deleted, _ = django_apps.get_model(label).objects.all().delete()
            cleared.append((label, deleted))

        owner = mirror_owner()
        loaded: dict[str, int] = {}
        repointed = []
        # deserialize wants the raw JSON text, not the parsed list.
        for item in deserialize("json", raw):
            obj = item.object
            label = obj._meta.label  # "courts.Court", matching CONTENT_MODELS
            notes = repoint_missing_users(obj, owner)
            if notes:
                repointed.append(f"  {label} pk={obj.pk}: " + "; ".join(notes))
            obj.save()
            loaded[label] = loaded.get(label, 0) + 1

        reset_sequences([django_apps.get_model(label) for label in CONTENT_MODELS])

        self.stdout.write("loaded:")
        for label in CONTENT_MODELS:
            if label in loaded:
                self.stdout.write(f"  {label:34s} {loaded[label]}")
        if repointed:
            self.stdout.write("user references fixed:")
            self.stdout.write("\n".join(repointed))
        self.stdout.write(self.style.SUCCESS(f"mirror loaded: {sum(loaded.values())} rows"))
