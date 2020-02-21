from django.db import models
from OrderTangoApp.models import CountryCode,Country,State,CurrencyType,RequestAccess,ItemStatus,QuantityType
from django.contrib.postgres.fields import JSONField
from OrderTangoApp import constants
# Create your models here.


class serviceLevelAgreement(models.Model):
    slaId= models.AutoField(primary_key=True)
    slaType = models.CharField(max_length=50, null=True)
    slaDetails = JSONField()
    slaStatus = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.slaType

    class Meta:
        db_table = 'serviceLevelAgreement'

class Area(models.Model):
    areaId = models.AutoField(primary_key=True)
    areaName = models.CharField(max_length=100)
    areaDesc = models.CharField(max_length=100)
    areaStatus = models.CharField(max_length=50,default=constants.Active)
    areaSlaId = models.ForeignKey(serviceLevelAgreement, on_delete=models.CASCADE, related_name="sla")
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.areaName

    class Meta:
        db_table = 'Area'

class UserAddress(models.Model):
    usradd_id=models.AutoField(primary_key=True)
    usradd_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    usradd_address_Line1 = models.CharField(max_length=100)
    usradd_address_Line2 = models.CharField(max_length=100)
    usradd_unit1 = models.CharField(max_length=2)
    usradd_unit2 = models.CharField(max_length=2)
    usradd_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    usradd_postalCode = models.CharField(max_length=6)
    usradd_addressType = models.CharField(max_length=50)
    status = models.CharField(max_length=100, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.usradd_addressType

    class Meta:
        db_table = 'useraddress'

class TypeOfSites(models.Model):
    siteTypeId = models.AutoField(primary_key=True)
    siteTypeCode = models.CharField(max_length=50,null=True)
    siteTypeName = models.CharField(max_length=50,null=True)
    siteTypeDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.siteTypeName

    class Meta:
        db_table = 'TypeOfSites'


class Sites(models.Model):
    siteId = models.AutoField(primary_key=True)
    siteName = models.CharField(max_length=50)
    siteDesc = models.CharField(max_length=100)
    siteStatus = models.CharField(max_length=50,default=constants.Active)
    siteType = models.ForeignKey(TypeOfSites, on_delete=models.CASCADE, related_name='type_sites')
    siteArea = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='area_sites')
    siteAddress = models.ForeignKey(UserAddress, on_delete=models.CASCADE, related_name='site_address')
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.siteName

    class Meta:
        db_table = 'Sites'


class Customer(models.Model):
    customerId = models.AutoField(primary_key=True)
    cusCompanyName = models.CharField(max_length=100)
    cusCompanyCode = models.CharField(max_length=100, null=True)
    cusEmail = models.EmailField(max_length=100)
    cusCountryCode = models.ForeignKey(CountryCode, on_delete=models.SET_NULL, null=True)
    cusContactNo = models.CharField(max_length=12)
    cusCountry = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    cusAddress_Line1 = models.CharField(max_length=100)
    cusAddress_Line2 = models.CharField(max_length=100)
    cusUnit1 = models.CharField(max_length=2)
    cusUnit2 = models.CharField(max_length=2)
    cusState = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    cusPostalCode = models.CharField(max_length=6)
    customerCode = models.CharField(max_length=100,null=True)
    contactPerson = models.CharField(max_length=100,null=True)
    connectionCode =  models.CharField(max_length=100,null=True)
    cusAlterNateEmail = models.EmailField(max_length=100,null=True)
    invitationStatus = models.IntegerField(default=0)
    relationshipStatus = models.BooleanField(default=False)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.customerId

    class Meta:
        db_table = 'Customer'

class CustomerShippingAddress(models.Model):
    cusShippingId = models.AutoField(primary_key=True)
    cusShipAddress_Line1 = models.CharField(max_length=100)
    cusShipAddress_Line2 = models.CharField(max_length=100)
    cusShipUnit1 = models.CharField(max_length=2)
    cusShipUnit2 = models.CharField(max_length=2)
    cusShipCountry = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    cusShipState = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    cusShipPostalCode = models.CharField(max_length=6)
    status = models.CharField(max_length=50, default=constants.Active)
    shippingCustomer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.cusShippingId

    class Meta:
        db_table = 'CustomerShippingAddress'


class Supplier(models.Model):
    supplierId =  models.AutoField(primary_key=True)
    supCompanyName = models.CharField(max_length=100)
    supCompanyCode = models.CharField(max_length=100, null=True)
    supEmail = models.EmailField(max_length=100)
    supCountryCode = models.ForeignKey(CountryCode, on_delete=models.SET_NULL, null=True)
    supContactNo = models.CharField(max_length=12)
    supCountry = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    supAddress_Line1 = models.CharField(max_length=100)
    supAddress_Line2 = models.CharField(max_length=100)
    supUnit1 = models.CharField(max_length=2)
    supUnit2 = models.CharField(max_length=2)
    supState = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    supPostalCode = models.CharField(max_length=6)
    supplierCode = models.CharField(max_length=100, null=True)
    connectionCode = models.CharField(max_length=100, null=True)
    supAlterNateEmail = models.EmailField(max_length=100,null=True)
    invitationStatus = models.IntegerField(default=0)
    relationshipStatus = models.BooleanField(default=False)
    contactPerson = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.supplierId

    class Meta:
        db_table = 'Supplier'


class SupplierShippingAddress(models.Model):
    supShippingId = models.AutoField(primary_key=True)
    supShipAddress_Line1 = models.CharField(max_length=100)
    supShipAddress_Line2 = models.CharField(max_length=100)
    supShipUnit1 = models.CharField(max_length=2)
    supShipUnit2 = models.CharField(max_length=2)
    supShipCountry = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    supShipState = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    supShipPostalCode = models.CharField(max_length=6)
    status = models.CharField(max_length=50, default=constants.Active)
    shippingSupplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.supShippingId

    class Meta:
        db_table = 'SupplierShippingAddress'


class typeOfArticle(models.Model):
    articleId = models.AutoField(primary_key=True)
    articleCode = models.CharField(max_length=50, null=True)
    articleName = models.CharField(max_length=50, null=True)
    articleDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.articleName

    class Meta:
        db_table = 'typeOfArticle'

class productCategory(models.Model):
    prtCatId = models.AutoField(primary_key=True)
    prtCatCode = models.CharField(max_length=50, null=True)
    prtCatName = models.CharField(max_length=50, null=True)
    prtCatDesc = models.CharField(max_length=50, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.prtCatName

    class Meta:
        db_table = 'productCategory'

class merchantCategory(models.Model):
    mrctCatId = models.AutoField(primary_key=True)
    mrctCatCode = models.CharField(max_length=50, null=True)
    mrctCatName = models.CharField(max_length=50, null=True)
    mrctCatDesc = models.CharField(max_length=50, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mrctCatName

    class Meta:
        db_table = 'merchantCategory'

class merchantSubCategoryOne(models.Model):
    mrctSubCatOneId = models.AutoField(primary_key=True)
    mrctSubCatOneCode = models.CharField(max_length=50, null=True)
    mrctSubCatOneName = models.CharField(max_length=50, null=True)
    mrctSubCatOneDesc = models.CharField(max_length=50, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mrctSubCatOneName

    class Meta:
        db_table = 'merchantSubCategoryOne'


class merchantSubCategoryTwo(models.Model):
    mrctSubCatTwoId = models.AutoField(primary_key=True)
    mrctSubCatTwoCode = models.CharField(max_length=50, null=True)
    mrctSubCatTwoName = models.CharField(max_length=50, null=True)
    mrctSubCatTwoDesc = models.CharField(max_length=50, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mrctSubCatTwoName

    class Meta:
        db_table = 'merchantSubCategoryTwo'


class storageConditions(models.Model):
    stgcntId = models.AutoField(primary_key=True)
    stgcntCode = models.CharField(max_length=50,null=True)
    stgcntName = models.CharField(max_length=50,null=True)
    stgcntDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.stgcntName

    class Meta:
        db_table = 'storageConditions'


class taxCode(models.Model):
    taxCodeId = models.AutoField(primary_key=True)
    taxCodeCode = models.CharField(max_length=50,null=True)
    taxCodeName = models.CharField(max_length=50,null=True)
    taxCodeDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.taxCodeName

    class Meta:
        db_table = 'taxCode'

class itemDimension(models.Model):
    itemDimensionId = models.AutoField(primary_key=True)
    itemDimensionCode = models.CharField(max_length=50,null=True)
    itemDimensionName = models.CharField(max_length=50,null=True)
    itemDimensionDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.itemDimensionName

    class Meta:
        db_table = 'itemDimension'

class weightUnit(models.Model):
    weightUnitId = models.AutoField(primary_key=True)
    weightUnitCode = models.CharField(max_length=50,null=True)
    weightUnitName = models.CharField(max_length=50,null=True)
    weightUnitDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.weightUnitName

    class Meta:
        db_table = 'weightUnit'

class itemDepartment(models.Model):
    itemDeptId = models.AutoField(primary_key=True)
    itemDeptCode = models.CharField(max_length=50,null=True)
    itemDeptName = models.CharField(max_length=50,null=True)
    itemDeptDesc = models.CharField(max_length=50,null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.itemDeptName

    class Meta:
        db_table = 'itemDepartment'


class ItemMaster(models.Model):
    itemMasterId = models.AutoField(primary_key=True)
    itemCode=models.CharField(max_length=50)
    itemName=models.CharField(max_length=50)
    alterItemCode = models.CharField(max_length=50)
    alterItemName = models.CharField(max_length=50)
    brandName = models.CharField(max_length=50)
    itemDesc = models.CharField(max_length=50)
    articleType = models.ForeignKey(typeOfArticle,related_name='articleType',null=True,on_delete=models.CASCADE)
    itemCategory = models.ForeignKey(productCategory,related_name='itemCategory',null=True, on_delete=models.CASCADE)
    itemMerchantCategory = models.ForeignKey(merchantCategory,related_name='itemMerchantCategory',null=True, on_delete=models.CASCADE)
    itemMerchantCategoryOne = models.ForeignKey(merchantSubCategoryOne,related_name='itemMerchantCategoryOne',null=True, on_delete=models.CASCADE)
    itemMerchantCategoryTwo = models.ForeignKey(merchantSubCategoryTwo,related_name='itemMerchantCategoryTwo',null=True,on_delete=models.CASCADE)
    itemStorageCondition = models.ForeignKey(storageConditions,related_name='itemStorageCondition',null=True,on_delete=models.CASCADE)
    baseUom=models.ForeignKey(QuantityType,related_name='baseUom',null=True,on_delete=models.CASCADE)
    packingUnit = models.CharField(max_length=50)
    selfManufacturing = models.BooleanField(default=False)
    manufacturingLeadTime = models.CharField(max_length=50)
    productDetail = models.CharField(default=constants.Both, max_length=50)
    status = models.CharField(max_length=50,default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.itemMasterId

    class Meta:
        db_table = 'itemmaster'

class productAttribute(models.Model):
    attributeId = models.AutoField(primary_key=True)
    attributeItem = models.ForeignKey(ItemMaster,related_name='attributeItem',on_delete=models.CASCADE)
    attributeColor = models.CharField(max_length=50,null=True)
    attributeSize = models.CharField(max_length=50,null=True)
    attributeDesign = models.CharField(max_length=50,null=True)
    attributeStyle = models.CharField(max_length=50,null=True)
    attributeOther = models.CharField(max_length=50,null=True)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.attributeId

    class Meta:
        db_table = 'productAttribute'

class purchasingItems(models.Model):
    purchasingId = models.AutoField(primary_key=True)
    purchasingItem = models.ForeignKey(ItemMaster,related_name='purchasingItem',on_delete=models.CASCADE)
    purchasingUom = models.ForeignKey(QuantityType,related_name='purchasingUom',null=True,on_delete=models.CASCADE)
    purchasingTax = models.ForeignKey(taxCode,related_name='purchasingTax',null=True,on_delete=models.CASCADE)
    purchasingPrice = models.FloatField(null=True,)
    purchasingCurrency = models.ForeignKey(CurrencyType,related_name='purchasingCurrency',null=True,on_delete=models.CASCADE)
    purchasingPriceUnit = models.FloatField(null=True)
    purchasingUomForKg = models.ForeignKey(QuantityType,related_name='purchasingUomForKg',null=True,on_delete=models.CASCADE)
    purchasingOrderText = models.CharField(max_length=50,null=True)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.purchasingId

    class Meta:
        db_table = 'purchasingItems'

class salesItems(models.Model):
    salesId = models.AutoField(primary_key=True)
    salesItem = models.ForeignKey(ItemMaster,related_name='salesItem', on_delete=models.CASCADE)
    salesUom = models.ForeignKey(QuantityType,related_name='salesUom',null=True, on_delete=models.CASCADE)
    salesTax = models.ForeignKey(taxCode,related_name='salesTax',null=True, on_delete=models.CASCADE)
    salesCategoryGrp = models.CharField(max_length=50, null=True)
    salesPrice = models.FloatField(null=True)
    salesCurrency = models.ForeignKey(CurrencyType,related_name='salesCurrency',null=True, on_delete=models.CASCADE)
    salesPriceUnit = models.FloatField(null=True)
    salesUomForKg = models.ForeignKey(QuantityType,related_name='salesUomForKg',null=True, on_delete=models.CASCADE)
    salesOrderText = models.CharField(max_length=50, null=True)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.salesId

    class Meta:
        db_table = 'salesItems'


class itemMeasurement(models.Model):
    measurementId = models.AutoField(primary_key=True)
    measurementItem = models.ForeignKey(ItemMaster,related_name='measurementItem', on_delete=models.CASCADE)
    measurementDimension=models.CharField(max_length=50,null=True)
    measurementDimensionUnit = models.ForeignKey(itemDimension,related_name='measurementDimensionUnit',null=True,on_delete=models.CASCADE)
    measurementLength = models.FloatField(null=True)
    measurementWidth = models.FloatField(null=True)
    measurementHeight = models.FloatField(null=True)
    measurementWeight = models.FloatField(null=True)
    measurementWeightUnit = models.ForeignKey(weightUnit,related_name='measurementWeightUnit',null=True,on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.measurementId

    class Meta:
        db_table = 'itemMeasurement'


class itemStorage(models.Model):
    storageId = models.AutoField(primary_key=True)
    storageItem = models.ForeignKey(ItemMaster,related_name='storageItem', on_delete=models.CASCADE)
    storageShelfLife = models.CharField(max_length=50,null=True)
    storageCase = models.CharField(max_length=50,null=True)
    storageTier = models.CharField(max_length=50,null=True)
    storagePallet = models.CharField(max_length=50,null=True)
    storageDept = models.ForeignKey(itemDepartment,related_name='storageDept',null=True,on_delete=models.CASCADE)
    storageRack = models.CharField(max_length=50,null=True)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.storageId

    class Meta:
        db_table = 'itemStorage'

class itemParameter(models.Model):
    parameterId = models.AutoField(primary_key=True)
    parameterItem = models.ForeignKey(ItemMaster,related_name='parameterItem', on_delete=models.CASCADE)
    alterNateParamOne = models.CharField(max_length=50,null=True)
    alterNateParamTwo = models.CharField(max_length=50,null=True)
    alterNateParamThree = models.CharField(max_length=50,null=True)
    alterNateParamFour = models.CharField(max_length=50,null=True)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.parameterId

    class Meta:
        db_table = 'itemParameter'


class Notification(models.Model):
    notificationId = models.AutoField(primary_key=True)
    sendFromId = models.CharField(max_length=255)
    desc = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    viewed = models.CharField(max_length=255, default=constants.No, editable=False)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.notificationId

    class Meta:
        db_table = 'notification'

class Store(models.Model):
    storeId = models.AutoField(primary_key=True)
    companyAddress = models.ForeignKey(Sites, on_delete=models.CASCADE)
    productId = models.ForeignKey(ItemMaster, on_delete=models.CASCADE)
    stockCount = models.CharField(max_length=50)
    stockUnit = models.ForeignKey(QuantityType, related_name='stock', on_delete=models.CASCADE)
    itemStatus = models.ForeignKey(ItemStatus, related_name='itemstatus', on_delete=models.CASCADE)
    sellCount = models.CharField(max_length=50)
    sellUnit = models.ForeignKey(QuantityType, related_name='sell', on_delete=models.CASCADE)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)


    def __int__(self):
        return self.storeId

    class Meta:
        db_table = 'store'

class Subuser(models.Model):
    subUserId = models.AutoField(primary_key=True)
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    email = models.EmailField(max_length=100,null=True)
    userName = models.CharField(max_length=50)
    password = models.CharField(max_length=100)
    designation = models.CharField(max_length=50)
    contactNo = models.CharField(max_length=12)
    role = models.CharField(max_length=50)
    DOJ = models.CharField(max_length=50)
    DOD = models.CharField(max_length=50, null=True)
    profilepic = models.FileField(blank=True, null=True)
    status = models.CharField(max_length=50,default=constants.Active)
    lastLogin = models.DateTimeField(auto_now_add=True)
    activityLog = models.CharField(max_length=100, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.subUserId

    class Meta:
        db_table = 'subuser'


class SubuserSiteAssign(models.Model):
    subuserSiteAssignId = models.AutoField(primary_key=True)
    subuserSiteAssignSites = models.ForeignKey(Sites, on_delete=models.SET_NULL, null=True)
    subuserSiteAssignSubUser = models.ForeignKey(Subuser, on_delete=models.SET_NULL, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.subuserSiteAssignId

    class Meta:
        db_table = 'subusersiteassign'


class userSubReqAcc(models.Model):
    userSubReqAccId = models.AutoField(primary_key=True)
    subUserId = models.ForeignKey(Subuser, on_delete=models.SET_NULL, null=True)
    subReqAccId = models.ForeignKey(RequestAccess, on_delete=models.SET_NULL, null=True)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.userSubReqAccId

    class Meta:
        db_table = 'usersubReqAcc'


class CustomerSiteDetails(models.Model):
    userCustSitesId = models.AutoField(primary_key=True)
    userCustSiteId = models.CharField(max_length=100)
    userCustSiteName = models.CharField(max_length=100)
    userCustSitesCompany = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    mappedSites = models.ForeignKey(Sites, on_delete=models.SET_NULL, null=True)
    customer_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    customer_address_Line1 = models.CharField(max_length=100)
    customer_address_Line2 = models.CharField(max_length=100)
    customer_unit1 = models.CharField(max_length=2)
    customer_unit2 = models.CharField(max_length=2)
    customer_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    customer_postalCode = models.CharField(max_length=6)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.userCustSitesId

    class Meta:
        db_table = 'CustomerSiteDetails'

class SupplierSlaForSites(models.Model):
    userSupSitesId = models.AutoField(primary_key=True)
    userSupSitesCompany = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    mappedSites = models.ForeignKey(Sites, on_delete=models.SET_NULL, null=True)
    slaFromSupplier = JSONField()
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.userSupSitesId

    class Meta:
        db_table = 'SupplierSlaForSites'


class ProductCatalogForSale(models.Model):
    salePrdtCatId = models.AutoField(primary_key=True)
    catalogName = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.salePrdtCatId

    class Meta:
        db_table = 'ProductCatalogForSale'


class ProductCatalogForSaleDetails(models.Model):
    salePrdtCatDetId = models.AutoField(primary_key=True)
    productCatelogId = models.ForeignKey(ProductCatalogForSale, related_name='prdtCatelogueId', null=True, on_delete=models.CASCADE)
    productId = models.ForeignKey(ItemMaster, related_name='salCatProductId', null=True, on_delete=models.CASCADE)
    itemCode = models.CharField(max_length=50)
    itemName = models.CharField(max_length=50)
    itemCategory = models.ForeignKey(productCategory, related_name='itemCategorySale', null=True, on_delete=models.CASCADE)
    alterItemCode = models.CharField(max_length=50)
    alterItemName = models.CharField(max_length=50)
    salesUom = models.ForeignKey(QuantityType, related_name='salesUompCat', null=True, on_delete=models.CASCADE)
    salesTax = models.ForeignKey(taxCode, related_name='salesTaxpCat', null=True, on_delete=models.CASCADE)
    salesPrice = models.FloatField(null=True)
    salesCurrency = models.ForeignKey(CurrencyType, related_name='salesCurrencypCat', null=True, on_delete=models.CASCADE)
    salesUomForKg = models.ForeignKey(QuantityType, related_name='salesUomForKgpCat', null=True, on_delete=models.CASCADE)
    discountPercentage = models.IntegerField(null=True)
    discountAbsolute = models.FloatField(null=True)
    discountPrice = models.FloatField(null=True)
    stockStatus = models.CharField(max_length=50, default=constants.Available)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.salePrdtCatDetId

    class Meta:
        db_table = 'ProductCatalogForSaleDetails'


class ProductCatalogForPurchase(models.Model):
    purPrdtCatId = models.AutoField(primary_key=True)
    catalogName = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.purPrdtCatId

    class Meta:
        db_table = 'ProductCatalogForPurchase'


class ProductCatalogForPurchaseDetails(models.Model):
    purPrdtCatDetId = models.AutoField(primary_key=True)
    productCatelogId = models.ForeignKey(ProductCatalogForPurchase, related_name='prdtCatelogueId', null=True, on_delete=models.CASCADE)
    productId = models.ForeignKey(ItemMaster, related_name='purCatProductId', null=True, on_delete=models.CASCADE)
    itemCode = models.CharField(max_length=50)
    itemName = models.CharField(max_length=50)
    itemCategory = models.ForeignKey(productCategory, related_name='itemCategoryPurchase', null=True, on_delete=models.CASCADE)
    alterItemCode = models.CharField(max_length=50)
    alterItemName = models.CharField(max_length=50)
    purchaseUom = models.ForeignKey(QuantityType, related_name='purchaseUompCat', null=True, on_delete=models.CASCADE)
    purchaseTax = models.ForeignKey(taxCode, related_name='purchaseTaxpCat', null=True, on_delete=models.CASCADE)
    purchasePrice = models.FloatField(null=True)
    purchaseCurrency = models.ForeignKey(CurrencyType, related_name='purchaseCurrencypCat', null=True, on_delete=models.CASCADE)
    purchaseUomForKg = models.ForeignKey(QuantityType, related_name='purchaseUomForKgpCat', null=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.purPrdtCatDetId

    class Meta:
        db_table = 'ProductCatalogForPurchaseDetails'



class CustomerProductCatalog(models.Model):
    customerCatId = models.AutoField(primary_key=True)
    customerId = models.ForeignKey(Customer, related_name='customerCatalog', on_delete=models.CASCADE)
    productCatId = models.ForeignKey(ProductCatalogForSale, related_name='productCatId', null=True, on_delete=models.CASCADE)
    productId = models.ForeignKey(ItemMaster, related_name='productId', null=True, on_delete=models.CASCADE)
    itemCode = models.CharField(max_length=50)
    itemName = models.CharField(max_length=50)
    itemCategory = models.ForeignKey(productCategory, related_name='itemCategoryCustomer', null=True, on_delete=models.CASCADE)
    customerItemCode = models.CharField(max_length=50,null =True)
    customerItemName = models.CharField(max_length=50,null = True)
    salesUom = models.ForeignKey(QuantityType, related_name='salesUomCusCat', null=True, on_delete=models.CASCADE)
    salesTax = models.ForeignKey(taxCode, related_name='salesTaxCusCat', null=True, on_delete=models.CASCADE)
    salesPrice = models.FloatField(null=True)
    salesCurrency = models.ForeignKey(CurrencyType, related_name='salesCurrencyCusCat', null=True,
                                      on_delete=models.CASCADE)
    salesUomForKg = models.ForeignKey(QuantityType, related_name='salesUomForKgCusCat', null=True,
                                      on_delete=models.CASCADE)
    discountPercentage = models.IntegerField(default=0)
    discountAbsolute = models.FloatField(default=0)
    discountPrice = models.FloatField(null=True)
    stockStatus = models.CharField(max_length=50, default=constants.Available)
    status = models.CharField(max_length=50, default=constants.Active)
    linked =  models.BooleanField(default=False)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.customerCatId

    class Meta:
        db_table = 'CustomerProductCatalog'


class SupplierProductCatalog(models.Model):
    supplierCatId = models.AutoField(primary_key=True)
    supplierId = models.ForeignKey(Supplier, related_name='supplierCatalog', on_delete=models.CASCADE)
    productCatId = models.ForeignKey(ProductCatalogForPurchase, related_name='productCatId', null=True,
                                     on_delete=models.CASCADE)
    productId = models.ForeignKey(ItemMaster, related_name='productIdSupplier', null=True, on_delete=models.CASCADE)
    itemCode = models.CharField(max_length=50, null=True)
    itemName = models.CharField(max_length=50, null=True)
    itemCategory = models.ForeignKey(productCategory, related_name='itemCategorySupplier', null=True, on_delete=models.CASCADE)
    supplierItemCode = models.CharField(max_length=50, null=True)
    supplierItemName = models.CharField(max_length=50, null=True)
    purchaseUom = models.ForeignKey(QuantityType, related_name='purUomCusCat', null=True, on_delete=models.CASCADE)
    purchaseTax = models.ForeignKey(taxCode, related_name='purTaxCusCat', null=True, on_delete=models.CASCADE)
    purchasePrice = models.FloatField(null=True)
    purchaseCurrency = models.ForeignKey(CurrencyType, related_name='purCurrencyCusCat', null=True,
                                      on_delete=models.CASCADE)
    purchaseUomForKg = models.ForeignKey(QuantityType, related_name='purUomForKgCusCat', null=True,
                                      on_delete=models.CASCADE)
    discountPrice = models.FloatField(null=True)
    stockStatus = models.CharField(max_length=50, default=constants.Available)
    defaultSupplier = models.BooleanField(default=False)
    status = models.CharField(max_length=50, default=constants.Active)
    linked = models.BooleanField(default=False)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.supplierCatId

    class Meta:
        db_table = 'SupplierProductCatalog'

class Holidays(models.Model):
    holidayId = models.AutoField(primary_key=True)
    holidayYear = models.IntegerField()
    holidayName = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.holidayId

    class Meta:
        db_table = 'Holidays'

class HolidaysDetails(models.Model):
    holidayDetId = models.AutoField(primary_key=True)
    holiday = models.ForeignKey(Holidays,related_name='holiday',on_delete=models.CASCADE)
    holidayDate = models.CharField(max_length=50)
    holidayReason = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.holidayDetId

    class Meta:
        db_table = 'HolidaysDetails'