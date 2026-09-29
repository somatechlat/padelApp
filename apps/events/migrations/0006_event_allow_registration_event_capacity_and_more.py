# Renumbered from 0003_event_allow_registration_event_capacity_and_more
# (was a second "0003_*"). `replaces` keeps old database records resolving so
# a shared DB that already applied the old name is treated as applied without
# re-running.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    replaces = [
        ('events', '0003_event_allow_registration_event_capacity_and_more'),
    ]

    dependencies = [
        ('events', '0005_openmatch_openmatchplayer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='allow_registration',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='event',
            name='capacity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name='EventRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('going', 'Va a asistir'), ('cancelled', 'No asiste')], default='going', max_length=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='events.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_registrations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'inscripcion a evento',
                'verbose_name_plural': 'inscripciones a eventos',
                'constraints': [models.UniqueConstraint(fields=('event', 'user'), name='uniq_event_user')],
            },
        ),
    ]
