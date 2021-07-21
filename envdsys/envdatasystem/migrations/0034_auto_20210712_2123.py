# Generated by Django 3.2.3 on 2021-07-12 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0033_auto_20210712_2120'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasystem',
            name='projects',
            field=models.ManyToManyField(blank=True, to='envdatasystem.Project', verbose_name='Project List'),
        ),
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('MOORING', 'Mooring'), ('STATION', 'Station/Lab'), ('AIRCRAFT', 'Aircraft'), ('SHIP', 'Ship'), ('UAS', 'UAS')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
    ]