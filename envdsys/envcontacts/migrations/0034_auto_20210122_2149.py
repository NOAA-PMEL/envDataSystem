# Generated by Django 3.1.5 on 2021-01-22 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0033_auto_20210122_2146'),
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
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('H', 'Home'), ('M', 'Mobile'), ('O', 'Other'), ('W', 'Work')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('H', 'Home'), ('M', 'Mobile'), ('O', 'Other'), ('W', 'Work')], default='M', max_length=1),
        ),
    ]