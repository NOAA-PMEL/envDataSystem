# Generated by Django 3.1.7 on 2021-05-02 23:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0018_auto_20210501_0005'),
    ]

    operations = [
        migrations.AddField(
            model_name='daqserver',
            name='namespace',
            field=models.CharField(default='localhost-default', max_length=100, verbose_name='Namespace'),
        ),
        migrations.AlterField(
            model_name='daqcontroller',
            name='name',
            field=models.CharField(help_text='Short, descriptive name to be used as id in urls, paths, etc (<b>no whitespace</b>)', max_length=50, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='daqcontroller',
            name='server',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='envdaq.daqserver', verbose_name='DAQ Server'),
        ),
        migrations.AlterField(
            model_name='daqinstrument',
            name='controller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='envdaq.daqcontroller', verbose_name='Controller'),
        ),
    ]
