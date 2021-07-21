# Generated by Django 3.2.3 on 2021-07-16 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0052_alter_platform_platform_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('UAS', 'UAS'), ('AIRCRAFT', 'Aircraft'), ('MOORING', 'Mooring'), ('SHIP', 'Ship'), ('STATION', 'Station/Lab')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
    ]