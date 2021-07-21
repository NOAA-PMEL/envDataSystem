# Generated by Django 3.2.3 on 2021-07-19 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0066_auto_20210718_1922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('MOORING', 'Mooring'), ('UAS', 'UAS'), ('AIRCRAFT', 'Aircraft'), ('SHIP', 'Ship'), ('STATION', 'Station/Lab')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
    ]