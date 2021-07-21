# Generated by Django 3.2.3 on 2021-07-12 21:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0036_auto_20210712_2126'),
    ]

    operations = [
        migrations.AddField(
            model_name='samplingsystem',
            name='data_system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.datasystem', verbose_name=''),
        ),
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('STATION', 'Station/Lab'), ('UAS', 'UAS'), ('MOORING', 'Mooring'), ('AIRCRAFT', 'Aircraft'), ('SHIP', 'Ship')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
    ]