# Generated by Django 3.1.7 on 2021-02-27 19:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0014_delete_controllercomponentinstrument'),
    ]

    operations = [
        migrations.CreateModel(
            name='ControllerComponentInstrument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary', models.BooleanField(default=False, verbose_name='Primary Component')),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='controllercomponentinstrument_component', to='envdatasystem.controllercomponent', verbose_name='Component')),
                ('instrument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='controllercomponentinstrument_instrument', to='envdatasystem.instrumentsystem', verbose_name='Instrument')),
            ],
            options={
                'verbose_name': 'ControllerComponent Instrument',
                'verbose_name_plural': 'ControllerComponent Instruments',
            },
        ),
    ]
