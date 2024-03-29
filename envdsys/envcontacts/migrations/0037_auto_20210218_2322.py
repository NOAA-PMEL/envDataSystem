# Generated by Django 3.1.5 on 2021-02-18 23:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0036_auto_20210218_2155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('O', 'Other'), ('H', 'Home'), ('W', 'Work'), ('M', 'Mobile')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('O', 'Other'), ('H', 'Home'), ('W', 'Work'), ('M', 'Mobile')], default='M', max_length=1),
        ),
    ]
