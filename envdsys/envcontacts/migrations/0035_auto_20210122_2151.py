# Generated by Django 3.1.5 on 2021-01-22 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0034_auto_20210122_2149'),
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
            field=models.CharField(choices=[('M', 'Mobile'), ('W', 'Work'), ('O', 'Other'), ('H', 'Home')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('W', 'Work'), ('O', 'Other'), ('H', 'Home')], default='M', max_length=1),
        ),
    ]
