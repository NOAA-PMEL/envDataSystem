# Generated by Django 2.1.5 on 2019-02-15 23:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='controllerdef',
            name='test',
        ),
    ]