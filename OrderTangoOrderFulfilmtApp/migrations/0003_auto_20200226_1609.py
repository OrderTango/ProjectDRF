# Generated by Django 2.0.2 on 2020-02-26 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OrderTangoOrderFulfilmtApp', '0002_auto_20200224_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderplacementfromcustomer',
            name='customer_postalCode',
            field=models.CharField(max_length=7),
        ),
    ]
