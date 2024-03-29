# Generated by Django 3.2.3 on 2021-07-15 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0047_alter_platform_platform_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('STATION', 'Station/Lab'), ('UAS', 'UAS'), ('SHIP', 'Ship'), ('AIRCRAFT', 'Aircraft'), ('MOORING', 'Mooring')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
    ]
