# Generated by Django 3.2.3 on 2021-07-18 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0064_auto_20210718_1854'),
    ]

    operations = [
        migrations.AddField(
            model_name='samplingsystemdataset',
            name='current',
            field=models.BooleanField(default=True, verbose_name='Current Dataset'),
        ),
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('MOORING', 'Mooring'), ('STATION', 'Station/Lab'), ('UAS', 'UAS'), ('AIRCRAFT', 'Aircraft'), ('SHIP', 'Ship')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
    ]
