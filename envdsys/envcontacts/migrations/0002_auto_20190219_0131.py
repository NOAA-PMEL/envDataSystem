# Generated by Django 2.1.5 on 2019-02-19 01:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_address', models.CharField(blank=True, max_length=100, null=True)),
                ('city', models.CharField(blank=True, max_length=30, null=True)),
                ('state', models.CharField(blank=True, max_length=30, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True)),
                ('country', models.CharField(blank=True, max_length=30, null=True)),
                ('website', models.URLField()),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('parent_org', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='envcontacts.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_address', models.CharField(blank=True, max_length=100, null=True)),
                ('city', models.CharField(blank=True, max_length=30, null=True)),
                ('state', models.CharField(blank=True, max_length=30, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True)),
                ('country', models.CharField(blank=True, max_length=30, null=True)),
                ('website', models.URLField()),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('phone1', models.CharField(blank=True, max_length=15, null=True)),
                ('phone1_type', models.CharField(choices=[('M', 'Mobile'), ('H', 'Home'), ('O', 'Other'), ('W', 'Work')], default='M', max_length=1)),
                ('phone2', models.CharField(blank=True, max_length=15, null=True)),
                ('phone2_type', models.CharField(choices=[('M', 'Mobile'), ('H', 'Home'), ('O', 'Other'), ('W', 'Work')], default='M', max_length=1)),
                ('email1', models.EmailField(blank=True, max_length=254, null=True)),
                ('email1_type', models.CharField(choices=[('H', 'Home'), ('W', 'Work'), ('O', 'Other')], default='W', max_length=1)),
                ('email2', models.EmailField(blank=True, max_length=254, null=True)),
                ('email2_type', models.CharField(choices=[('H', 'Home'), ('W', 'Work'), ('O', 'Other')], default='W', max_length=1)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='envcontacts.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='contact',
            name='organization',
        ),
        migrations.DeleteModel(
            name='Contact',
        ),
    ]