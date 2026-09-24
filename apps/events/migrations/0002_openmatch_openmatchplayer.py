import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_skilllevel_user_birth_date_user_first_name_and_more"),
        ("events", "0004_event_category"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpenMatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("start_time", models.TimeField()),
                ("duration_minutes", models.PositiveIntegerField(default=90)),
                ("max_players", models.PositiveIntegerField(default=4)),
                ("notes", models.CharField(blank=True, max_length=280)),
                ("status", models.CharField(choices=[("open", "Abierto"), ("full", "Completo"), ("cancelled", "Cancelado")], default="open", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="open_matches_created", to=settings.AUTH_USER_MODEL)),
                ("skill_level", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="open_matches", to="users.skilllevel")),
            ],
            options={
                "verbose_name": "partido abierto",
                "verbose_name_plural": "partidos abiertos",
                "ordering": ("date", "start_time"),
            },
        ),
        migrations.CreateModel(
            name="OpenMatchPlayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("match", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="players", to="events.openmatch")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="open_match_players", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "jugador de partido",
                "verbose_name_plural": "jugadores de partido",
                "constraints": [models.UniqueConstraint(fields=("match", "user"), name="uniq_openmatch_user")],
            },
        ),
    ]
