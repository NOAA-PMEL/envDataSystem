# Generated by Django 2.2.1 on 2020-03-27 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0018_auto_20200327_2043'),
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
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('H', 'Home'), ('M', 'Mobile')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('H', 'Home'), ('M', 'Mobile')], default='M', max_length=1),
        ),
    ]
