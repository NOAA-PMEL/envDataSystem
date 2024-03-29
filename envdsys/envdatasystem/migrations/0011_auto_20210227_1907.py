# Generated by Django 3.1.7 on 2021-02-27 19:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0010_auto_20210227_1855'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='controllercomponentinstrument',
            name='controller',
        ),
        migrations.RemoveField(
            model_name='instrumentcomponentinterface',
            name='instrument',
        ),
        migrations.AddField(
            model_name='controllercomponentinstrument',
            name='instrument',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='controllercomponentinstrument_instrument', to='envdatasystem.instrumentsystem', verbose_name='Instrument'),
        ),
        migrations.AddField(
            model_name='instrumentcomponentinterface',
            name='interface',
            field=models.CharField(default='default_interface', max_length=100, verbose_name='Interface'),
        ),
    ]
