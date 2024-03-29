# Generated by Django 3.1.7 on 2021-04-16 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0011_auto_20210415_2301'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interface',
            name='host_ip',
        ),
        migrations.RemoveField(
            model_name='interface',
            name='host_name',
        ),
        migrations.RemoveField(
            model_name='interface',
            name='host_path',
        ),
        migrations.RemoveField(
            model_name='interface',
            name='host_port',
        ),
        migrations.AddField(
            model_name='interface',
            name='uri',
            field=models.CharField(default='localhost:10001', help_text='In the form of <host>:<path> where host is name or ip address and path is port number, device path, etc', max_length=100, verbose_name='URI'),
        ),
    ]
