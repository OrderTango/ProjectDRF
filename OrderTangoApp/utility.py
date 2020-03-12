import uuid,datetime,os
from django.core import serializers
from OrderTangoApp.models import *
from OrderTangoOrdermgmtApp.models import *
from django.db import connection
from OrderTango.settings import MEDIA_ROOT

"""Get the object from the request session by using sessionKey and request"""
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
        user = User.objects.get(token__iexact=tOken)
    except:
        user = None
    return user

def getUserByCompanyId(companyId):
    try:
        user = User.objects.get(userCompanyId = companyId)
    except:
        user =None
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

def getSchemaBySchemaName(sChemaName):
    try:
        schema = Schema.objects.get(schema_name__iexact=sChemaName)
    except:
        schema = None
    return schema

def getSchemaByDomainUrl(domainUrl):
    try:
        schema = Schema.objects.get(domain_url__iexact=domainUrl)
    except:
        schema = None
    return schema

def getRequestAccessURLByCompany(companyId):
    try:
        urls = RequestAccess.objects.filter(module__in=Module.objects.filter(planId=oTAccount.objects.get(
            companyId=companyId).plan_Id )).values_list('requestMap')
    except:
        urls = None
    return urls


"""Method is to check the request access is present for the company by using request URL and companyId"""
def checkRequesURLisPresentForCompany(companyId,path):
    try:
        if path == "":
            urls = RequestAccess.objects.filter(module__planId=
                                                oTAccount.objects.get(companyId=companyId).plan_Id)
        else:
            urls = RequestAccess.objects.filter(module__planId=
                                         oTAccount.objects.get(
                                             companyId=companyId).plan_Id,requestMap=path.replace('/',''))
    except:
        urls = None
    return urls


"""Method is to check the request access is present for the subuser/super-admin by using request URL and userId"""
def checkRequesURLisPresentForSubUser(subUser,path):
    try:
        companyId = getCompanyBySchemaName(connection.schema_name).companyId
        planId = oTAccount.objects.get(companyId=companyId).plan_Id
        if subUser.superAdmin:
            if subUser.accessRights != constants.Admin:
                urls = RequestAccess.objects.filter(module__planId=planId).values_list('requestMap', flat=True)
            else:
                urls = None
        else:
            if path != "":
                requestUrl =  RequestAccess.objects.get(module__planId=planId,requestMap__iexact=path.replace('/', ''))
                if requestUrl.pk in subUser.role.roleArray:
                    urls = RequestAccess.objects.filter(module__planId=planId,requestAccId__in =
                    subUser.role.roleArray).values_list('requestMap', flat=True)
                else:
                    urls = None
            else:
                urls = RequestAccess.objects.filter(module__planId=planId,
                                                    requestAccId__in=subUser.role.roleArray).values_list('requestMap',
                                                                                                         flat=True)
    except:
        urls = None
    return urls

"""order number generator method for create unique order number"""
def oTorderNumberGenerator(supId,supplierName):
    try:
        # Get the previous order number from the model
        orderPlacement = OrderPlacementtoSupplier.objects.filter(productId__supplierId=supId,orderType=constants.Orginal).last()
        ordNum  = orderPlacement.ordNumber
        if "-COPY" in ordNum:
            ordNum = ordNum[:-5]
        ordNumPartOne = str(ordNum[:8])
        ordNumPartTwo = str(int(ordNum[-7:])+1).zfill(7)
        otOrderNumber = ordNumPartOne+ordNumPartTwo
    except:
        # Initialize the order number when table has no data
        today = datetime.date.today()
        counts = "1"
        otOrderNumber = supplierName[:2].upper()+"-POA"+str(today.year)[2:]+counts.zfill(7)
    return otOrderNumber


"""unique token generator for user"""
def uuIdTokenGenerator():
    token = uuid.uuid4().hex
    while True:
        # check the token number is already exist
        if getUserByToken(token):
            token = uuid.uuid4().hex
            continue
        else:
            break
    return token


"""company code generator method for create unique company code"""
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


""""Method is to convert object as serialized json format for session"""
def setObjectToSession(sessionObject):
    obJect = serializers.serialize('json', [sessionObject, ])
    return obJect


""""Update the session object by using sessionKey,model object,object primary key"""
def updateSessionforObject(request,sessionKey,model,pk):
    del request.session[sessionKey]
    sessionObject = model.objects.get(pk=pk)
    request.session[sessionKey] = setObjectToSession(sessionObject)
    return request


"""Get the schema memory size by using schemaName"""
def getSchemaMemorySize(schemaName):
    try:
        cursor = connection.cursor()
        query = "SELECT (sum(table_size) / database_size) * 100 FROM (SELECT pg_catalog.pg_namespace.nspname " \
                "as schema_name,pg_relation_size(pg_catalog.pg_class.oid) as table_size," \
                " sum(pg_relation_size(pg_catalog.pg_class.oid)) over () as database_size FROM  " \
                " pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON relnamespace = pg_catalog.pg_namespace.oid) t " \
                "Where schema_name = '"+schemaName+"' GROUP BY schema_name,database_size"
        cursor.execute(query)
        size = cursor.fetchone()[0]
    except:
        size= 0
    #return in Bytes size(mega byte)
    return size * 1000000


def getQuantityTypeByName(qtyType):
    try:
        qtyType = QuantityType.objects.get(quantityTypeCode__iexact=qtyType)
    except:
        qtyType = None
    return qtyType

def getCurrencyTypeByCode(currencyCode):
    try:
        currency = CurrencyType.objects.get(currencyTypeCode__iexact=currencyCode)
    except:
        currency = None
    return currency


"""Method is to find differnce between two same type of model objects"""
def diffBertweenTwoObjects(obj1,obj2):
    return obj1.__dict__.items() ^ obj2.__dict__.items()


"""Method is to find differnce between two same type of model querysets"""
def diffBertweenTwoQuerySet(set1,set2):
    return set1.difference(set2)


"""Get the schema media files size by using schemaName"""
def getMediaSize(schemaName):
    path = MEDIA_ROOT + "/" + schemaName + "/"
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size
   #return size as  bytes format

def getoTAccountByCompany(company):
    try:
        account = oTAccount.objects.get(companyId=company)
    except:
        account = None
    return  account

def getStorageSizeByAllocation(storageAllocation):
    try:
        size = storageSize.objects.get(storageAllocation = storageAllocation)
    except:
        size = None
    return size

def getStorageAllocationById(storageAllocationId):
    try:
        storage = storageAllocation.objects.get(pk = storageAllocationId)
    except:
        storage = None
    return storage

"""Method is to check the plan features quantity is still present or not for the particular company. Parameters -
company = company object, modelName = plan feature model, currentCount = total count of plan feature model """
def checkEntryCountBasedOnPlanAndFeatures(company,modelName,currentCount):
    planFeatureCount = planFeaturesCountByCompanyAndModelName(company, modelName)
    if int(currentCount) < int(planFeatureCount):
        return True
    else:
        return False

def getUpgradeFeaturesByModelName(modelName):
    try:
        features = upgradeFeatures.objects.get(modelName__iexact=modelName)
    except:
        features = None
    return features

def getUpgradeFeatureBycategoryDetail(categoryDetail):
    try:
        features = upgradeFeatures.objects.get(categoryDetail__iexact=categoryDetail)
    except:
        features = None
    return features


def getAddOnFeaturesByAccountAndFeatures(account,features):
    try:
        addon = addonFeatures.objects.get(otAccountDetail=account,featuresDetails=features)
    except:
        addon = None
    return addon


def getRequestAccessByRequestUrl(path):
    try:
        requestAccess =  RequestAccess.objects.get(requestMap__iexact=path.replace('/', ''))
    except:
        requestAccess = None
    return requestAccess

"""Method is to get the plan features quantity for the particular company. Parameters -company = company object, 
modelName = plan feature model """
def planFeaturesCountByCompanyAndModelName(company,modelName):
    account = getoTAccountByCompany(company)
    planFeatures = account.plan_Id.planFeaturesJson
    features = getUpgradeFeaturesByModelName(modelName)
    categoryName = features.categoryDetail
    planFeatureCount = planFeatures[categoryName]
    addon = getAddOnFeaturesByAccountAndFeatures(account, features)
    if addon:
        planFeatureCount = int(planFeatureCount) + int(addon.categoryQty)
    return planFeatureCount


def getCountryCodeById(id):
    try:
        countryCode = CountryCode.objects.get(pk=id)
    except:
        countryCode = None
    return countryCode


def getUrlsAccessAddonModule(companyId,path):
    try:
        moduleId = RequestAccess.objects.get(requestMap=path.replace('/','')).module.moduleId
        urls = addOnModule.objects.get(modulesAccess=moduleId,otAccountDetail=oTAccount.objects.get(companyId=companyId))
    except:
        urls = None
    return urls

