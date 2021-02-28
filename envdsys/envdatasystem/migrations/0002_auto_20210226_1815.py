# Generated by Django 3.1.7 on 2021-02-26 18:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SamplingSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('long_name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'samplingsystem',
                'verbose_name_plural': 'samplingsystems',
            },
        ),
        migrations.AlterField(
            model_name='datasystem',
            name='platform',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.platform', verbose_name='Platform'),
        ),
        migrations.CreateModel(
            name='SamplingSystemSamplePoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('long_name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.samplingsystemsamplepoint', verbose_name='')),
                ('sampling_system', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.samplingsystem', verbose_name='Sampling System')),
            ],
            options={
                'verbose_name': 'SamplingSystemSamplePoint',
                'verbose_name_plural': 'SamplingSystemSamplePoints',
            },
        ),
        migrations.CreateModel(
            name='SamplingSystemLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('long_name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.samplingsystemlocation', verbose_name='')),
                ('sampling_system', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.samplingsystem', verbose_name='Sampling System')),
            ],
            options={
                'verbose_name': 'SamplingSystemLocation',
                'verbose_name_plural': 'SamplingSystemLocations',
            },
        ),
        migrations.AddField(
            model_name='samplingsystem',
            name='locations',
            field=models.ManyToManyField(blank=True, to='envdatasystem.SamplingSystemLocation', verbose_name=''),
        ),
        migrations.AddField(
            model_name='samplingsystem',
            name='sample_points',
            field=models.ManyToManyField(blank=True, to='envdatasystem.SamplingSystemSamplePoint', verbose_name=''),
        ),
    ]
