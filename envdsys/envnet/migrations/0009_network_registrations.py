# Generated by Django 3.1.7 on 2021-02-19 21:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envnet', '0008_auto_20210219_2127'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='registrations',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='envnet.serviceregistration'),
        ),
    ]