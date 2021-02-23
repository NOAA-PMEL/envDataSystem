# Generated by Django 3.1.5 on 2021-02-19 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0046_auto_20210219_2009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email1_type',
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('H', 'Home')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='email2_type',
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('H', 'Home')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('O', 'Other'), ('W', 'Work'), ('H', 'Home')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('O', 'Other'), ('W', 'Work'), ('H', 'Home')], default='M', max_length=1),
        ),
    ]
