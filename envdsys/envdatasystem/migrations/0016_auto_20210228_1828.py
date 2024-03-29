# Generated by Django 3.1.7 on 2021-02-28 18:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0006_controllerdef_component_map'),
        ('envdatasystem', '0015_controllercomponentinstrument'),
    ]

    operations = [
        migrations.CreateModel(
            name='SSMPlatform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'SSMPlatform',
                'verbose_name_plural': 'SSMPlatforms',
            },
        ),
        migrations.RemoveField(
            model_name='samplingsystem',
            name='locations',
        ),
        migrations.RemoveField(
            model_name='samplingsystem',
            name='sample_points',
        ),
        migrations.AddField(
            model_name='samplingsystemlocation',
            name='sampling_system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sslocations_samplingsystem', to='envdatasystem.samplingsystem', verbose_name='Sampling System'),
        ),
        migrations.AddField(
            model_name='samplingsystemsamplepoint',
            name='sampling_system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sssamplepoints_samplingsystem', to='envdatasystem.samplingsystem', verbose_name='Sample System'),
        ),
        migrations.AlterField(
            model_name='controllersystem',
            name='controller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='controllersystem_controllers', to='envdaq.controller', verbose_name='Controller'),
        ),
        migrations.AlterField(
            model_name='controllersystem',
            name='daq',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='controllersystem_daqs', to='envdatasystem.daqsystem', verbose_name='DAQ System'),
        ),
        migrations.AlterField(
            model_name='controllersystem',
            name='parent_controller',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='controllersystem_parentcontrollers', to='envdatasystem.controllersystem', verbose_name='Parent Controller'),
        ),
        migrations.AlterField(
            model_name='daqsystem',
            name='data_system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daqsystem_datasystems', to='envdatasystem.datasystem', verbose_name='Data System'),
        ),
        migrations.AlterField(
            model_name='datasystem',
            name='platform',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='datasystems_platform', to='envdatasystem.platform', verbose_name='Platform'),
        ),
        migrations.AlterField(
            model_name='datasystem',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='datasystems_project', to='envdatasystem.project', verbose_name='Project'),
        ),
        migrations.AlterField(
            model_name='samplingsystemlocation',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sslocations_parent', to='envdatasystem.samplingsystemlocation', verbose_name='Parent Location'),
        ),
        migrations.AlterField(
            model_name='samplingsystemsamplepoint',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='samplepoint_parents', to='envdatasystem.samplingsystemsamplepoint', verbose_name='Parent Sampling Point'),
        ),
        migrations.CreateModel(
            name='SamplingSystemMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ssm_platform', to='envdatasystem.platform', verbose_name='Platform')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ssm_project', to='envdatasystem.project', verbose_name='Project')),
            ],
            options={
                'verbose_name': 'samplingsystemmap',
                'verbose_name_plural': 'samplingsystemmaps',
            },
        ),
    ]
