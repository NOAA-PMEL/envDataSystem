# Generated by Django 3.1.7 on 2021-04-26 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0109_auto_20210426_2136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email1_type',
            field=models.CharField(choices=[('W', 'Work'), ('H', 'Home'), ('O', 'Other')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='email2_type',
            field=models.CharField(choices=[('W', 'Work'), ('H', 'Home'), ('O', 'Other')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('W', 'Work'), ('H', 'Home'), ('M', 'Mobile'), ('O', 'Other')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('W', 'Work'), ('H', 'Home'), ('M', 'Mobile'), ('O', 'Other')], default='M', max_length=1),
        ),
    ]