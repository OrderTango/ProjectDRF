# Generated by Django 2.1.2 on 2019-10-29 19:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('OrderTangoSubDomainApp', '0001_initial'),
        ('OrderTangoApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderDetails',
            fields=[
                ('ordDetailId', models.AutoField(primary_key=True, serialize=False)),
                ('itemCode', models.CharField(max_length=50)),
                ('itemName', models.CharField(max_length=50)),
                ('itemCategory', models.CharField(default='uncategorized', max_length=50)),
                ('quantity', models.CharField(max_length=50)),
                ('actualQuantity', models.CharField(max_length=50, null=True)),
                ('price', models.CharField(max_length=50)),
                ('ordstatus', models.CharField(default='Pending', max_length=50)),
                ('comment', models.TextField()),
                ('goodsIssue', models.CharField(max_length=50)),
                ('goodsReceive', models.CharField(max_length=50)),
                ('pickUpList', models.CharField(max_length=50)),
                ('status', models.CharField(default='Active', max_length=50)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'OrderDetails',
            },
        ),
        migrations.CreateModel(
            name='OrderPlacementfromCustomer',
            fields=[
                ('ordFrmCusId', models.AutoField(primary_key=True, serialize=False)),
                ('ordNumber', models.CharField(max_length=255)),
                ('totalQuantity', models.CharField(max_length=50, null=True)),
                ('totalPrice', models.CharField(default='0', max_length=50)),
                ('totalPriceUnit', models.CharField(default='USD', max_length=50)),
                ('ordstatus', models.CharField(default='Pending', max_length=50)),
                ('customer_address_Line1', models.CharField(max_length=100)),
                ('customer_address_Line2', models.CharField(max_length=100)),
                ('customer_unit1', models.CharField(max_length=2)),
                ('customer_unit2', models.CharField(max_length=2)),
                ('customer_postalCode', models.CharField(max_length=7)),
                ('expectedDate', models.CharField(max_length=50)),
                ('expectedTime', models.CharField(max_length=50)),
                ('orderDate', models.DateField()),
                ('pdfField', models.BinaryField(null=True)),
                ('connectedStatus', models.BooleanField(default=False)),
                ('status', models.CharField(default='Active', max_length=50)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('customerId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='OrderTangoSubDomainApp.Customer')),
                ('customer_country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.Country')),
                ('customer_state', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.State')),
                ('siteId', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoSubDomainApp.Sites')),
            ],
            options={
                'db_table': 'OrderPlacementfromCustomer',
            },
        ),
        migrations.AddField(
            model_name='orderdetails',
            name='ordNumber',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orderdetail', to='OrderTangoOrderFulfilmtApp.OrderPlacementfromCustomer'),
        ),
        migrations.AddField(
            model_name='orderdetails',
            name='priceUnit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='OrderTangoApp.CurrencyType'),
        ),
        migrations.AddField(
            model_name='orderdetails',
            name='uOm',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='OrderTangoApp.QuantityType'),
        ),
    ]
