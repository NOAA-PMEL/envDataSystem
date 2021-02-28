# Generated by Django 3.1.7 on 2021-02-27 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0081_auto_20210227_1910'),
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
            field=models.CharField(choices=[('O', 'Other'), ('H', 'Home'), ('M', 'Mobile'), ('W', 'Work')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('O', 'Other'), ('H', 'Home'), ('M', 'Mobile'), ('W', 'Work')], default='M', max_length=1),
        ),
    ]