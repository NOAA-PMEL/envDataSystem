# Generated by Django 2.2.1 on 2020-03-27 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envproject', '0006_auto_20200327_1742'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=20, verbose_name='Short Name / Acronym'),
        ),
    ]