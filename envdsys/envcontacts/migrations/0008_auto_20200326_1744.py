# Generated by Django 2.2.1 on 2020-03-26 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0007_auto_20200326_1717'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email1_type',
            field=models.CharField(choices=[('H', 'Home'), ('W', 'Work'), ('O', 'Other')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='email2_type',
            field=models.CharField(choices=[('H', 'Home'), ('W', 'Work'), ('O', 'Other')], default='W', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('H', 'Home'), ('W', 'Work'), ('O', 'Other')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('H', 'Home'), ('W', 'Work'), ('O', 'Other')], default='M', max_length=1),
        ),
    ]
