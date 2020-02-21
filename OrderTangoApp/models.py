from django.db import models
from tenant_schemas.models import TenantMixin
from django.contrib.postgres.fields import JSONField
from OrderTangoApp import constants

class Country(models.Model):
    countryId =  models.AutoField(primary_key=True)
    countryCode =  models.CharField(max_length=100,null=True)
    countryDesc =  models.CharField(max_length=100,null=True)
    countryName = models.CharField(max_length=100)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.countryName

    class Meta:
        db_table = 'country'


class State(models.Model):
    stateId = models.AutoField(primary_key=True)
    stateCode = models.CharField(max_length=100,null=True)
    stateDesc = models.CharField(max_length=100,null=True)
    stateName = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.stateName

    class Meta:
        db_table = 'state'


class CountryCode(models.Model):
    countryCodeId = models.AutoField(primary_key=True)
    countryCodeType = models.CharField(max_length=100,null=True)
    countryCodeDesc = models.CharField(max_length=100,null=True)
    countryCodeName = models.CharField(max_length=100)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.countryCodeName

    class Meta:
        db_table = 'countrycode'

class SecurityQuestion(models.Model):
    securityQuestionId = models.AutoField(primary_key=True)
    securityQuestionCode = models.CharField(max_length=100,null=True)
    securityQuestionDesc = models.CharField(max_length=100,null=True)
    securityQuestionName = models.CharField(max_length=100)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.securityQuestionName

    class Meta:
        db_table = 'securityquestion'


class Company(models.Model):
    companyId = models.AutoField(primary_key=True)
    companyName = models.CharField(max_length=100)
    companyCode = models.CharField(max_length=100,null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    address_Line1 = models.CharField(max_length=100)
    address_Line2 = models.CharField(max_length=100)
    unit1 = models.CharField(max_length=2)
    unit2 = models.CharField(max_length=2)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    postalCode = models.CharField(max_length=6)
    schemaName = models.CharField(max_length=100)
    companyImage = models.FileField(blank=True, null=True)
    userReference = models.CharField(max_length=100, default=constants.Self, editable=False)
    verificationStatus = models.CharField(max_length=20, default=constants.Pending, editable=False)
    urlchanged = models.CharField(max_length=20, default=constants.No, editable=False)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.companyId

    class Meta:
        db_table = 'company'


class User(models.Model):
    userId = models.AutoField(primary_key=True)
    userCompanyId = models.ForeignKey(Company, on_delete=models.CASCADE)
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    countryCode = models.ForeignKey(CountryCode, on_delete=models.SET_NULL, null=True)
    contactNo = models.CharField(max_length=12)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)
    otp = models.CharField(max_length=4)
    sec_question = models.ForeignKey(SecurityQuestion, on_delete=models.SET_NULL, null=True)
    sec_answer = models.CharField(max_length=100,null=True)
    token = models.CharField(max_length=100, unique=True)
    profilepic = models.FileField(blank=True, null=True)
    lastLogin = models.DateTimeField(auto_now_add=True)
    activityLog = models.CharField(max_length=100,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.userId

    class Meta:
        db_table = 'user'


class Schema(TenantMixin):
    schemaId = models.AutoField(primary_key=True)
    schemaCode = models.CharField(max_length=100,null=True)
    schemaDesc = models.CharField(max_length=100,null=True)
    schemaCompanyName = models.CharField(max_length=100)
    auto_create_schema = True
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schema'


class QuantityType(models.Model):
    quantityTypeId = models.AutoField(primary_key=True)
    quantityTypeCode = models.CharField(max_length=50)
    quantityTypeName = models.CharField(max_length=50,null=True)
    quantityTypeDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.quantityTypeCode

    class Meta:
        db_table = 'quantitytype'


class CurrencyType(models.Model):
    currencyTypeId = models.AutoField(primary_key=True)
    currencyTypeCode = models.CharField(max_length=50)
    currencyTypeName = models.CharField(max_length=50,null=True)
    currencyTypeDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.currencyTypeCode

    class Meta:
        db_table = 'currencytype'

class ItemStatus(models.Model):
    itemStatusId = models.AutoField(primary_key=True)
    itemStatusType = models.CharField(max_length=50)
    itemStatusDesc = models.CharField(max_length=50,null=True)
    itemStatusName = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.itemStatusType

    class Meta:
        db_table = 'itemstatus'

class oTorder(models.Model):
    orderId = models.AutoField(primary_key=True)
    orderType = models.IntegerField()
    orderDesc = models.CharField(max_length=50,null=True)
    orderName = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.orderType

    class Meta:
        db_table = 'otorder'


class Plan(models.Model):
    planId = models.AutoField(primary_key=True)
    planCode = models.CharField(max_length=50,null=True)
    planName = models.CharField(max_length=50,null=True)
    planDesc = models.CharField(max_length=50,null=True)
    status = models.CharField(max_length=50,null=True)
    cost = models.CharField(max_length=50,null=True)
    currencyType = models.ForeignKey(CurrencyType, on_delete=models.SET_NULL, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.planName

    class Meta:
        db_table = 'plan'

class oTAccount(models.Model):
    oTAccountId = models.AutoField(primary_key=True)
    plan_Id = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=50,null=True)
    accountBillingId = models.CharField(max_length=50,null=True)
    companyId = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    otAccName = models.CharField(max_length=50,null=True)
    otAccDesc = models.CharField(max_length=50, null=True)
    otAccCode = models.CharField(max_length=50, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.otAccName

    class Meta:
        db_table = 'otaccount'


class baseModuleList(models.Model):
    baseModId = models.AutoField(primary_key=True)
    baseModCode = models.CharField(max_length=50,null=True)
    baseModName = models.CharField(max_length=50,null=True)
    planId = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    baseModDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.baseModCode

    class Meta:
        db_table = 'basemodulelist'

class Module(models.Model):
    moduleId = models.AutoField(primary_key=True)
    moduleCode = models.CharField(max_length=50, null=True)
    moduleName = models.CharField(max_length=50, null=True)
    baseModuleId = models.ForeignKey(baseModuleList, on_delete=models.SET_NULL, null=True)
    moduleDesc = models.CharField(max_length=50, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.moduleCode

    class Meta:
        db_table = 'module'

class RequestAccess(models.Model):
    requestAccId = models.AutoField(primary_key=True)
    module_Id = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True)
    requestMap = models.CharField(max_length=50, null=True)
    type = models.CharField(max_length=50, null=True)
    group = models.CharField(max_length=50, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.requestMap

    class Meta:
        db_table = 'requestaccess'

class oTcompanyToken(models.Model):
    tokenId = models.AutoField(primary_key=True)
    tokenType = models.IntegerField()
    tokenDesc = models.CharField(max_length=50,null=True)
    tokenName = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.tokenType

    class Meta:
        db_table = 'otcompanytoken'
