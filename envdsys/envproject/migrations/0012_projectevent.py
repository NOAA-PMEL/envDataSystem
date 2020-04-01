# Generated by Django 2.2.1 on 2020-03-27 22:03

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('envtags', '0001_initial'),
        ('envproject', '0011_auto_20200327_2201'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('start_datetime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Start DateTime')),
                ('stop_datetime', models.DateTimeField(blank=True, null=True, verbose_name='Stop DateTime')),
                ('uniqueID', models.UUIDField(default=uuid.uuid1, editable=False)),
                ('description', models.TextField(blank=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='envproject.Project')),
                ('tags', models.ManyToManyField(blank=True, related_name='envproject_projectevent_related', related_query_name='envproject_projectevents', to='envtags.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
