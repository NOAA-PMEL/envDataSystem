# Generated by Django 2.1.5 on 2019-02-19 02:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0006_auto_20190219_0232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email1_type',
            field=models.CharField(choices=[('O', 'Other'), ('H', 'Home'), ('W', 'Work')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='email2_type',
            field=models.CharField(choices=[('O', 'Other'), ('H', 'Home'), ('W', 'Work')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('H', 'Home'), ('O', 'Other'), ('M', 'Mobile'), ('W', 'Work')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('H', 'Home'), ('O', 'Other'), ('M', 'Mobile'), ('W', 'Work')], default='M', max_length=1),
        ),
    ]
