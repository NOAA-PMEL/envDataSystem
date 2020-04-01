# Generated by Django 2.2.1 on 2020-03-26 17:17

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('envtags', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('long_name', models.CharField(blank=True, max_length=100)),
                ('acronym', models.CharField(blank=True, max_length=20)),
                ('description', models.TextField(blank=True)),
                ('start_datetime', models.DateTimeField(verbose_name='Start DateTime')),
                ('stop_datetime', models.DateTimeField(blank=True, null=True, verbose_name='Stop DateTime')),
                ('uniqueID', models.UUIDField(default=uuid.uuid1, editable=False)),
                ('tags', models.ManyToManyField(blank=True, related_name='project_tags', to='envtags.Tag')),
            ],
            options={
                'verbose_name_plural': 'Projects',
            },
        ),
    ]
