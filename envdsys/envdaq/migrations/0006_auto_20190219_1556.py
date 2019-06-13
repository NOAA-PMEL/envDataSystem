# Generated by Django 2.1.5 on 2019-02-19 15:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('envdaq', '0005_person_affiliation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instrument',
            name='definition',
        ),
        migrations.RemoveField(
            model_name='instrument',
            name='instrument_mask',
        ),
        migrations.RemoveField(
            model_name='person',
            name='affiliation',
        ),
        migrations.DeleteModel(
            name='Instrument',
        ),
        migrations.DeleteModel(
            name='InstrumentDef',
        ),
        migrations.DeleteModel(
            name='Organization',
        ),
        migrations.DeleteModel(
            name='Person',
        ),
    ]