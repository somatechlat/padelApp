from django.db import migrations, models


def set_default_category(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    Event.objects.filter(category='').update(category='quedada')


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_tournament_chk_tournament_date_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='category',
            field=models.CharField(
                choices=[
                    ('quedada', 'Quedada'),
                    ('torneo', 'Torneo'),
                    ('liga', 'Liga'),
                    ('academia', 'Academia'),
                    ('noticia', 'Noticia'),
                ],
                default='quedada',
                max_length=10,
            ),
        ),
        migrations.RunPython(set_default_category, migrations.RunPython.noop),
    ]
