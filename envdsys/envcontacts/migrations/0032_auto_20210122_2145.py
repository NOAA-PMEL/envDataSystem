# Generated by Django 3.1.5 on 2021-01-22 21:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0031_auto_20210122_2145'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email1_type',
            field=models.CharField(choices=[('H', 'Home'), ('O', 'Other'), ('W', 'Work')], default='W', max_length=10),
        ),
        migrations.AlterField(
            model_name='person',
            name='email2_type',
            field=models.CharField(choices=[('H', 'Home'), ('O', 'Other'), ('W', 'Work')], default='W', max_length=10),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('H', 'Home'), ('O', 'Other'), ('W', 'Work')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('H', 'Home'), ('O', 'Other'), ('W', 'Work')], default='M', max_length=1),
        ),
    ]
