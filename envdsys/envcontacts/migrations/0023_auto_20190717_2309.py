# Generated by Django 2.2.1 on 2019-07-17 23:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0022_auto_20190717_2303'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('O', 'Other'), ('M', 'Mobile'), ('W', 'Work'), ('H', 'Home')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('O', 'Other'), ('M', 'Mobile'), ('W', 'Work'), ('H', 'Home')], default='M', max_length=1),
        ),
    ]