# Generated by Django 3.1.7 on 2021-05-21 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0133_auto_20210519_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('O', 'Other'), ('H', 'Home'), ('W', 'Work')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('O', 'Other'), ('H', 'Home'), ('W', 'Work')], default='M', max_length=1),
        ),
    ]