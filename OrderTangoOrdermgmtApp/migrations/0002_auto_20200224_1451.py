# Generated by Django 2.0.2 on 2020-02-24 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OrderTangoOrdermgmtApp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderplacementtosupplier',
            name='orderType',
        ),
        migrations.RemoveField(
            model_name='pdfdetailsforplacedorder',
            name='supplierId',
        ),
        migrations.RemoveField(
            model_name='shoppingcart',
            name='cartStatus',
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='status',
            field=models.CharField(default='Pending', max_length=50),
        ),
    ]