# Generated by Django 3.1.7 on 2021-02-26 21:54

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0006_controllerdef_component_map'),
        ('envdatasystem', '0004_auto_20210226_1849'),
    ]

    operations = [
        migrations.CreateModel(
            name='DAQSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True, verbose_name='Name')),
                ('daq_host', models.GenericIPAddressField(blank=True, null=True, verbose_name='DAQ Server address')),
                ('daq_namespace', models.CharField(default='default', max_length=20, verbose_name='DAQ Namespace')),
                ('daq_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('data_system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.datasystem', verbose_name='Data System')),
            ],
            options={
                'verbose_name': 'DAQSystem',
                'verbose_name_plural': 'DAQSystems',
            },
        ),
        migrations.CreateModel(
            name='ControllerSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('controller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='envdaq.controller', verbose_name='Controller')),
            ],
            options={
                'verbose_name': 'Controller System',
                'verbose_name_plural': 'Controller Systems',
            },
        ),
    ]
