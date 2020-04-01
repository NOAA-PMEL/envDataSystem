# Generated by Django 2.2.1 on 2020-03-27 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envproject', '0004_auto_20200326_2238'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='event_type',
            field=models.CharField(default='GENERIC', max_length=50),
        ),
        migrations.AlterField(
            model_name='project',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='event_tags', to='envtags.Tag'),
        ),
    ]
