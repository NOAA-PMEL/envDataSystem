# Generated by Django 3.1.7 on 2021-05-02 23:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0116_auto_20210501_0005'),
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
            field=models.CharField(choices=[('W', 'Work'), ('O', 'Other'), ('H', 'Home'), ('M', 'Mobile')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('W', 'Work'), ('O', 'Other'), ('H', 'Home'), ('M', 'Mobile')], default='M', max_length=1),
        ),
    ]
