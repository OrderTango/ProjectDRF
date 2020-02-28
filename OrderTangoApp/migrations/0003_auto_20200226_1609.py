# Generated by Django 2.0.2 on 2020-02-26 16:09

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('OrderTangoApp', '0002_auto_20200224_1451'),
    ]

    operations = [
        migrations.CreateModel(
            name='addonFeatures',
            fields=[
                ('addonId', models.AutoField(primary_key=True, serialize=False)),
                ('categoryQty', models.FloatField()),
                ('purchasedPrice', models.FloatField()),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'addonFeatures',
            },
        ),
        migrations.CreateModel(
            name='addOnModule',
            fields=[
                ('addOnModuleId', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(default='Active', max_length=50)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'addOnModule',
            },
        ),
        migrations.CreateModel(
            name='BillingDetails',
            fields=[
                ('BillingDetailsId', models.AutoField(primary_key=True, serialize=False)),
                ('billingDate', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(max_length=100, null=True)),
                ('paymentMethod', models.CharField(max_length=50, null=True)),
                ('amount', models.CharField(max_length=100, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'billingDetails',
            },
        ),
        migrations.CreateModel(
            name='storageAllocation',
            fields=[
                ('storageListId', models.AutoField(primary_key=True, serialize=False)),
                ('storageListCode', models.CharField(max_length=50, null=True)),
                ('storageListName', models.CharField(max_length=50, null=True)),
                ('storageListDesc', models.CharField(max_length=50, null=True)),
                ('status', models.CharField(default='Active', max_length=50)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'storageAllocation',
            },
        ),
        migrations.CreateModel(
            name='storageSize',
            fields=[
                ('storageSizeId', models.AutoField(primary_key=True, serialize=False)),
                ('storageSizeCode', models.CharField(max_length=50, null=True)),
                ('storageSizeName', models.CharField(max_length=50, null=True)),
                ('storageSizeDesc', models.CharField(max_length=50, null=True)),
                ('storagePrice', models.FloatField(null=True)),
                ('status', models.CharField(default='Active', max_length=50)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('currencyType', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.CurrencyType')),
                ('storageAllocation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.storageAllocation')),
            ],
            options={
                'db_table': 'storageSize',
            },
        ),
        migrations.CreateModel(
            name='storageType',
            fields=[
                ('storageTypeId', models.AutoField(primary_key=True, serialize=False)),
                ('storageTypeCode', models.CharField(max_length=50, null=True)),
                ('storageTypeName', models.CharField(max_length=50, null=True)),
                ('storageTypeDesc', models.CharField(max_length=50, null=True)),
                ('status', models.CharField(default='Active', max_length=50)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'storageType',
            },
        ),
        migrations.CreateModel(
            name='upgradeFeatures',
            fields=[
                ('upgradeId', models.AutoField(primary_key=True, serialize=False)),
                ('modelName', models.CharField(max_length=50, null=True)),
                ('categoryDetail', models.CharField(max_length=50, null=True)),
                ('categoryPrice', models.FloatField()),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('categoryPriceUnit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.CurrencyType')),
            ],
            options={
                'db_table': 'upgradeFeatures',
            },
        ),
        migrations.RemoveField(
            model_name='basemodulelist',
            name='planId',
        ),
        migrations.RenameField(
            model_name='requestaccess',
            old_name='module_Id',
            new_name='module',
        ),
        migrations.RemoveField(
            model_name='module',
            name='baseModuleId',
        ),
        migrations.AddField(
            model_name='company',
            name='status',
            field=models.CharField(default='Active', editable=False, max_length=50),
        ),
        migrations.AddField(
            model_name='module',
            name='modulePrice',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='module',
            name='modulePriceUnit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.CurrencyType'),
        ),
        migrations.AddField(
            model_name='module',
            name='planId',
            field=models.ManyToManyField(db_table='allowedPlanList', to='OrderTangoApp.Plan'),
        ),
        migrations.AddField(
            model_name='otaccount',
            name='planSuspended',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='otaccount',
            name='storageSize',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='planFeaturesJson',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='requestaccess',
            name='panel',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='status',
            field=models.CharField(default='Active', editable=False, max_length=50),
        ),
        migrations.AlterField(
            model_name='company',
            name='companyImage',
            field=models.FileField(blank=True, max_length=5000, null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='company',
            name='companyName',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='company',
            name='postalCode',
            field=models.CharField(max_length=7),
        ),
        migrations.AlterField(
            model_name='plan',
            name='planDesc',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='plan',
            name='status',
            field=models.CharField(default='Active', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=60),
        ),
        migrations.AlterField(
            model_name='user',
            name='firstName',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='user',
            name='lastName',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='user',
            name='otp',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='user',
            name='profilepic',
            field=models.FileField(blank=True, max_length=5000, null=True, upload_to=''),
        ),
        migrations.DeleteModel(
            name='baseModuleList',
        ),
        migrations.AddField(
            model_name='storageallocation',
            name='planDetail',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.Plan'),
        ),
        migrations.AddField(
            model_name='billingdetails',
            name='otAccountDetail',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.oTAccount'),
        ),
        migrations.AddField(
            model_name='addonmodule',
            name='modulesAccess',
            field=models.ManyToManyField(db_table='allowedModuleList', to='OrderTangoApp.Module'),
        ),
        migrations.AddField(
            model_name='addonmodule',
            name='otAccountDetail',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.oTAccount'),
        ),
        migrations.AddField(
            model_name='addonfeatures',
            name='featuresDetails',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.upgradeFeatures'),
        ),
        migrations.AddField(
            model_name='addonfeatures',
            name='otAccountDetail',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.oTAccount'),
        ),
        migrations.AddField(
            model_name='addonfeatures',
            name='purchasedPriceUnit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.CurrencyType'),
        ),
        migrations.AddField(
            model_name='otaccount',
            name='storageAllocation_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.storageAllocation'),
        ),
    ]