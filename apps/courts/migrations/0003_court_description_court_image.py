from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courts', '0002_courtschedule_chk_schedule_time_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='court',
            name='description',
            field=models.TextField(blank=True, default='', help_text='Descripcion de la cancha visible para los clientes'),
        ),
        migrations.AddField(
            model_name='court',
            name='image',
            field=models.ImageField(blank=True, help_text='Foto de la cancha', null=True, upload_to='courts/%Y/%m/'),
        ),
    ]
