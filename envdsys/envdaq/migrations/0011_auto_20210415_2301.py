# Generated by Django 3.1.7 on 2021-04-15 23:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0010_auto_20210415_2247'),
    ]

    operations = [
        migrations.AddField(
            model_name='interface',
            name='host_path',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Host Path/Device'),
        ),
        migrations.AddField(
            model_name='interface',
            name='host_port',
            field=models.IntegerField(blank=True, null=True, verbose_name='Host Port'),
        ),
    ]