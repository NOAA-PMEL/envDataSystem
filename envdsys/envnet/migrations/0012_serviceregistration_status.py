# Generated by Django 3.1.7 on 2021-02-19 23:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envnet', '0011_serviceregistration_network'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceregistration',
            name='status',
            field=models.CharField(default='UNKNOWN', max_length=50, verbose_name='Status'),
        ),
    ]
