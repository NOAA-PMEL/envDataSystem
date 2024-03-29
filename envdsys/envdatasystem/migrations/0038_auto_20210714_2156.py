# Generated by Django 3.2.3 on 2021-07-14 21:56

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('envtags', '0002_auto_20210122_2145'),
        ('envdatasystem', '0037_auto_20210712_2129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platform',
            name='platform_type',
            field=models.CharField(choices=[('UAS', 'UAS'), ('SHIP', 'Ship'), ('STATION', 'Station/Lab'), ('AIRCRAFT', 'Aircraft'), ('MOORING', 'Mooring')], default='STATION', max_length=10, verbose_name='Platform Type'),
        ),
        migrations.AlterField(
            model_name='samplingsystem',
            name='data_system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.datasystem', verbose_name='Data System'),
        ),
        migrations.CreateModel(
            name='ProjectEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eventType', models.CharField(blank=True, max_length=50, null=True, verbose_name='Event Type')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('eventID', models.UUIDField(default=uuid.uuid1, editable=False)),
                ('updated', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Updated')),
                ('start_datetime', models.DateTimeField(verbose_name='Start DateTime')),
                ('stop_datetime', models.DateTimeField(blank=True, null=True, verbose_name='Stop DateTime')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.project', verbose_name='Project')),
                ('tags', models.ManyToManyField(blank=True, to='envtags.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'projectevent',
                'verbose_name_plural': 'projectevents',
            },
        ),
        migrations.CreateModel(
            name='PlatformEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eventType', models.CharField(blank=True, max_length=50, null=True, verbose_name='Event Type')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('eventID', models.UUIDField(default=uuid.uuid1, editable=False)),
                ('updated', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Updated')),
                ('start_datetime', models.DateTimeField(verbose_name='Start DateTime')),
                ('stop_datetime', models.DateTimeField(blank=True, null=True, verbose_name='Stop DateTime')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.platform', verbose_name='Platform')),
                ('tags', models.ManyToManyField(blank=True, to='envtags.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'PlatformEvent',
                'verbose_name_plural': 'PlatformEvents',
            },
        ),
    ]
