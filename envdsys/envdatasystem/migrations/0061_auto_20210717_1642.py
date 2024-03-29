# Generated by Django 3.2.3 on 2021-07-17 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0060_auto_20210717_1638'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DAQDataset',
            new_name='SamplingSystemDataset',
        ),
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('STATION', 'Station/Lab'), ('MOORING', 'Mooring'), ('UAS', 'UAS'), ('SHIP', 'Ship'), ('AIRCRAFT', 'Aircraft')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
    ]
