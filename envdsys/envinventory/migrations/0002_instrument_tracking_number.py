# Generated by Django 3.1.7 on 2021-05-21 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envinventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument',
            name='tracking_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Tracking Number'),
        ),
    ]