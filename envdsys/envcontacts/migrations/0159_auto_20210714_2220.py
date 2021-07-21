# Generated by Django 3.2.3 on 2021-07-14 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0158_auto_20210714_2218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='phone1_type',
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('M', 'Mobile'), ('H', 'Home')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone2_type',
            field=models.CharField(choices=[('O', 'Other'), ('W', 'Work'), ('M', 'Mobile'), ('H', 'Home')], default='M', max_length=1),
        ),
    ]
