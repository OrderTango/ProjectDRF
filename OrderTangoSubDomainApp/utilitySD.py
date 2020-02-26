from OrderTangoSubDomainApp.models import *
from OrderTangoOrdermgmtApp.models import *
from OrderTangoOrderFulfilmtApp.models import *
import sys

def getSupplierById(id):
    try:
        supplier = Supplier.objects.get(pk = id)
    except:
        supplier = None
    return supplier

def getSupplierByConnectionCode(connectionCode):
    try:
        supplier = Supplier.objects.get(connectionCode__iexact = connectionCode)
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

def getCustomerById(id):
    try:
        customer = Customer.objects.get(pk = id)
    except:
        customer = None
    return customer

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
        customer = Customer.objects.get(connectionCode__iexact = connectionCode)
    except:
        customer = None
    return customer

def getCustomerSiteDetailsForUpdateSites(siteId):
    try:
        customer = CustomerSiteDetails.objects.get(userCustSiteId__iexact=siteId,
                                               linkedStatus=True)
    except:
        customer = None
    return customer

def getCustomerListBasedonSite(siteId):
    try:
        customerList = list(CustomerSiteDetails.objects.filter(mappedSites__in=Sites.objects.filter(
                            pk=siteId).values('siteId')).values('userCustSitesCompany'))
    except:
        customerList = []
    return customerList


def getCustomerListBasedonSla(slaId):
    try:
        customerList = list(CustomerSiteDetails.objects.filter(mappedSites_id=slaId,
                                                               userCustSitesCompany__relationshipStatus=True).values(
            'userCustSitesCompany__cusCompanyCode','userCustSitesCompany__connectionCode','userCustSiteId'))
    except:
        customerList = []
    return customerList


def getCustomerSiteBySiteId(siteId,customerId):
    try:
        site = CustomerSiteDetails.objects.get(userCustSiteId__iexact=siteId,userCustSitesCompany_id=customerId,
                                               linkedStatus=True)
    except:
        site = None
    return site

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


def getSiteSlabasedOnSupplierIdAndSiteId(siteId,supplierId):
    try:
        sla = SupplierSlaForSites.objects.get(userSupSitesCompany_id=supplierId,mappedSites_id=siteId,
                                              status=constants.Active,linkedStatus = True)
    except:
        try:
            sla = SupplierSlaForSites.objects.get(userSupSitesCompany_id=supplierId, mappedSites_id=siteId,
                                                  status=constants.Active,selfCreation=True)
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

def getSaleProductCatelogById(catalogId):
    try:
        prodCat = ProductCatalogForSale.objects.get(pk = catalogId)
    except:
        prodCat = None
    return  prodCat

def getPurchaseProductCatelogByName(catalogName):
    try:
        prodCat = ProductCatalogForPurchase.objects.get(catalogName__iexact = catalogName)
    except:
        prodCat = None
    return  prodCat

def getPurchaseProductCatelogById(catalogId):
    try:
        prodCat = ProductCatalogForPurchase.objects.get(purPrdtCatId = catalogId)
    except:
        prodCat = None
    return  prodCat


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

def getTaxCodeByName(taxCodeName):
    try:
        tax = taxCode.objects.get(taxCodeName__iexact=taxCodeName)
    except:
        tax = None
    return tax

"""customer/supplier code generator method for create unique customer/supplier code"""
def oTtradersCodeGenerator(companyName,tradersRole):
    comName = companyName.replace(' ', '')[:3].upper()
    if tradersRole.lower() == 'customer':
        trdRole = "BUY"
        filterObject = comName + trdRole
        filterResult = Customer.objects.filter(customerCode__contains=filterObject).order_by(
            '-customerCode').values_list('customerCode', flat=True)[:1]
    else:
        trdRole = "SEL"
        filterObject = comName + trdRole
        filterResult = Supplier.objects.filter(supplierCode__contains=filterObject).order_by(
            '-supplierCode').values_list('supplierCode', flat=True)[:1]
    if not filterResult:
        tradersCodeId = filterObject+str(1).zfill(6)
    else:
        tradersCodeId = filterObject+str(int(filterResult[0][6:])+1).zfill(6)
    return tradersCodeId.upper()

def getAreaById(areaId):
    try:
        area = Area.objects.get(pk=areaId)
    except:
        area = None
    return area

def getAreaByAreaName(areaName):
    try:
        area = Area.objects.get(areaName__iexact=areaName)
    except:
        area = None
    return area

def getSiteBysiteAddressId(addressId):
    try:
        site = Sites.objects.get(siteAddress_id=addressId)
    except:
        site = None
    return site

def getSiteBySiteId(siteId):
    try:
        site = Sites.objects.get(pk=siteId)
    except:
        site = None
    return site

def getSiteBySiteName(siteName):
    try:
        site = Sites.objects.get(siteName__iexact=siteName)
    except:
        site = None
    return site

def getSlaBySlaId(slaId):
    try:
        sla = serviceLevelAgreement.objects.get(pk=slaId)
    except:
        sla = None
    return sla

def getSlaBySlaName(slaType):
    try:
        sla = serviceLevelAgreement.objects.get(slaType__iexact=slaType)
    except:
        sla = None
    return sla

def getSupplierCatalogById(catalogId):
    try:
        catalog = SupplierProductCatalog.objects.get(supplierCatId=catalogId)
    except:
        catalog = None
    return  catalog


def getSupplierCatalogByProductCode(itemCode):
    try:
        catalog = SupplierProductCatalog.objects.get(supplierItemCode__iexact=itemCode)
    except:
        catalog = None
    return  catalog

def getCustomerCatalogByProductCode(itemCode):
    try:
        catalog = CustomerProductCatalog.objects.get(customerItemCode__iexact=itemCode)
    except:
        catalog = None
    return catalog

def getCustomerCatalogById(catalogId):
    try:
        catalog = CustomerProductCatalog.objects.get(customerCatId=catalogId)
    except:
        catalog = None
    return  catalog

def getRoleByRoleName(roleName):
    try:
        role = RolesAndAccess.objects.get(roleName__iexact = roleName)
    except:
        role = None
    return role

def getRoleById(roleId):
    try:
        role = RolesAndAccess.objects.get(pk = roleId)
    except:
        role = None
    return role

def getCustomerSiteBySiteName(customer,siteName):
    try:
        site = CustomerSiteDetails.objects.get(userCustSitesCompany=customer,userCustSiteName=siteName)
    except:
        site = None
    return site

def getSubUserById(userId):
    try:
        subUser = Subuser.objects.get(pk=userId)
    except:
        subUser = None
    return subUser

def getSubUserByContactNo(contactNo):
    try:
        subUser = Subuser.objects.get(contactNo=contactNo,status=constants.Active)
    except:
        subUser = None
    return subUser

def getSubUserByEmail(email):
    try:
        subUser = Subuser.objects.get(email__iexact=email,status=constants.Active)
    except:
        subUser = None
    return subUser


def getActiveSubUserByName(userName):
    try:
        subUser = Subuser.objects.get(userName__iexact=userName,status=constants.Active)
    except:
        try:
            subUser = Subuser.objects.get(userName__iexact=userName)
            if subUser.status == constants.Disable:
                subUser = subUser
            else:
                subUser = None
        except:
            subUser = None
    return subUser


def notificationStatusChangeByID(id):
    try:
        notification = getNotificationById(id)
        notification.viewed = constants.Yes
        notification.save()
    except:
        notification = None
    return notification

def getPdfBasedOnOrderNo(orderNo,supplierId):
    try:
        pdf = pdfDetailsForPlacedOrder.objects.get(ordNumber__iexact=orderNo,supplierId=supplierId)
    except:
        pdf = None
    return pdf

def getOrderPlacementtoSupplierById(ordToSupId):
    try:
        order = OrderPlacementtoSupplier.objects.get(pk=ordToSupId)
    except:
        order = None
    return order

def getOrderPlacementfromCustomerById(ordFromCusId):
    try:
        order = OrderPlacementfromCustomer.objects.get(pk=ordFromCusId)
    except:
        order = None
    return order

def getalreadyOrderDupNum(ordNum):
    try:
        alreadyOrderDupNum = OrderPlacementtoSupplier.objects.get(ordNumber=ordNum)
    except:
        alreadyOrderDupNum = None
    return alreadyOrderDupNum

"""Method used to get the active count of the model by using modelName"""
def getCountOftheModelByModelName(modelName):
    try:
        model = getattr(sys.modules[__name__],modelName)
        count = model.objects.filter(status = constants.Active).count()
    except:
        count = 0
    return count

