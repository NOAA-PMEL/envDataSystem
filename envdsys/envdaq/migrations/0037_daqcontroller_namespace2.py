# Generated by Django 3.1.7 on 2021-05-25 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0036_auto_20210521_1905'),
    ]

    operations = [
        migrations.AddField(
            model_name='daqcontroller',
            name='namespace2',
            field=models.JSONField(blank=True, default=dict, verbose_name='NamespaceJSON'),
        ),
    ]
