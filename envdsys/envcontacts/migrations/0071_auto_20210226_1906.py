# Generated by Django 3.1.7 on 2021-02-26 19:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0070_auto_20210226_1849'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email1_type',
            field=models.CharField(choices=[('H', 'Home'), ('O', 'Other'), ('W', 'Work')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='email2_type',
            field=models.CharField(choices=[('H', 'Home'), ('O', 'Other'), ('W', 'Work')], default='W', max_length=1),
        ),
    ]
