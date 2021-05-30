# Generated by Django 3.1.7 on 2021-05-17 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0030_auto_20210517_2059'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instrumentcomponent',
            name='controller',
        ),
        migrations.RemoveField(
            model_name='instrumentcomponent',
            name='parent',
        ),
        migrations.AddField(
            model_name='daqcontroller',
            name='component',
            field=models.CharField(default='default', max_length=100, verbose_name='Component Name'),
        ),
        migrations.AddField(
            model_name='daqcontroller',
            name='primary_component',
            field=models.BooleanField(default=False, verbose_name='Primary Component'),
        ),
        migrations.AddField(
            model_name='daqinstrument',
            name='component',
            field=models.CharField(default='default', max_length=100, verbose_name='Component Name'),
        ),
        migrations.AddField(
            model_name='daqinstrument',
            name='primary_component',
            field=models.BooleanField(default=False, verbose_name='Primary Component'),
        ),
        migrations.DeleteModel(
            name='ControllerComponent',
        ),
        migrations.DeleteModel(
            name='InstrumentComponent',
        ),
    ]
