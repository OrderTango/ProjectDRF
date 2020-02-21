import uuid,datetime
from django.core import serializers
from OrderTangoSubDomainApp.models import *
from django.db.models import F
from django.db import connection


def getSupplierById(id):
    try:
        supplier = Supplier.objects.get(pk = id)
    except:
        supplier = None
    return supplier

def getCustomerById(id):
    try:
        customer = Customer.objects.get(pk = id)
    except:
        customer = None
    return customer

def getCustomerListBasedonSite(siteId):
    try:
        customerList = list(Customer.objects.filter(customerSite__in=Sites.objects.filter(
                            pk=siteId).values('siteId')).values('relId',schemaName =F('trdersId__schemaName')))
    except:
        customerList = []
    return customerList

def getCustomerBasedonCompanyId(companyId):
    try:
        customer = Customer.objects.get(trdersId_id=companyId)
    except:
        customer = None
    return customer

def getSupplierBasedonCompanyId(companyId):
    try:
        supplier = Supplier.objects.get(trdersId_id=companyId)
    except:
        supplier = None
    return supplier


def getCustomerByEmail(email):
    try:
        customer = Customer.objects.get(cusEmail__iexact = email)
    except:
        customer = None
    return customer

def getCustomerByCompanyName(companyName):
    try:
        customer = Customer.objects.get(cusCompanyName__iexact = companyName)
    except:
        customer = None
    return customer

def getCustomerByContactNo(contactNo):
    try:
        customer = Customer.objects.get(cusContactNo__iexact = contactNo)
    except:
        customer = None
    return customer

def getCustomerByConnectionCode(connectionCode):
    try:
        customer = Customer.objects.get(connectionCode = connectionCode)
    except:
        customer = None
    return customer

def getSupplierByConnectionCode(connectionCode):
    try:
        supplier = Supplier.objects.get(connectionCode = connectionCode)
    except:
        supplier = None
    return supplier

def getSupplierByEmail(email):
    try:
        supplier = Supplier.objects.get(supEmail__iexact = email)
    except:
        supplier = None
    return supplier

def getSupplierByCompanyName(companyName):
    try:
        supplier = Supplier.objects.get(supCompanyName__iexact = companyName)
    except:
        supplier = None
    return supplier

def getSupplierByContactNo(contactNo):
    try:
        supplier = Supplier.objects.get(supContactNo__iexact = contactNo)
    except:
        supplier = None
    return supplier

def getProductByItemCode(itemCode):
    try:
        product = ItemMaster.objects.get(itemCode__iexact=itemCode)
    except:
        product =None
    return product

def getProductByItemName(itemName):
    try:
        product = ItemMaster.objects.get(itemName__iexact=itemName)
    except:
        product =None
    return product

def getProductById(productId):
    try:
        product = ItemMaster.objects.get(pk=productId)
    except:
        product =None
    return product

def getSalesDetailsByProduct(product):
    try:
        sales = salesItems.objects.get(salesItem = product)
    except:
        sales = None
    return sales

def getPurchaseDetailsByProduct(product):
    try:
        purchase = purchasingItems.objects.get(purchasingItem = product)
    except:
        purchase = None
    return purchase

def getSiteBysiteAddressId(addressId):
    try:
        site = Sites.objects.get(siteAddress_id=addressId)
    except:
        site = None
    return site

def getSiteSlabasedOnSupplierIdAndSiteId(siteId,supplierId):
    try:
        sla = SupplierSlaForSites.objects.get(userSupSitesCompany_id=supplierId,mappedSites_id=siteId)
    except:
        sla = None
    return sla

def getArticleTypeByName(articleType):
    try:
        articleType = typeOfArticle.objects.get(articleName__iexact=articleType)
    except:
        articleType = None
    return  articleType

def getProductCategoryByName(prtCatName):
    try:
        prodCat = productCategory.objects.get(prtCatName__iexact=prtCatName)
    except:
        prodCat = None
    return  prodCat

def getMerchantCategoryByName(mrctCatName):
    try:
        merchantCat = merchantCategory.objects.get(mrctCatName__iexact=mrctCatName)
    except:
        merchantCat = None
    return  merchantCat

def getMerchantCategoryOneByName(mrctSubCatOneName):
    try:
        merchantCatOne = merchantSubCategoryOne.objects.get(mrctSubCatOneName__iexact=mrctSubCatOneName)
    except:
        merchantCatOne = None
    return  merchantCatOne

def getMerchantCategoryTwoByName(mrctSubCatTwoName):
    try:
        merchantCatTwo = merchantSubCategoryTwo.objects.get(mrctSubCatTwoName__iexact=mrctSubCatTwoName)
    except:
        merchantCatTwo = None
    return  merchantCatTwo

def getStorageConditionByName(stgcntName):
    try:
        strgCond = storageConditions.objects.get(stgcntName__iexact=stgcntName)
    except:
        strgCond = None
    return  strgCond

def getSaleProductCatelogByName(catalogName):
    try:
        prodCat = ProductCatalogForSale.objects.get(catalogName__iexact = catalogName)
    except:
        prodCat = None
    return  prodCat

def getPurchaseProductCatelogByName(catalogName):
    try:
        prodCat = ProductCatalogForPurchase.objects.get(catalogName__iexact = catalogName)
    except:
        prodCat = None
    return  prodCat

def getCustomerSiteBySiteId(siteId,customerId):
    try:
        site = CustomerSiteDetails.objects.get(userCustSiteId__iexact=siteId,userCustSitesCompany_id=customerId)
    except:
        site = None
    return site

def getProductFromSaleProductCatelogById(catalogId):
    try:
        product = ProductCatalogForSaleDetails.objects.get(salePrdtCatDetId=catalogId)
    except:
        product = None
    return  product

def getProductFromPurchaseProductCatelogById(catalogId):
    try:
        product = ProductCatalogForPurchaseDetails.objects.get(purPrdtCatDetId=catalogId)
    except:
        product = None
    return  product

def getHolidayByName(name):
    try:
        holiday = Holidays.objects.get(holidayName= name)
    except:
        holiday = None
    return holiday

def getNotificationById(id):
    try:
        notify = Notification.objects.get(pk=id)
    except:
        notify = None
    return notify