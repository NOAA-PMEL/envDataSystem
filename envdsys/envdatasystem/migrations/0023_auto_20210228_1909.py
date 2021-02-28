# Generated by Django 3.1.7 on 2021-02-28 19:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0022_auto_20210228_1904'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='samplingsystemmap',
            options={'verbose_name': 'Sampling System Map', 'verbose_name_plural': 'Sampling System Maps'},
        ),
        migrations.AddField(
            model_name='samplingsystemmap',
            name='sampling_system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='envdatasystem.samplingsystem', verbose_name='Sampling System'),
        ),
    ]
