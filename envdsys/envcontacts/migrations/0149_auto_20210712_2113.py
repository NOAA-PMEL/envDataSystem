# Generated by Django 3.2.3 on 2021-07-12 21:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0148_auto_20210712_2047'),
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
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('H', 'Home'), ('M', 'Mobile')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('H', 'Home'), ('M', 'Mobile')], default='M', max_length=1),
        ),
    ]