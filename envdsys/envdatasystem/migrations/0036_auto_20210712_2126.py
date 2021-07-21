# Generated by Django 3.2.3 on 2021-07-12 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0035_auto_20210712_2124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasystem',
            name='projects',
            field=models.ManyToManyField(blank=True, to='envdatasystem.Project', verbose_name='Project List'),
        ),
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('UAS', 'UAS'), ('MOORING', 'Mooring'), ('STATION', 'Station/Lab'), ('SHIP', 'Ship'), ('AIRCRAFT', 'Aircraft')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
    ]