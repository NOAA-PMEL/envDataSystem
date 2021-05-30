# Generated by Django 3.1.7 on 2021-05-10 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0122_auto_20210503_1627'),
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
            field=models.CharField(choices=[('M', 'Mobile'), ('W', 'Work'), ('H', 'Home'), ('O', 'Other')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('M', 'Mobile'), ('W', 'Work'), ('H', 'Home'), ('O', 'Other')], default='M', max_length=1),
        ),
    ]
