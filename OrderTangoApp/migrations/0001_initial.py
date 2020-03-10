# Generated by Django 2.1.2 on 2019-10-29 19:09

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import tenant_schemas.postgresql_backend.base


class Migration(migrations.Migration):

    initial = True

    dependencies = [
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
            name='Company',
            fields=[
                ('companyId', models.AutoField(primary_key=True, serialize=False)),
                ('companyName', models.CharField(max_length=60)),
                ('companyCode', models.CharField(max_length=100, null=True)),
                ('address_Line1', models.CharField(max_length=100)),
                ('address_Line2', models.CharField(max_length=100)),
                ('unit1', models.CharField(max_length=2)),
                ('unit2', models.CharField(max_length=2)),
                ('postalCode', models.CharField(max_length=7)),
                ('schemaName', models.CharField(max_length=100)),
                ('companyImage', models.FileField(blank=True, max_length=5000, null=True, upload_to='')),
                ('userReference', models.CharField(default='Self', editable=False, max_length=100)),
                ('verificationStatus', models.CharField(default='Pending', editable=False, max_length=20)),
                ('urlchanged', models.CharField(default='No', editable=False, max_length=20)),
                ('status', models.CharField(default='Active', editable=False, max_length=50)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'company',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('countryId', models.AutoField(primary_key=True, serialize=False)),
                ('countryCode', models.CharField(max_length=100, null=True)),
                ('countryDesc', models.CharField(max_length=100, null=True)),
                ('countryName', models.CharField(max_length=100)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'country',
            },
        ),
        migrations.CreateModel(
            name='CountryCode',
            fields=[
                ('countryCodeId', models.AutoField(primary_key=True, serialize=False)),
                ('countryCodeType', models.CharField(max_length=100, null=True)),
                ('countryCodeDesc', models.CharField(max_length=100, null=True)),
                ('countryCodeName', models.CharField(max_length=100)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'countrycode',
            },
        ),
        migrations.CreateModel(
            name='CurrencyType',
            fields=[
                ('currencyTypeId', models.AutoField(primary_key=True, serialize=False)),
                ('currencyTypeCode', models.CharField(max_length=50)),
                ('currencyTypeName', models.CharField(max_length=50, null=True)),
                ('currencyTypeDesc', models.CharField(max_length=50, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'currencytype',
            },
        ),
        migrations.CreateModel(
            name='ItemStatus',
            fields=[
                ('itemStatusId', models.AutoField(primary_key=True, serialize=False)),
                ('itemStatusType', models.CharField(max_length=50)),
                ('itemStatusDesc', models.CharField(max_length=50, null=True)),
                ('itemStatusName', models.CharField(max_length=50, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'itemstatus',
            },
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('moduleId', models.AutoField(primary_key=True, serialize=False)),
                ('moduleCode', models.CharField(max_length=50, null=True)),
                ('moduleName', models.CharField(max_length=50, null=True)),
                ('modulePrice', models.FloatField()),
                ('moduleDesc', models.CharField(max_length=50, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('modulePriceUnit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.CurrencyType')),
            ],
            options={
                'db_table': 'module',
            },
        ),
        migrations.CreateModel(
            name='oTAccount',
            fields=[
                ('oTAccountId', models.AutoField(primary_key=True, serialize=False)),
                ('storageSize', models.CharField(max_length=50, null=True)),
                ('status', models.CharField(max_length=50, null=True)),
                ('accountBillingId', models.CharField(max_length=50, null=True)),
                ('otAccName', models.CharField(max_length=50, null=True)),
                ('otAccDesc', models.CharField(max_length=50, null=True)),
                ('otAccCode', models.CharField(max_length=50, null=True)),
                ('planSuspended', models.BooleanField(default=False)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('companyId', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.Company')),
            ],
            options={
                'db_table': 'otaccount',
            },
        ),
        migrations.CreateModel(
            name='oTcompanyToken',
            fields=[
                ('tokenId', models.AutoField(primary_key=True, serialize=False)),
                ('tokenType', models.IntegerField()),
                ('tokenDesc', models.CharField(max_length=50, null=True)),
                ('tokenName', models.CharField(max_length=50, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'otcompanytoken',
            },
        ),
        migrations.CreateModel(
            name='oTorder',
            fields=[
                ('orderId', models.AutoField(primary_key=True, serialize=False)),
                ('orderType', models.IntegerField()),
                ('orderDesc', models.CharField(max_length=50, null=True)),
                ('orderName', models.CharField(max_length=50, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'otorder',
            },
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('planId', models.AutoField(primary_key=True, serialize=False)),
                ('planCode', models.CharField(max_length=50, null=True)),
                ('planName', models.CharField(max_length=50, null=True)),
                ('planDesc', models.TextField(null=True)),
                ('planFeaturesJson', django.contrib.postgres.fields.jsonb.JSONField()),
                ('status', models.CharField(default='Active', max_length=50, null=True)),
                ('cost', models.CharField(max_length=50, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('currencyType', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.CurrencyType')),
            ],
            options={
                'db_table': 'plan',
            },
        ),
        migrations.CreateModel(
            name='QuantityType',
            fields=[
                ('quantityTypeId', models.AutoField(primary_key=True, serialize=False)),
                ('quantityTypeCode', models.CharField(max_length=50)),
                ('quantityTypeName', models.CharField(max_length=50, null=True)),
                ('quantityTypeDesc', models.CharField(max_length=50, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'quantitytype',
            },
        ),
        migrations.CreateModel(
            name='RequestAccess',
            fields=[
                ('requestAccId', models.AutoField(primary_key=True, serialize=False)),
                ('requestMap', models.CharField(max_length=50, null=True)),
                ('type', models.CharField(max_length=50, null=True)),
                ('group', models.CharField(max_length=50, null=True)),
                ('panel', models.CharField(max_length=50, null=True)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('module', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.Module')),
            ],
            options={
                'db_table': 'requestaccess',
            },
        ),
        migrations.CreateModel(
            name='Schema',
            fields=[
                ('domain_url', models.CharField(max_length=128, unique=True)),
                ('schema_name', models.CharField(max_length=63, unique=True, validators=[tenant_schemas.postgresql_backend.base._check_schema_name])),
                ('schemaId', models.AutoField(primary_key=True, serialize=False)),
                ('schemaCode', models.CharField(max_length=100, null=True)),
                ('schemaDesc', models.CharField(max_length=100, null=True)),
                ('schemaCompanyName', models.CharField(max_length=100)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'schema',
            },
        ),
        migrations.CreateModel(
            name='SecurityQuestion',
            fields=[
                ('securityQuestionId', models.AutoField(primary_key=True, serialize=False)),
                ('securityQuestionCode', models.CharField(max_length=100, null=True)),
                ('securityQuestionDesc', models.CharField(max_length=100, null=True)),
                ('securityQuestionName', models.CharField(max_length=100)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'securityquestion',
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('stateId', models.AutoField(primary_key=True, serialize=False)),
                ('stateCode', models.CharField(max_length=100, null=True)),
                ('stateDesc', models.CharField(max_length=100, null=True)),
                ('stateName', models.CharField(max_length=100)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='OrderTangoApp.Country')),
            ],
            options={
                'db_table': 'state',
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
                ('planDetail', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.Plan')),
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
        migrations.CreateModel(
            name='User',
            fields=[
                ('userId', models.AutoField(primary_key=True, serialize=False)),
                ('firstName', models.CharField(max_length=30)),
                ('lastName', models.CharField(max_length=30)),
                ('contactNo', models.CharField(max_length=12)),
                ('email', models.EmailField(max_length=60)),
                ('password', models.CharField(max_length=100)),
                ('otp', models.CharField(max_length=10)),
                ('sec_answer', models.CharField(max_length=100, null=True)),
                ('token', models.CharField(max_length=100, unique=True)),
                ('profilepic', models.FileField(blank=True, max_length=5000, null=True, upload_to='')),
                ('lastLogin', models.DateTimeField(auto_now_add=True)),
                ('activityLog', models.CharField(max_length=100, null=True)),
                ('status', models.CharField(default='Active', editable=False, max_length=50)),
                ('createdDateTime', models.DateTimeField(auto_now_add=True)),
                ('updatedDateTime', models.DateTimeField(auto_now=True)),
                ('countryCode', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.CountryCode')),
                ('sec_question', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.SecurityQuestion')),
                ('userCompanyId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='OrderTangoApp.Company')),
            ],
            options={
                'db_table': 'user',
            },
        ),
        migrations.AddField(
            model_name='otaccount',
            name='plan_Id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.Plan'),
        ),
        migrations.AddField(
            model_name='otaccount',
            name='storageAllocation_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.storageAllocation'),
        ),
        migrations.AddField(
            model_name='module',
            name='planId',
            field=models.ManyToManyField(db_table='allowedPlanList', to='OrderTangoApp.Plan'),
        ),
        migrations.AddField(
            model_name='company',
            name='country',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.Country'),
        ),
        migrations.AddField(
            model_name='company',
            name='state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='OrderTangoApp.State'),
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
    ]
