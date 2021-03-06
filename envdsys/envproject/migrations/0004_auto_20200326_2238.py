# Generated by Django 2.2.1 on 2020-03-26 22:38

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('envtags', '0001_initial'),
        ('envproject', '0003_auto_20200326_1754'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='acronym',
        ),
        migrations.AlterField(
            model_name='project',
            name='long_name',
            field=models.CharField(blank=True, max_length=200, verbose_name='Long Name'),
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=20, verbose_name='Short Name / Acronym'),
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('long_name', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(blank=True)),
                ('website', models.URLField(blank=True, null=True, verbose_name='Platform Website')),
                ('uniqueID', models.UUIDField(default=uuid.uuid1, editable=False)),
                ('tags', models.ManyToManyField(blank=True, related_name='platform_tags', to='envtags.Tag')),
            ],
            options={
                'verbose_name_plural': 'Platforms',
            },
        ),
    ]
