# Generated by Django 3.1.5 on 2021-02-19 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envnet', '0006_auto_20210219_2002'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='active',
            field=models.BooleanField(default=False, verbose_name='Active network'),
        ),
    ]