# Generated by Django 2.1.5 on 2019-02-14 21:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0004_instrument_serial_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstrumentMask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Enter the name that describes what the instrument represents', max_length=30)),
            ],
        ),
        migrations.RemoveField(
            model_name='controller',
            name='inst_list',
        ),
        migrations.RemoveField(
            model_name='instrument',
            name='name',
        ),
        migrations.AddField(
            model_name='instrument',
            name='nickname',
            field=models.CharField(default=None, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='controller',
            name='definition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='controllers', to='envdaq.ControllerDef'),
        ),
        migrations.AlterField(
            model_name='instrument',
            name='serial_number',
            field=models.CharField(default='NA', help_text='Enter serial number', max_length=30),
        ),
        migrations.AddField(
            model_name='instrumentmask',
            name='controller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instruments', to='envdaq.Controller'),
        ),
        migrations.AddField(
            model_name='instrument',
            name='instrument_mask',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='instrument', to='envdaq.InstrumentMask'),
        ),
    ]
