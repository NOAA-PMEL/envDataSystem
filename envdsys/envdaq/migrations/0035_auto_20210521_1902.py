# Generated by Django 3.1.7 on 2021-05-21 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0034_daqserver_autoenable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='daqserver',
            name='configuration',
        ),
        migrations.RemoveField(
            model_name='daqserver',
            name='daq_config',
        ),
        migrations.AlterField(
            model_name='daqserver',
            name='namespace2',
            field=models.JSONField(blank=True, default=dict, verbose_name='NamespaceJSON'),
        ),
    ]
