# Generated by Django 3.1.7 on 2021-02-27 19:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('envdatasystem', '0012_auto_20210227_1908'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='controllercomponentinstrument',
            name='instrument',
        ),
    ]
