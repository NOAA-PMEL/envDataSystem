# Generated by Django 2.2.1 on 2020-03-26 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envproject', '0002_auto_20200326_1744'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='projects/', verbose_name='Logo Image'),
        ),
    ]