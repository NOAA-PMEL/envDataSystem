# Generated by Django 3.1.5 on 2021-02-19 01:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0039_auto_20210219_0112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email1_type',
            field=models.CharField(choices=[('W', 'Work'), ('O', 'Other'), ('H', 'Home')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='email2_type',
            field=models.CharField(choices=[('W', 'Work'), ('O', 'Other'), ('H', 'Home')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('M', 'Mobile'), ('H', 'Home')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('M', 'Mobile'), ('H', 'Home')], default='M', max_length=1),
        ),
    ]
