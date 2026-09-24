from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("policies", "0002_cancellationpolicy_uniq_venue_cancellation_policy"),
    ]

    operations = [
        migrations.AddField(
            model_name="cancellationpolicy",
            name="max_holds_per_user",
            field=models.PositiveIntegerField(default=5),
        ),
    ]
