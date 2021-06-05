# Generated by Django 3.1.7 on 2021-05-21 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('envcontacts', '0134_auto_20210521_1502'),
    ]

    operations = [
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