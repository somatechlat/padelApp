from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courts", "0004_promobanner_venue_bank_account_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="venue",
            name="booking_alert_email",
            field=models.EmailField(
                blank=True,
                default="",
                help_text="Email que recibe aviso de cada nueva reserva",
                max_length=254,
            ),
        ),
        migrations.AddField(
            model_name="venue",
            name="booking_alert_push",
            field=models.BooleanField(
                default=True,
                help_text="Enviar push a los administradores en cada nueva reserva",
            ),
        ),
    ]
