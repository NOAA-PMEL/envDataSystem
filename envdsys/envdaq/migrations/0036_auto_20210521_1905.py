# Generated by Django 3.1.7 on 2021-05-21 19:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envtags', '0002_auto_20210122_2145'),
        ('envdaq', '0035_auto_20210521_1902'),
    ]

    operations = [
        migrations.AddField(
            model_name='daqserver',
            name='configuration',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='configurations', to='envtags.configuration'),
        ),
        migrations.AddField(
            model_name='daqserver',
            name='daq_config',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='envdaq.daqserverconfig', verbose_name='DAQServer Config'),
        ),
    ]
