import uuid,datetime
from django.core import serializers
from OrderTangoApp.models import *
from OrderTangoSubDomainApp.models import *
from django.db.models import F
from django.db import connection

def getObjectFromSession(request,sessionKey):
    sessionObject = request.session.get(sessionKey)
    obJect = list(serializers.deserialize("json", sessionObject))[0].object
    return obJect

def getUserByEmail(eMail):
    try:
        user = User.objects.get(email__iexact=eMail)
    except:
        user = None
    return user

def getUserByToken(tOken):
    try:
        user = User.objects.get(token=tOken)
    except:
        user = None
    return user

def getUserByUserId(iD):
    try:
        user = User.objects.get(pk=iD)
    except:
        user = None
    return user

def getCompanyByCompanyId(coMpanyId):
    try:
        company = Company.objects.get(companyId=coMpanyId)
    except:
        company = None
    return company

def getSchemaBySchemaName(sChemaName):
    try:
        schema = Schema.objects.get(schema_name=sChemaName)
    except:
        schema = None
    return schema

def getSchemaByDomainUrl(domainUrl):
    try:
        schema = Schema.objects.get(domain_url__iexact=domainUrl)
    except:
        schema = None
    return schema

def getSubUserByUserName(useRname):
    try:
        subUser = Subuser.objects.get(userName__iexact=useRname)
    except:
        subUser = None
    return subUser

def getRequestAccessURLByCompany(companyId):
    try:
        urls = RequestAccess.objects.filter(module_Id__in=Module.objects.filter(baseModuleId=baseModuleList.objects.get(
            planId=oTAccount.objects.get(companyId=companyId).plan_Id))).values_list('requestMap')
    except:
        urls = None
    return urls

def checkRequesURLisPresentForCompany(companyId,path):
    try:
        urls = RequestAccess.objects.filter(module_Id__in=Module.objects.filter(baseModuleId=baseModuleList.objects.get(
            planId=oTAccount.objects.get(companyId=companyId).plan_Id)),requestMap=path.replace('/','')).values()
    except:
        urls = None
    return urls

def checkRequesURLisPresentForSubUser(subUserId,path):
    try:
        urls = userSubReqAcc.objects.filter(subUserId=subUserId,subReqAccId__requestMap=path.replace('/','')).values()
    except:
        urls = None
    return urls

# order number generator method for create unique order number
def oTorderNumberGenerator():
    try:
        # Get the previous order number from the model
        otOrder = oTorder.objects.get(orderId=1)
        # Increment the order number by one and save into dataabase
        otOrder.orderType += 1
        otOrder.save()
        otOrderNumber = otOrder.orderType
    except:
        # Initialize the order number when table has no data
        oTorder.objects.create(orderId=1, orderType=1)
        otOrder = oTorder.objects.get(orderId=1)
        otOrderNumber = otOrder.orderType
    return otOrderNumber

# unique token generator for user
def uuIdTokenGenerator():
    token = uuid.uuid4().hex
    while True:
        # check the token number is already exist
        if userTokeneAlreadyExist(token):
            token = uuid.uuid4().hex
            continue
        else:
            break
    return token

def userTokeneAlreadyExist(token):
    try:
        user = User.objects.get(token=token)
    except:
        user = None
    return user

def oTcompanyCodeGenerator(companyName,countryCode):
    try:
        # Get the previous order number from the model
        otComToken = oTcompanyToken.objects.get(tokenId=1)
        # Increment the order number by one and save into dataabase
        otComToken.tokenType += 1
        otComToken.save()
        otToken = otComToken.tokenType
    except:
        # Initialize the order number when table has no data
        oTcompanyToken.objects.create(tokenId=1, tokenType=10001)
        otComToken = oTcompanyToken.objects.get(tokenId=1)
        otToken = otComToken.tokenType
    comName = companyName.replace(' ','')[:3]
    today = datetime.date.today()
    companyToken = str(countryCode)+str(today.year) + str(today.month).zfill(2)+comName+str(otToken).zfill(6)
    return companyToken.upper()

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

def setObjectToSession(sessionObject):
    obJect = serializers.serialize('json', [sessionObject, ])
    return obJect

def getCompanyBySchemaName(schemaName):
    try:
        company = Company.objects.get(schemaName__iexact=schemaName)
    except:
        company = None
    return company

def getCompanyByCompanyCode(companyCode):
    try:
        company = Company.objects.get(companyCode__iexact=companyCode)
    except:
        company = None
    return company

def getUserByCompanyId(companyId):
    try:
        user = User.objects.get(userCompanyId = companyId)
    except:
        user =None
    return user

def updateSessionforObject(request,sessionKey,model,pk):
    del request.session[sessionKey]
    sessionObject = model.objects.get(pk=pk)
    request.session[sessionKey] = setObjectToSession(sessionObject)
    return request

def getAreaByAreaName(areaName):
    try:
        area = Area.objects.get(areaName__iexact=areaName)
    except:
        area = None
    return area

def getSiteBySiteName(siteName):
    try:
        site = Sites.objects.get(siteName__iexact=siteName)
    except:
        site = None
    return site

def getSiteBySiteId(siteId):
    try:
        site = Sites.objects.get(pk=siteId)
    except:
        site = None
    return site

def getSlaBySlaName(slaName):
    try:
        sla = serviceLevelAgreement.objects.get(slaType__iexact=slaName)
    except:
        sla = None
    return sla

def getSlaBySlaId(slaId):
    try:
        sla = serviceLevelAgreement.objects.get(pk=slaId)
    except:
        sla = None
    return sla

def getCustomerListBasedonSla(slaId):
    try:
        customerList = list(Customer.objects.filter(customerSite__siteArea__areaSlaId_id__in=slaId).values('relId',
                        schemaName =F('trdersId__schemaName')))
    except:
        customerList = []
    return customerList

def getSupplierById(id):
    try:
        supplier = Supplier.objects.get(pk=id)
    except:
        supplier = None
    return supplier

def getCustomerById(id):
    try:
        customer = Customer.objects.get(pk=id)
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

def getSchemaMemorySize(schemaName):
    try:
        cursor = connection.cursor()
        query = "SELECT (sum(table_size) / database_size) * 100 FROM (SELECT pg_catalog.pg_namespace.nspname as schema_name,pg_relation_size(pg_catalog.pg_class.oid) as table_size, sum(pg_relation_size(pg_catalog.pg_class.oid)) over () as database_size FROM   pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON relnamespace = pg_catalog.pg_namespace.oid) t Where schema_name = '"+schemaName+"' GROUP BY schema_name,database_size"
        cursor.execute(query)
        size = cursor.fetchone()[0]
    except:
        size= 0
    #return in MB size(mega byte)
    return size

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

def getQuantityTypeByName(qtyType):
    try:
        qtyType = QuantityType.objects.get(quantityTypeCode__iexact=qtyType)
    except:
        qtyType = None
    return qtyType