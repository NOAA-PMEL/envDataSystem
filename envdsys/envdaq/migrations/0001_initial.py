# Generated by Django 2.2.1 on 2019-08-12 15:25

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('envinventory', '__first__'),
        ('envtags', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Controller',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('uniqueID', models.UUIDField(default=uuid.uuid1, editable=False)),
            ],
            options={
                'verbose_name_plural': 'Controllers',
            },
        ),
        migrations.CreateModel(
            name='FieldProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='test', max_length=50)),
                ('long_name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.CharField(blank=True, max_length=300, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('long_name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('units', models.CharField(blank=True, help_text='Enter units using UDUnits convention', max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='test', max_length=50)),
                ('long_name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.CharField(blank=True, max_length=300, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InstrumentAlias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Enter the name that describes what the instrument represents', max_length=30)),
                ('prefix', models.CharField(help_text='Short prefix to add to all measurements and signals. If blank, will use <name>', max_length=30, null=True)),
                ('controller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='controllers', to='envdaq.Controller')),
                ('instrument', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='instruments', to='envinventory.Instrument')),
                ('tags', models.ManyToManyField(blank=True, related_name='instrumentalias_tags', to='envtags.Tag')),
            ],
        ),
        migrations.CreateModel(
            name='DAQServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('uniqueID', models.UUIDField(default=uuid.uuid1, editable=False)),
                ('host', models.CharField(max_length=30, null=True)),
                ('ip_address', models.GenericIPAddressField(null=True)),
                ('port', models.IntegerField(null=True)),
                ('configuration', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='configurations', to='envtags.Configuration')),
                ('tags', models.ManyToManyField(blank=True, related_name='daqserver_tags', to='envtags.Tag')),
            ],
            options={
                'verbose_name': 'DAQ Server',
                'verbose_name_plural': 'DAQ Servers',
            },
        ),
        migrations.CreateModel(
            name='ControllerDef',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Enter Controller type name', max_length=30)),
                ('_class', models.CharField(help_text='Enter class name', max_length=30)),
                ('_module', models.CharField(help_text='Enter module name', max_length=50)),
                ('tags', models.ManyToManyField(blank=True, related_name='controllerdef_tags', to='envtags.Tag')),
            ],
            options={
                'verbose_name': 'Controller Definition',
                'verbose_name_plural': 'Controller Definitions',
            },
        ),
        migrations.AddField(
            model_name='controller',
            name='definition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='controllers', to='envdaq.ControllerDef'),
        ),
        migrations.AddField(
            model_name='controller',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='controller_tags', to='envtags.Tag'),
        ),
    ]
