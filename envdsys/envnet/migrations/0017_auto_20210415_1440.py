# Generated by Django 3.1.7 on 2021-04-15 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envnet', '0016_daqregistration_config2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='daqregistration',
            name='config2',
            field=models.JSONField(default=None),
        ),
    ]