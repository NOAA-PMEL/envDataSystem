# Generated by Django 2.1.5 on 2019-02-15 23:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0007_auto_20190215_2300'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='devicedef',
            name='contacts',
        ),
        migrations.RemoveField(
            model_name='instrumentdef',
            name='measurements',
        ),
    ]
