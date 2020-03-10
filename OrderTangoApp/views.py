import csv
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.cache import cache_control
from django.contrib.sessions.models import Session
from OrderTangoApp.forms import *
from django.core.mail import EmailMessage
from django.contrib import messages
from OrderTangoApp.tokens import account_activation_token
import datetime
import os, io,  json
from django.core import serializers
import logging
import random
from django.db.models import  F
from OrderTangoSubDomainApp.forms import *
from django.views.decorators.csrf import csrf_exempt
from OrderTango.settings import IMPORT_FILES_FOLDER,MEDIA_ROOT
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from OrderTangoApp import utility, constants
from OrderTangoSubDomainApp.views import addInvitedCustomerOrSupplier
from OrderTangoSubDomainApp import utilitySD
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
import stripe


# console logger
logger = logging.getLogger(__name__)

# session time for expiration
time = settings.TIME

"""convert HTML to pdf conversion - PO pdf generation"""
def htmlToPdfConvertion(html,pdfName):
    initialise = open(MEDIA_ROOT +pdfName,"a+")
    initialise.close()
    file = open(MEDIA_ROOT +pdfName, "w+b")
    pisa.CreatePDF(html.encode('utf-8'), dest=file,encoding='utf-8')
    file.seek(0)
    file.read()
    file.close()
    return pdfName

# home page
def landingpage(request):
    return render(request, 'landingpage.html', {'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


"""Update plan HTML."""
def updateplan(request):
    if 'user' in request.session or 'subUser' in request.session:
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, "")
            superAdmin = False
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser,request.path)
            superAdmin = False
            if currentUser.superAdmin:
                if currentUser.accessRights != constants.Operational:
                    superAdmin = True
                else:
                    superAdmin = False
                    urls = None
        account = utility.getoTAccountByCompany(company)
        if urls or superAdmin:
            if superAdmin and currentUser.accessRights == constants.Admin:
                lengTh = 0
                notiFy = []
                urls = []
                subscribedModules = {}
            else:
                notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
                notiFy = notifiCation[:10]
                lengTh = len(notifiCation)
                subscribedModules = {}
                subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
                for sub in subscribed:
                    module = Module.objects.get(moduleId=sub['modulesAccess'])
                    subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'updateplan.html',
                      {'company': company, 'category':list(productCategory.objects.all()), 'user': currentUser,
                       'ProfileForm': ProfileForm,
                       'companyProfileForm': companyProfileForm,'urls': list(urls),
                       'subUserProfile': subUserProfile, 'status': company.urlchanged,
                       'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Account Info HTML - Page has create Super-Admin,Plan suspend,update addons and update storage functionalities """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def accountinfo(request):
    if 'user' in request.session  or 'subUser' in request.session:
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        subUserForm = SubUserFormDetails()
        editSubUserForm = EditSubUserFormDetails()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, "")
            mainUser = currentUser
            superAdmin = False
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser,request.path)
            superAdmin = False
            if currentUser.superAdmin:
               if currentUser.accessRights != constants.Operational:
                   superAdmin = True
               else:
                   superAdmin = False
                   urls = None
            mainUser = utility.getUserByCompanyId(company)
        account = utility.getoTAccountByCompany(company)
        if urls or superAdmin:
            if superAdmin and currentUser.accessRights == constants.Admin:
                lengTh = 0
                notiFy = []
                urls = []
                subscribedModules = {}
            else:
                notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
                notiFy = notifiCation[:10]
                lengTh = len(notifiCation)
                subscribedModules = {}
                subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
                for sub in subscribed:
                    module = Module.objects.get(moduleId=sub['modulesAccess'])
                    subscribedModules[module.moduleName] = module.moduleId
            accessusers = Subuser.objects.filter(superAdmin=True, status=constants.Active).order_by('subUserId')
            account = utility.getoTAccountByCompany(company)
            if account.planSuspended:
                planSuspend = 'Activate Service'
                planSuspendId = 'planActive'
            else:
                planSuspend = 'Suspend Service'
                planSuspendId = 'planSuspend'
            featuresJsons = getFeaturesJsonByCompany(account)
            planFeatures = featuresJsons[0]
            tableSpaceDetails = featuresJsons[1]
            plan = account.plan_Id
            planName = plan.planName
            cost = plan.cost
            storage = storageSize.objects.filter().values("storageSizeCode","storagePrice",
                                                                             "currencyType__currencyTypeCode",
                                                                          "storageAllocation__storageListId",
                                                                          "storageAllocation__storageListCode"

                                                                          )
            currencyType = plan.currencyType.currencyTypeCode
            #moduleList = Module.objects.filter(planId=plan).values('moduleName')
            moduleList = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess__moduleName')
            firstLogin = False
            if 'firstLogin' in request.session:
                del request.session['firstLogin']
                if account.planSuspended:
                    firstLogin = True
            return render(request, 'accountinfo.html',
                          {'company': company, 'category':list(productCategory.objects.all()), 'user': currentUser,
                           'profileForm': ProfileForm,'accessusers':accessusers,'mainUser':mainUser,
                           'companyProfileForm': companyProfileForm,'planFeatures':planFeatures,'planName':planName,
                           'moduleList':moduleList,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,'cost':cost,
                           'currencyType':currencyType,'firstLogin':firstLogin,
                           'noti': notiFy, 'urls': list(urls),'leng': lengTh,'tableSpaceDetails':tableSpaceDetails,
                           'storage':storage,'planSuspend':planSuspend,'planSuspendId':planSuspendId,
                           'subUserForm':subUserForm,'editSubUserForm':editSubUserForm,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


""" Method is used to get the addon features based on their purchases """
def getFeaturesJsonByCompany(account):
    masterJson = {}
    tableJson = {}
    planFeatures = account.plan_Id.planFeaturesJson
    for key,value in planFeatures.items():
        if int(value)>0:
            features = utility.getUpgradeFeatureBycategoryDetail(key)
            addon = utility.getAddOnFeaturesByAccountAndFeatures(account,features)
            categoryQty = 0
            totalQty = float(value)
            usedQty = utilitySD.getCountOftheModelByModelName(features.modelName)
            if addon:
                categoryQty = addon.categoryQty
                totalQty += categoryQty
            masterJson[key] = [value,int(categoryQty),features.categoryPrice,
                               features.categoryPriceUnit.currencyTypeCode]
            tableJson[key] = [int(totalQty),int(usedQty)]
    return masterJson,tableJson


"""Sale catalog-Create HTML - Page has create new sales catalog functionality """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productsalescatalog(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'productsalescatalog.html',
                          {'company': company,'urls':list(urls), 'category':list(productCategory.objects.all()),
                           'user': currentUser, 'form': userForm, 'profileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Sale catalog-View HTML - Page has update sales catalog functionality """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productsalescatalogview(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, 'productsalescatalog')
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, 'productsalescatalog')
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            catalog = list(ProductCatalogForSale.objects.filter(status = constants.Active).values(
                'catalogName','salePrdtCatId'))
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'productsalescatalogview.html',
                          {'company': company,'urls':list(urls), 'category':list(productCategory.objects.all()),
                           'user': currentUser, 'form': userForm, 'profileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,'catalog':catalog,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Sale catalog-Update HTML - Page has add new product to the existing sales catalog functionality """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productsalescatalogupdate(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, 'productsalescatalog')
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, 'productsalescatalog')
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            catalog = list(ProductCatalogForSale.objects.filter(status = constants.Active).values(
                'catalogName','salePrdtCatId'))
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'productsalescatalogupdate.html',
                          {'company': company, 'urls':list(urls),'category':list(productCategory.objects.all()),
                           'user': currentUser, 'form': userForm, 'profileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,'catalog':catalog,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Purchase catalog-Create HTML - Page has create new purchase catalog functionality """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productpurchasecatalog(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'productpurchasecatalog.html',
                          {'company': company,'urls':list(urls), 'category':list(productCategory.objects.all()),
                           'user': currentUser, 'form': userForm, 'profileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Purchase catalog-Update HTML - Page has add new product to the existing purchase catalog functionality """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productpurchasecatalogupdate(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, 'productpurchasecatalog')
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, 'productpurchasecatalog')
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            catalog = list(ProductCatalogForPurchase.objects.filter(status = constants.Active).values(
                'catalogName','purPrdtCatId'))
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'productpurchasecatalogupdate.html',
                          {'company': company, 'urls':list(urls),'category':list(productCategory.objects.all()),
                           'user': currentUser, 'form': userForm, 'profileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,'catalog':catalog,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Purchase catalog-View HTML - Page has update purchase catalog functionality """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productpurchasecatalogview(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, 'productpurchasecatalog')
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, 'productpurchasecatalog')
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            catalog = list(ProductCatalogForPurchase.objects.filter(status = constants.Active).values(
                'catalogName','purPrdtCatId'))
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'productpurchasecatalogview.html',
                          {'company': company,'urls':list(urls), 'category':list(productCategory.objects.all()),
                           'user': currentUser, 'form': userForm, 'profileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,'catalog':catalog,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


def subscription(request):
    return render(request, 'subscriptionnew.html', {'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


"""Create customer,supplier and product by manual or csv upload Page."""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def administrationpanel(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'administrationpanel.html',
                          {'company': company,'urls':list(urls), 'user': currentUser, 'form': userForm,
                           'ProfileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""View Placed order HTML - Page has update/proceed placed order from customer"""
@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def vieworders(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            addOnModuleUrls = utility.getUrlsAccessAddonModule(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls or addOnModuleUrls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'vieworders.html',
                          {'company': company,'urls':list(urls), 'user': currentUser, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,
                           'leng': lengTh,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



"""Operational panel HTML"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def operationalpanel(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            firstLogin =False
            if 'firstLogin' in request.session:
                del request.session['firstLogin']
                account = utility.getoTAccountByCompany(company)
                if account.planSuspended:
                    firstLogin = True
            return render(request, 'operationalpanel.html',
                          {'company': company,'urls':list(urls), 'user': currentUser, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,'firstLogin':firstLogin,
                           'leng': lengTh,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/accountinfo')
    return HttpResponseRedirect('/login/')


""" Email validation for registered users """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def validation(request):
    if 'emailBeforevalidation' in request.session:
        wsid = ''
        if 'wsid' in request.session:
            wsid = request.session['wsid']
        return render(request, 'validation.html', {'email': request.session['emailBeforevalidation'],'wsid': wsid})
    else:
        request.session.flush()
        messages.error(request, 'Session Expired!')
        return HttpResponseRedirect('/login/')


"""Sending email functionality. Method used to send all types of email with or without attachements,
Parameters user = mail sender information, email = to email information, otp = generated pin or sometimes extra objects,
html = template for generating messaging content, subject = mail subject, domain = mail receiver domain information,
 attachment = files, wsid = security token """
def sendingEmail(request, user, email, otp, html, subject, domain, attachment,wsid):
    try:
        requestSchema = utility.getSchemaBySchemaName(otp.userCompanyId.schemaName).domain_url.split('.')[0]
    except:
        requestSchema = None
    message = render_to_string(html, {
        'user': user, 'domain': domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'token': account_activation_token.make_token(user),
        'otp': otp, 'main_url': request.get_host().replace(request.get_host().split('.')[0], ""),
        'domain_url': requestSchema,'wsid':wsid
    })
    mail_subject = subject
    to_email = email
    email = EmailMessage(mail_subject, message, to=[to_email])
    if attachment:
        email.attach_file(MEDIA_ROOT+attachment)
        email.send()
    else:
        email.send()


""" Generate 4 digits numeric random numbers"""
def otpGenerator():
    generatedOtp = str(random.randint(1000, 10000))
    return generatedOtp


"""Registration - Registration functionalities with user defined validations, Save the User with status as inactive """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def registration(request):
    if request.method == 'POST':
        userForm = UserForm(request.POST)
        companyForm = CompanyForm(request.POST)
        if userForm.is_valid() and companyForm.is_valid():
            email = userForm.cleaned_data.get('email').lower()
            try:
                token = userForm.cleaned_data.get('wsid')
            except:
                token = None
            user = userForm.save(commit=False)
            company = companyForm.save(commit=False)
            user.token = utility.uuIdTokenGenerator()
            user.password = make_password(userForm.cleaned_data.get('password'))
            company.companyCode = utility.oTcompanyCodeGenerator(company.companyName, company.country.countryCode)
            company.save()
            otp = otpGenerator()
            user.otp = otp
            user.userCompanyId = company
            user.email = email
            user.sec_answer = userForm.cleaned_data.get('sec_answer').lower()
            user.save()
            storage = storageAllocation.objects.get(planDetail_id=request.POST['plan'])
            oTAccountPlan = oTAccount()
            oTAccountPlan.plan_Id_id = request.POST['plan']
            oTAccountPlan.storageAllocation_id = storage
            storageSizeCode = utility.getStorageSizeByAllocation(storage).storageSizeCode
            if constants.MegaByte in storageSizeCode:
                storageSizeCode = float(storageSizeCode.replace(constants.MegaByte , "")) * 1000000
            else:
                storageSizeCode = float(storageSizeCode.replace(constants.GegaByte, "")) * 1000000000
            oTAccountPlan.storageSize = str(storageSizeCode)
            oTAccountPlan.companyId_id = company
            oTAccountPlan.status = constants.Active
            oTAccountPlan.save()
            if request.POST['plan'] == str(1):
                moduleSaving = addOnModule()
                moduleSaving.otAccountDetail = oTAccountPlan
                moduleSaving.save()
                for a in [1]:
                    x = Module.objects.get(moduleId=a)
                    moduleSaving.modulesAccess.add(x)
                    moduleSaving.save()
            elif request.POST['plan'] == str(2):
                moduleSaving = addOnModule()
                moduleSaving.otAccountDetail = oTAccountPlan
                moduleSaving.save()
                for a in [1,2]:
                    x = Module.objects.get(moduleId=a)
                    moduleSaving.modulesAccess.add(x)
                    moduleSaving.save()
            elif request.POST['plan'] == str(3):
                moduleSaving = addOnModule()
                moduleSaving.otAccountDetail = oTAccountPlan
                moduleSaving.save()
                for a in [1,2,3]:
                    x = Module.objects.get(moduleId=a)
                    moduleSaving.modulesAccess.add(x)
                    moduleSaving.save()
            else:
                moduleSaving = addOnModule()
                moduleSaving.otAccountDetail = oTAccountPlan
                moduleSaving.save()
                for a in [1, 2, 3]:
                    x = Module.objects.get(moduleId=a)
                    moduleSaving.modulesAccess.add(x)
                    moduleSaving.save()
            sendingEmail(request, user, email, user.otp, 'acc_active_email.html', 'Activate your account',
                         request.get_host(), None,token)
            request.session["emailBeforevalidation"] = email
            request.session["otpCount"] = 0
            if token:
                request.session["wsid"] = token
            return HttpResponseRedirect('/validation/')
        else:
            return render(request, 'registration.html',
                          {'form': userForm, 'companyform': companyForm,
                           'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
    else:
        wsid= None
        if request.GET.get('wsid', None) is not None:
            wsid = request.GET.get('wsid', '')
    userForm = UserForm(initial={'wsid': wsid})
    companyForm = CompanyForm(initial={'companyWsid': wsid})
    return render(request, 'registration.html',
                  {'form': userForm, 'companyform': companyForm,
                   'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


"""Login - Both primary and sub domain login functionalities with user defined validations"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login(request):
    if request.method == 'POST':
        loginform = LoginForm(request.POST)
        email = request.POST['email'].lower()
        password = request.POST['password']
        if email and password is not None:
            user = utility.getUserByEmail(email)
            rootUrl = request.get_host()
            www = ""
            if request.get_host().startswith('www.'):
                rootUrl = request.get_host().replace('www.', '')
                www = 'www.'
            if user is not None:
                if user.userCompanyId.verificationStatus == constants.Active:
                    if check_password(password, user.password):
                        if settings.DOMAIN_NAME not in rootUrl:
                            userSchema = Schema.objects.get(schema_name=user.userCompanyId.schemaName)
                            url = userSchema.domain_url
                            connection.set_schema(schema_name=user.userCompanyId.schemaName)
                            request.session.create()
                            request.session['user'] = utility.setObjectToSession(user)
                            request.session.modified = True
                            wsid = request.session._session_key
                            user.lastLogin = datetime.datetime.now()
                            user.save()
                            return HttpResponseRedirect(
                                settings.HTTP + www + url + ':' + settings.PORT + '/dashboard?wsid=' + wsid)
                        else:
                            if connection.schema_name == user.userCompanyId.schemaName:
                                if 'subUser' in request.session:
                                    messages.error(request, 'Already other user in session.Try after some time.')
                                    return render(request, 'login.html',
                                                  {'form1': loginform,
                                                   'emailError': "",
                                                   'passError': "",
                                                   'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                                request.session['user'] = utility.setObjectToSession(user)
                                request.session['firstLogin'] = True
                                request.session.modified = True
                                user.lastLogin = datetime.datetime.now()
                                user.save()
                                return HttpResponseRedirect('/dashboard/')
                            else:
                                return render(request, 'login.html',
                                              {'form1': loginform, 'emailError': "Incorrect Username", 'passError': "",
                                               'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                    else:
                        return render(request, 'login.html',
                                      {'form1': loginform, 'emailError': "",
                                       'passError': "Password does not match",
                                       'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                else:
                    return render(request, 'login.html',
                                  {'form1': loginform, 'emailError': "Please activate your account", 'passError': "",
                                   'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
            else:

                if settings.DOMAIN_NAME in rootUrl:
                    if 'user' in request.session:
                        messages.error(request, 'Already other user in session.Try after some time.')
                        return render(request, 'login.html',
                                      {'form1': loginform,
                                       'emailError': "",
                                       'passError': "",
                                       'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                    elif 'subUser' in request.session:
                        messages.error(request, 'Already other user in session.Try after some time.')
                        return render(request, 'login.html',
                                      {'form1': loginform,
                                       'emailError': "",
                                       'passError': "",
                                       'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                    subUser = utilitySD.getActiveSubUserByName(email)
                    if subUser:
                        if subUser.status == constants.Active:
                            if check_password(password, subUser.password):
                                subUser.lastLogin = datetime.datetime.now()
                                subUser.save()
                                request.session["subUser"] = utility.setObjectToSession(subUser)
                                request.session['firstLogin'] = True
                                request.session.modified = True
                                return HttpResponseRedirect('/dashboard/')
                            else:
                                return render(request, 'login.html',
                                              {'form1': loginform, 'emailError': "",
                                               'passError': "Password does not match",
                                               'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                        elif subUser.status == constants.Disable:
                            return render(request, 'login.html',
                                          {'form1': loginform, 'emailError': "You are disabled please contact admin",
                                           'passError': "",
                                           'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                    else:
                        return render(request, 'login.html',
                                      {'form1': loginform, 'emailError': "Incorrect Username", 'passError': "",
                                       'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})

                else:
                    try:
                        subUserName = email.split('@')
                        url = subUserName[1] + settings.DOMAIN_NAME
                        schema = Schema.objects.get(domain_url__iexact=url)
                        connection.set_schema(schema_name=schema.schema_name)
                        subUser = utilitySD.getActiveSubUserByName(subUserName[0])
                    except:
                        subUser = None
                        url = ""
                        connection.set_schema_to_public()
                    if subUser:
                        if subUser.status == constants.Active:
                            if check_password(password, subUser.password):
                                subUser.lastLogin = datetime.datetime.now()
                                subUser.save()
                                request.session.create()
                                request.session["subUser"] = utility.setObjectToSession(subUser)
                                request.session.modified = True
                                wsid = request.session._session_key
                                return HttpResponseRedirect(
                                    settings.HTTP + www + url + ':' + settings.PORT + '/dashboard?wsid=' + wsid)
                            else:
                                return render(request, 'login.html',
                                              {'form1': loginform, 'emailError': "",
                                               'passError': "Password does not match",
                                               'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                        elif subUser.status == constants.Disable:
                            return render(request, 'login.html',
                                          {'form1': loginform, 'emailError': "You are disabled please contact admin", 'passError': "",
                                           'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
                    else:
                        return render(request, 'login.html',
                                      {'form1': loginform, 'emailError': "Incorrect Username", 'passError': "",
                                       'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})

        else:
            if email is None:
                return render(request, 'login.html',
                              {'form1': loginform, 'emailError': "Enter the Email/Username", 'passError': "",
                               'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
            elif password is None:
                return render(request, 'login.html',
                              {'form1': loginform, 'emailError': "Enter the Password", 'passError': "",
                               'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
    else:
        if "wsid" in request.GET:
            loginform = LoginForm()
            messages.error(request, 'Already other user in session.Try after some time.')
            return render(request, 'login.html',
                          {'form1': loginform, 'emailError': "", 'passError': "",
                           'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
        elif 'user' in request.session or 'subUser' in request.session:
            return HttpResponseRedirect('/dashboard/')
        else:
            loginform = LoginForm()
            return render(request, 'login.html',
                          {'form1': loginform, 'emailError': "", 'passError': "",
                           'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


""" loading states from table based on selection country """
def load_states(request):
    country_id = request.GET.get('country_id')
    states = State.objects.filter(country_id=country_id).order_by('stateName')
    data = serializers.serialize('json', states)
    return JsonResponse({'states': data})


""" loading country from table """
def load_country(request):
    country = Country.objects.all().order_by('countryName')
    data = serializers.serialize('json', country)
    return JsonResponse({'country': data})


"""Admin Dashboard - Method used to redirecting the login users with specified schema and domain """
@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dashboard(request):
    try:
        sessions = Session.objects.get(session_key=request.GET.get('wsid', ''))
        session_data = sessions.get_decoded()
        session_time = sessions.expire_date

    except:
        session_data = None
    if session_data:
        try:
            user = list(serializers.deserialize("json", session_data.get('user', None)))[0].object
        except:
            user = None
        try:
            subUser = list(serializers.deserialize("json", session_data.get('subUser', None)))[0].object
        except:
            subUser = None
        if (user or subUser is not None) and datetime.datetime.now() - session_time < datetime.timedelta(0, time):
            Session.objects.get(session_key=request.GET.get('wsid', '')).delete()
            if user:
                if 'subUser' in request.session:
                    return HttpResponseRedirect(settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT
                                                +'/login?wsid='
                                                +request.GET.get('wsid', ''))
                request.session['user'] = utility.setObjectToSession(user)
                request.session['firstLogin'] = True
                response = adminPanel(request, user, None)
            else:
                if 'user' in request.session:
                    return HttpResponseRedirect(settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT
                                                + '/login?wsid='
                                                +request.GET.get('wsid', ''))
                elif 'subUser' in request.session:
                    return HttpResponseRedirect(settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT
                                                + '/login?wsid='
                                                +request.GET.get('wsid', ''))
                request.session['subUser'] = utility.setObjectToSession(subUser)
                request.session['firstLogin'] = True
                response = adminPanel(request, None, subUser)
            request.session.modified = True
            return response
    elif 'user' in request.session:
        user = utility.getObjectFromSession(request, 'user')
        response = adminPanel(request, user, None)
        return response
    elif 'subUser' in request.session:
        subUser = utility.getObjectFromSession(request, 'subUser')
        response = adminPanel(request, None, subUser)
        return response
    request.session.flush()
    return HttpResponseRedirect('/login/')


"""Admin Panel HTML - Page has view/edit customer,supplier and product functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminPanel(request, user, subUser):
    profileForm = UserProfileForm()
    companyProfileForm = CompanyProfileForm()
    if subUser:
        currentUser = subUser
        subUserProfile = constants.Yes
        company = utility.getCompanyBySchemaName(connection.schema_name)
        urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
    else:
        currentUser = user
        subUserProfile = constants.No
        company = user.userCompanyId
        urls = utility.checkRequesURLisPresentForCompany(company.companyId, request.path)
    account = utility.getoTAccountByCompany(company)
    if user or subUser is not None:
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            itemMasterAddForm = EditItemMasterManualForm()
            attributeForm = EditproductAttributeForm()
            purchasingForm = EditpurchasingItemsForm()
            salesForm = EditsalesItemsForm()
            measurementForm = EdititemMeasurementForm()
            storageForm = EdititemStorageForm()
            parameterForm = EdititemParameterForm()
            customerForm = CustomerManualAddingForm()
            customerShippingForm = CustomerShippingAddressForm()
            supplierForm = SupplierManualAddingForm()
            supplierShippingForm = SupplierShippingAddressForm()
            firstLogin = False
            if 'firstLogin' in request.session:
                del request.session['firstLogin']
                account = utility.getoTAccountByCompany(company)
                if account.planSuspended:
                    firstLogin = True
            return render(request, 'viewall.html',
                          {'company': company,'urls':list(urls), 'user': currentUser, 'profileForm': profileForm,
                           'customerForm':customerForm,'customerShippingForm':customerShippingForm,
                           'companyProfileForm': companyProfileForm, 'itemMasterAddForm': itemMasterAddForm,
                           'storageForm': storageForm,'attributeForm': attributeForm,'purchasingForm':purchasingForm,
                           'salesForm':salesForm,'measurementForm':measurementForm,'parameterForm':parameterForm,
                           'subUserProfile': subUserProfile,'noti': notiFy, 'status': company.urlchanged,
                           'supplierForm': supplierForm,'supplierShippingForm': supplierShippingForm,
                           'leng': lengTh,'firstLogin':firstLogin,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/operationalpanel/')
    else:
        return HttpResponseRedirect('/registration/')


""" user logged out functionality - flush all the session from request and redirected to login page"""
def logout(request):
    request.session.flush()
    return HttpResponseRedirect('/login/')


"""Forget password for registered users - sending email link for change password"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def forgetpassword(request):
    if request.method == 'POST':
        Forgetform = ForgetpasswordForm(request.POST)
        email = request.POST['email'].lower()
        if Forgetform.is_valid():
            user = utility.getUserByEmail(email)
            user.updatedDateTime = datetime.datetime.now()
            user.save()
            sendingEmail(request, user, email, None, 'forgot_password_email.html', 'Change your password',
                         request.get_host(), None,None)
            messages.error(request, 'Change password link has been sent to your mail')
            return HttpResponseRedirect('/forgetpassword/')
        else:
            return render(request, 'forgetpassword.html', {'form1': Forgetform})
    else:
        Forgetform = ForgetpasswordForm()
        return render(request, 'forgetpassword.html', {'form1': Forgetform})


""" Password change form with getting user from URL path """
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def newpassword(request, uidb64, token):
    newPassForm = newpasswordForm()
    uid = force_text(urlsafe_base64_decode(uidb64))
    user = utility.getUserByUserId(uid)
    if user is not None:
        timenow = datetime.datetime.now()
        updatedtime = user.updatedDateTime
        if account_activation_token.check_token(user, token) and timenow - updatedtime < datetime.timedelta(0, time):
            return render(request, 'newpassword.html', {'form1': newPassForm, 'email': user.email.lower()})
    messages.error(request, 'Link is Expired!')
    return HttpResponseRedirect('/forgetpassword/')


"""change password method with password validations and redirecting dashboard - generating encrypted password 
using sha-256 algorithm"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def changePassword(request):
    if request.method == 'POST' and request.POST['emailId'] is not None:
        newPassForm = newpasswordForm(request.POST)
        if newPassForm.is_valid():
            email = request.POST['emailId'].lower()
            user = utility.getUserByEmail(email)
            if user is not None:
                pwd = request.POST['password']
                user.password = make_password(pwd)
                user.save()
                userSchema = Schema.objects.get(schema_name=user.userCompanyId.schemaName)
                if settings.DOMAIN_NAME not in request.build_absolute_uri():
                    url = userSchema.domain_url
                    request.session.flush()
                    connection.set_schema(schema_name=user.userCompanyId.schemaName)
                    request.session.create()
                    request.session["user"] = utility.setObjectToSession(user)
                    request.session.modified = True
                    wsid = request.session._session_key
                    return HttpResponseRedirect(settings.HTTP + url + ':' + settings.PORT + '/dashboard?wsid=' + wsid)
                else:
                    request.session.flush()
                    request.session["user"] = utility.setObjectToSession(user)
                    request.session.modified = True
                    return HttpResponseRedirect('/dashboard/')
            else:
                return HttpResponseRedirect('/registration/')

        else:
            return render(request, 'newpassword.html', {'form1': newPassForm, 'email': request.POST['emailId'].lower()})

    else:
        return HttpResponseRedirect('/login/')


"""validate the entered otp and change the user status as active when the entered OTP is correct and also schema is 
generated with requested plan,site,area,sla and if any invited customer/supplier
present in the URL is added into the system"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def validateotp(request):
    if request.method == 'POST' and 'emailBeforevalidation' in request.session and 'otpCount' in request.session:
        email = request.session["emailBeforevalidation"]
        user = utility.getUserByEmail(email)
        # check the user is inactive
        if user.userCompanyId.verificationStatus != constants.Active:
            # get the generated otp for the user
            savedOtp = user.otp
            # get the entered otp from the form
            enterOtp = request.POST['otp']
            updatedtime = user.updatedDateTime
            timenow = datetime.datetime.now()
            # setting the otp attempts count
            #request.session["otpCount"] += 1
            # check the otp attempt reaches the less than 3
            #if request.session["otpCount"] <= 3 and savedOtp == enterOtp:
            if savedOtp == enterOtp:
                # session expiration check
                if timenow - updatedtime < datetime.timedelta(0, time):
                    # set the user status as active
                    company = utility.getCompanyByCompanyId(user.userCompanyId)
                    company.verificationStatus = constants.Active
                    wsid = None
                    if 'wsid' in request.session:
                        wsid = request.session['wsid']
                    request.session.flush()
                    company.save()
                    # check the user is having schema
                    if not user.userCompanyId.schemaName:
                        # create the schema for the user
                        company = Company.objects.get(pk=user.userCompanyId)
                        tenantSchema(company)
                        currentSchema = connection.schema_name
                        connection.set_schema(schema_name=company.schemaName)
                        defaultAreaSiteAndSlaCreation(company)
                        if wsid:
                            addInvitedCustomerOrSupplier(wsid, company.companyName)
                        connection.set_schema(schema_name=currentSchema)
                    return render(request, 'onboard.html', {'email': email})

                # entered otp is correct but session is expired
                elif timenow - updatedtime >= datetime.timedelta(0, time):
                    # redirect to security question form
                    wsid = ''
                    if 'wsid' in request.session:
                        wsid = request.session['wsid']
                    secQuesForm = securityQuestionForm()
                    messages.error(request, "Link is Expired!")
                    # get the security question for the user
                    security = SecurityQuestion.objects.get(pk=user.sec_question.securityQuestionId)
                    question = security.securityQuestionName
                    return render(request, 'securityquestion.html',
                                  {'form1': secQuesForm, 'email': email, 'question': question,'wsid':wsid})
                # entered otp is incorrect and session also expired
                else:
                    # redirect to login page
                    request.session.flush()
                    messages.error(request, 'Session Expired!')
                    messages.error(request, 'Please click on the activation link sent to your mail')
                    return HttpResponseRedirect('/login/')
            else:
                messages.error(request, "Please enter the valid otp")
                return HttpResponseRedirect('/validation/')
        # user is already active then it will redirect to login page
        else:
            request.session.flush()
            messages.error(request, 'You have already registered')
            return HttpResponseRedirect('/login/')
    # form is not submitted but user in session then it will redirect to security question form
    else:
        if 'emailBeforevalidation' in request.session:
            user = utility.getUserByEmail(request.session["emailBeforevalidation"])
            secQuesForm = securityQuestionForm()
            # get the security question for the user
            security = SecurityQuestion.objects.get(pk=user.sec_question.securityQuestionId)
            question = security.securityQuestionName
            return render(request, 'securityquestion.html',
                          {'form1': secQuesForm, 'email': request.session["emailBeforevalidation"],
                           'question': question})
        # user not in the session it will redirected to login page
        else:
            request.session.flush()
            messages.error(request, "Session Expired!")
            return HttpResponseRedirect('/login/')


"""Resent otp functionality"""
@csrf_exempt
def resendotp(request):
    if request.method == 'POST' and 'emailBeforevalidation' in request.session and 'otpCount' in request.session:
        email = request.session["emailBeforevalidation"]
        user = utility.getUserByEmail(email)
        if user.userCompanyId.verificationStatus != constants.Active:
             # reset the otp attempt count
            request.session["otpCount"] = 0
            # send the otp via Email
            sendingEmail(request, user, email, user.otp, 'acc_active_email.html', 'Activate your account',
                         request.get_host(), None, None)
            return JsonResponse({'status': 'success', 'success_msg': 'OTP has been sent to your mail.',
                                 })
        else:
            request.session.flush()
            return JsonResponse({'status': 'success', 'success_msg': 'You have already registered',
                                 })
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""security question verification and change the user status as active when the entered answer is correct and also 
schema is generated with requested plan,site,area,sla and if any invited customer/supplier
present in the URL is added into the system"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def securityquestion(request):
    if request.method == 'POST' and request.POST['emailId'] is not None:
        secQuesForm = securityQuestionForm(request.POST)
        # get the email from the submitted form
        email = request.POST['emailId'].lower()
        # get the entered answer from the submitted form
        enterAnswer = request.POST['sec_answer'].lower()
        user = utility.getUserByEmail(email)
        if user is not None:
            # check the user is inactive
            if user.userCompanyId.verificationStatus != constants.Active:
                # get the answer for the user
                savedAnswer = user.sec_answer.lower()
                if enterAnswer == savedAnswer:
                    # set the user status as active
                    company = utility.getCompanyByCompanyId(user.userCompanyId)
                    company.verificationStatus = constants.Active
                    request.session.flush()
                    company.save()
                    # check the user is having schema
                    if not user.userCompanyId.schemaName:
                        # create the schema for the user
                        tenantSchema(company)
                        currentSchema = connection.schema_name
                        connection.set_schema(schema_name=company.schemaName)
                        defaultAreaSiteAndSlaCreation(company)
                        if request.POST['wsid']:
                            addInvitedCustomerOrSupplier(request.session['wsid'], company.companyName)
                        connection.set_schema(schema_name=currentSchema)
                    return render(request, 'onboard.html', {'email': email})
                # entered answer is incorrect it will redirect to security quesstion page with errors
                else:
                    messages.error(request, "Please enter the correct answer")
                    secQuesForm = securityQuestionForm()
                    security = SecurityQuestion.objects.get(pk=user.sec_question.securityQuestionId)
                    question = security.securityQuestionName
                    return render(request, 'securityquestion.html',
                                  {'form1': secQuesForm, 'email': user.email, 'question': question})
            # user is already active then it will redirect to login page
            else:
                messages.error(request, 'You have already registered')
                return HttpResponseRedirect('/login/')
        # user is not in the system it will redirect to registration page
        else:
            return HttpResponseRedirect('/registration/')
    # user not in the session it will redirected to login page
    else:
        request.session.flush()
        messages.error(request, "Session Expired!")
        return HttpResponseRedirect('/login/')


"""Activate the user by hyperlink - getting the user from URL path and activate the user when the period of time is 
not exceeded the limit and also schema is generated with requested plan,site,area,sla and if any invited 
customer/supplier present in the URL is added into the system"""
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = utility.getUserByUserId(uid)
    except:
        user = None
    if user is not None:
        updatedtime = user.updatedDateTime
        timenow = datetime.datetime.now()
        # check the user is inactive
        if user.userCompanyId.verificationStatus != constants.Active:
            # session expiration check
            if timenow - updatedtime < datetime.timedelta(0, time):
                # check the user is correct
                if account_activation_token.check_token(user, token):
                    user.is_active = True
                    # set the user status as active
                    # check the user is having schema
                    if not user.userCompanyId.schemaName:
                        # create the schema for the user
                        company = Company.objects.get(pk=user.userCompanyId)
                        tenantSchema(company)
                        currentSchema = connection.schema_name
                        connection.set_schema(schema_name=company.schemaName)
                        defaultAreaSiteAndSlaCreation(company)
                        if request.GET.get('wsid', None) is not None:
                            addInvitedCustomerOrSupplier(request.GET.get('wsid'), company.companyName)
                        connection.set_schema(schema_name=currentSchema)
                    company = utility.getCompanyByCompanyId(user.userCompanyId)
                    company.verificationStatus = constants.Active
                    company.save()
                    return render(request, 'onboard.html', {'email': user.email.lower()})
                # user details is incorrect it will redirect to login page
                else:
                    messages.error(request, "Activation link is Expired!")
                    return HttpResponseRedirect('/login/')
            # session is expired it will redirect to security question form
            else:
                secQuesForm = securityQuestionForm()
                messages.error(request, "Link is Expired!")
                security = SecurityQuestion.objects.get(pk=user.sec_question.securityQuestionId)
                question = security.securityQuestionName
                return render(request, 'securityquestion.html',
                              {'form1': secQuesForm, 'email': user.email.lower(), 'question': question})
        # user is already active then it will redirect to login page
        else:
            messages.error(request, 'You have already registered')
            return HttpResponseRedirect('/login/')
    # user is not in the system it will redirect to registration page
    else:
        return HttpResponseRedirect('/registration/')


"""Onboard page- After successful activation the user redirected into their respective schema and domain"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def onboard(request):
    if request.method == "POST":
        # get the email from the submitted form
        email = request.POST.get('emailId', None)
        if email is not None:
            user = utility.getUserByEmail(email)
            if user is not None:
                # getting the schema for the user from schema table
                userSchema = Schema.objects.get(schema_name=user.userCompanyId.schemaName)
                # getting the schema url for the user
                url = userSchema.domain_url
                # connect the schema of the user
                connection.set_schema(schema_name=user.userCompanyId.schemaName)
                # create session for the user
                request.session.create()
                # setting email in to session
                request.session["user"] = utility.setObjectToSession(user)
                user.lastLogin = datetime.datetime.now()
                user.save()
                # setting session auto modification is true for every request
                request.session.modified = True
                # get the created session key as wsid for login
                wsid = request.session._session_key
                return HttpResponseRedirect(settings.HTTP + url + ':' + settings.PORT + '/dashboard?wsid=' + wsid)
    # user is not in the system or not in session it will redirect to login page
    return HttpResponseRedirect('/login/')


""" method is used get the details as dictionaries from csv and save into model """
def modelSave(listCsv, modelName):
    # takes an object and produces a string
    dumps = json.dumps(listCsv)
    # would take a file-like object, read the data from that object, and use that string to create an object
    load = json.loads(dumps)
    for dictionaries in load:
        # save the object in to model
        model = modelName(**dictionaries)
        model.save()
    return True


""" create schema with auto generated schema name """
def tenantSchema(company):
    # getting the current schema from the connection
    currentSchema = connection.schema_name
    # set the connection schema in to public
    connection.set_schema_to_public()
    # creating unique schema for the user
    name = 'ot' + uuid.uuid4().hex[:8].lower()
    while True:
        # check the schema name already exists in the system
        if utility.getSchemaBySchemaName(name):
            # recreate the unique schema
            name = 'ot' + uuid.uuid4().hex[:8].lower()
            continue
        else:
            break
    # getting the user company name
    companyName = company.companyName
    # create tenant schema
    tenant = Schema(domain_url=name + settings.DOMAIN_NAME,
                    schema_name=name,
                    schemaCompanyName=companyName,
                    )
    tenant.save()
    company.schemaName = name
    company.save()
    # reset the connection to current schema
    connection.set_schema(schema_name=currentSchema)
    return name


"""Rename the schema URL based on the user request"""
def renameSchemaURL(request):
    if 'user' in request.session and request.POST['domainName'] is not None:
        # get the email from the session
        user = utility.getObjectFromSession(request, 'user')
        # get the requested domain name from the submitted form
        newDomainName = request.POST.get('domainName').lower()
        # check the form has requested domain url
        if request.POST['domainName']:
            if user is not None:
                # get the schema name for the user
                name = user.userCompanyId.schemaName
                # getting the schema for the user from schema table
                tenantScheMaNew = Schema.objects.get(schema_name=name)
                # get the url changed status
                check = user.userCompanyId.urlchanged
                # check the url is not changed previously
                if check == constants.No:
                    # check the requested url is already exist in the system
                    tenantScheMaURL = utility.getSchemaByDomainUrl(newDomainName + settings.DOMAIN_NAME)
                    if tenantScheMaURL is None:
                        # save the user domain url
                        tenantScheMaNew.domain_url = newDomainName + settings.DOMAIN_NAME
                        tenantScheMaNew.save()
                        company = Company.objects.get(pk=user.userCompanyId)
                        company.urlchanged = constants.Yes
                        company.save()
                        url = newDomainName + settings.DOMAIN_NAME
                        # redirect to login page
                        redirecturl = settings.HTTP + url + ':' + settings.PORT + '/login'
                        return JsonResponse(
                            {'status': 'success', 'success_msg': 'Your Domain Name has been changed successfully',
                             'redirect_url': redirecturl})
                    # domain name already exists it throughs error
                    else:
                        return JsonResponse(
                            {'status': 'error', 'error_msg': 'This Domain Name is already taken. Try Another'})
                # domain url already changed
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'You have already changed your domain name'})
        # domain name not entered
        else:
            return JsonResponse({'status': 'error', 'error_msg': 'Please enter domain name'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Customer Manual adding form"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def customermanualform(request):
    customerForm = CustomerManualAddingForm()
    customerShippingForm = CustomerShippingAddressForm()
    return render(request, 'customermanualform.html',
                  {'customerForm':customerForm,'customerShippingForm':customerShippingForm})


"""Customer CSV upload form"""
def customerautoform(request):
    return render(request, 'customerautoform.html')


"""Supplier Manual adding form"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def suppliermanualform(request):
    supplierForm = SupplierManualAddingForm()
    supplierShippingForm = SupplierShippingAddressForm()
    return render(request, 'suppliermanualform.html',
                  {'supplierForm': supplierForm, 'supplierShippingForm': supplierShippingForm})


"""Supplier CSV upload form"""
def supplierautoform(request):
    return render(request, 'supplierautoform.html')


"""Product Manual adding form"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productmanualform(request):
    if 'user' in request.session or 'subUser' in request.session:
        itemMasterAddForm = ItemMasterManualForm()
        attributeForm = productAttributeForm()
        purchasingForm = purchasingItemsForm()
        salesForm = salesItemsForm()
        measurementForm = itemMeasurementForm()
        storageForm = itemStorageForm()
        parameterForm = itemParameterForm()
        return render(request, 'productmanualform.html',
                      {'itemMasterAddForm': itemMasterAddForm, 'attributeForm': attributeForm,
                       'purchasingForm': purchasingForm,'salesForm': salesForm, 'measurementForm': measurementForm,
                       'storageForm': storageForm, 'parameterForm':parameterForm})
    return HttpResponseRedirect('/login/')


"""Product CSV upload form"""
def productautoform(request):
    return render(request, 'productautoform.html')


"""Fuzzy validation for Email - entered email 90% matches the existing email method return the matched email as list
Parameters - Email = entered email, methodType = request to return multiple users or single user"""
def fuzzyEmail(email, methodType):
    listOfUsers = []
    userEmail = User.objects.all().values_list('email')
    user = User.objects.all().values(
        "email",
        "contactNo",
        companyName=F("userCompanyId__companyName"),
        country=F("userCompanyId__country"),
        state=F("userCompanyId__state"),
        country__name=F("userCompanyId__country__countryName"),
        state__name=F("userCompanyId__state__stateName"),
    )
    if userEmail:
        if methodType == "user":
            emailId = process.extractOne(email, userEmail)
            if emailId[1] >= 90:
                listOfUsers.append(emailId)
        else:
            for individualUser in user:
                emailMatch = fuzz.ratio(email.lower(), individualUser["email"])
                if emailMatch >= 90:
                    listOfUsers.append(individualUser)
    return listOfUsers


"""Validation for Contact Number - check contact number already exists"""
def fuzzyContactNumber(contactNo):
    try:
        userContactNumber = User.objects.filter(contactNo__iexact=contactNo).values("email",
                                                                                    "contactNo",
                                                                                    companyName=F(
                                                                                        "userCompanyId__companyName"),
                                                                                    country=F("userCompanyId__country"),
                                                                                    state=F("userCompanyId__state")
                                                                                    )
    except:
        userContactNumber = []
    return userContactNumber


"""Fuzzy validation for Company Name - entered company name 90% matches the existing company name method return the 
matched company name as list and if 60% matches the existing then the method check the address matches 90% or not,
address matches 90% method return matched results"""
def fuzzyCompanyName(companyName, country, state, pincode, unit1, unit2, addressLine1, addressLine2, methodType):
    listOfUsersHighPerc = []
    listOfUsersLessPerc = []
    company = User.objects.all().values("email", "contactNo",
                                        companyName=F("userCompanyId__companyName"),
                                        country=F("userCompanyId__country"),
                                        state=F("userCompanyId__state"),
                                        country__name=F("userCompanyId__country__countryName"),
                                        state__name=F("userCompanyId__state__stateName"),
                                        address_Line1=F("userCompanyId__address_Line1"),
                                        address_Line2=F("userCompanyId__address_Line2"),
                                        unit1=F("userCompanyId__unit1"),
                                        unit2=F("userCompanyId__unit2")
                                        )
    companyList = Company.objects.all().values_list('companyName')
    if company:
        if methodType == "user":
            companyMatch = process.extractOne(companyName, companyList)
            if companyMatch[1] >= 90:
                listOfUsersHighPerc.append(companyMatch)
            elif companyMatch[1] >= 60:
                for individualUser in company:
                    comPanyName = individualUser["companyName"].lower()
                    companyMatch = fuzz.ratio(companyName, comPanyName)
                    if companyMatch >= 60 and companyMatch < 90:
                        if country == individualUser["country"] and state == individualUser[
                            "state"] and pincode.lower() == individualUser["postalCode"]:
                            addressLine1Match = fuzz.ratio(addressLine1.lower(),
                                                           individualUser["address_Line1"].lower())
                            addressLine2Match = fuzz.ratio(addressLine2.lower(),
                                                           individualUser["address_Line2"].lower())
                            unit1Match = fuzz.ratio(unit1.lower(), individualUser["unit1"].lower())
                            unit2Match = fuzz.ratio(unit2.lower(), individualUser["unit2"].lower())
                            if addressLine1Match >= 90 and addressLine2Match >= 90 and unit1Match >= 90 \
                                    and unit2Match >= 90:
                                listOfUsersLessPerc.append(comPanyName)
        else:
            for individualUser in company:
                comPanyName = individualUser["companyName"].lower()
                companyMatch = fuzz.ratio(companyName, comPanyName)
                if companyMatch >= 90:
                    listOfUsersHighPerc.append(individualUser)
                elif companyMatch >= 60 and companyMatch < 90:
                    if country == individualUser["country"] and state == individualUser["state"] and\
                            pincode.lower() == individualUser["postalCode"]:
                        addressLine1Match = fuzz.ratio(addressLine1.lower(), individualUser["address_Line1"].lower())
                        addressLine2Match = fuzz.ratio(addressLine2.lower(), individualUser["address_Line2"].lower())
                        unit1Match = fuzz.ratio(unit1.lower(), individualUser["unit1"].lower())
                        unit2Match = fuzz.ratio(unit2.lower(), individualUser["unit2"].lower())
                        if addressLine1Match >= 90 and addressLine2Match >= 90 and unit1Match>=90 and unit2Match >= 90:
                            listOfUsersLessPerc.append(individualUser)
    return (listOfUsersHighPerc, listOfUsersLessPerc)


"""Place Order HTML - Page allow to view the placed order by the user and also allow to place new multiple/single 
supplier orders"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def placeOrder(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId

            return render(request, 'placeOrder.html',
                          {'company': company, 'urls':list(urls),'user': currentUser, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'status': company.urlchanged,
                           'noti': notiFy,'leng': lengTh,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Customer product catalog HTML - page used to assign products/catalog to the customers"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def customerProductPanel(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'customerproductpanel.html',
                          {'company': company,'urls':list(urls), 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'subscribedModules':subscribedModules })
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Supplier product catalog HTML - page used to assign products/catalog to the suppliers"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def supplierProductPanel(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'supplierproductpanel.html',
                          {'company': company, 'urls':list(urls),'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'user': currentUser,
                           'leng': lengTh, 'status': company.urlchanged,'subscribedModules':subscribedModules })
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Initialise the pre-requested model values with importing csv to respective models in the public schema"""
def initialiseCsvImport(request):
    connection.set_schema_to_public()
    addressType = Country.objects.all().order_by('countryName')
    if not addressType:
        csvNameArray = ['Countries.csv', 'CurrencyType.csv', 'ItemStatus.csv','QuantityType.csv', 'CountryCode.csv',
                        'Questions.csv', 'States.csv', 'plan.csv',  'module.csv','requestaccess.csv',
                        'storageAllocation.csv','storageSize.csv','storageType.csv','upgradeFeatures.csv']
        modelNameArray = [Country, CurrencyType, ItemStatus, QuantityType, CountryCode, SecurityQuestion, State,
                          Plan, Module, RequestAccess,storageAllocation,storageSize,storageType,upgradeFeatures]
        zipData = zip(csvNameArray, modelNameArray)
        for csvfile, modelName in zipData:
            f = open(os.path.join(IMPORT_FILES_FOLDER, csvfile), encoding='ISO-8859-1')
            if csvfile != 'module.csv' and csvfile != "plan.csv":
                reader = csv.DictReader(f)
                rows = list(reader)
                # modelName.objects.all().delete()
                modelSave(rows, modelName)
            elif csvfile == 'plan.csv':
                listCsv = list(csv.DictReader(f))
                dumps = json.dumps(listCsv)
                usersFromCsv = json.loads(dumps)
                for customerOrsupplier in usersFromCsv:
                    planfeatures = Plan()
                    planfeatures.planName = customerOrsupplier['planName']
                    planfeatures.planCode = customerOrsupplier['planCode']
                    planfeatures.planDesc = customerOrsupplier['planDesc']
                    planfeatures.cost = customerOrsupplier['cost']
                    planfeatures.currencyType_id = customerOrsupplier['currencyType_id']
                    del customerOrsupplier['planCode']
                    del customerOrsupplier['planName']
                    del customerOrsupplier['cost']
                    del customerOrsupplier['planDesc']
                    del customerOrsupplier['currencyType_id']
                    planfeatures.planFeaturesJson = customerOrsupplier
                    planfeatures.save()
            else:
                listCsv = list(csv.DictReader(f))
                dumps = json.dumps(listCsv)
                csvData = json.loads(dumps)
                for modulelist in csvData:
                    module = Module()
                    module.moduleCode = modulelist['moduleCode']
                    module.moduleDesc = modulelist['moduleDesc']
                    module.moduleName = modulelist['moduleName']
                    module.modulePrice = modulelist['modulePrice']
                    module.modulePriceUnit_id = modulelist['modulePriceUnit_id']
                    module.save()
                    for a in modulelist['planId'].split(','):
                        module.planId.add(int(a))
                        module.save()
        return HttpResponse('Csv imported successfully ☺')
    else:
        return HttpResponse('You have initialized the database already ☺')


"""Create the new notification for the specified schema
Parameters sendingTrader = Customer/Supplier, id = Customer/Supplier Id, desc = Notification Description,
types = type of the notification, href = hyperlink , site = site id for notification"""
def notificationView(sendingTrader,id, desc, types,href,site):
    noti = Notification()
    noti.sendFromId = id
    noti.sendingTrader = sendingTrader
    noti.desc = desc
    noti.type = types
    noti.href = href
    noti.notificationSite_id = site
    noti.save()


"""Method is to changed the viwed the status"""
@csrf_exempt
def notificationStatus(request):
    if 'user' in request.session or 'subUser' in request.session:
        id = request.POST['notificationId']
        noti = utilitySD.getNotificationById(id)
        noti.viewed = constants.Yes
        msg = noti.desc
        email = noti.sendFromId
        noti.save()
        return JsonResponse({'status': 'success', 'msg': msg, 'email': email})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Reset Password - Change the USER/SUB-USER/SUPER-ADMIN password as per request and the password is encrypted using
SHA-256 algorithm"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def resetPassword(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, "")
            superAdmin = False
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, "")
            superAdmin = False
            if currentUser.superAdmin:
                if currentUser.accessRights != constants.Operational:
                    superAdmin = True
                else:
                    superAdmin = False
        account = utility.getoTAccountByCompany(company)
        if superAdmin and currentUser.accessRights == constants.Admin:
            lengTh = 0
            notiFy = []
            urls = []
            subscribedModules = {}
        else:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId

        if request.method != 'POST':
            Resetpassword = ResetpasswordForm()
        else:
            Resetpassword = ResetpasswordForm()
            if not account.planSuspended:
                Resetpassword = ResetpasswordForm(request.POST)
                if Resetpassword.is_valid():
                    checkPwd = check_password(request.POST['old_password'], currentUser.password)
                    samePwd = check_password(request.POST['password'], currentUser.password)
                    if not checkPwd:
                        messages.error(request, "Please enter the correct old password")
                    elif samePwd:
                        messages.error(request, "New Password and Old Password are same")
                    elif checkPwd and not samePwd:
                        currentUser.password = make_password(request.POST['password'])
                        currentUser.save()
                        if subUserProfile == constants.No:
                            utility.updateSessionforObject(request, 'user', User, currentUser.pk)
                        else:
                            utility.updateSessionforObject(request, 'subUser',Subuser, currentUser.pk)
                        return HttpResponseRedirect('/dashboard/')
            else:
                messages.error(request, "Your plan has suspended")
        return render(request, 'resetpassword.html',
                      {'company': company,'urls':list(urls), 'profileForm': profileForm, 'formreset': Resetpassword,
                       'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                       'noti': notiFy, 'user': currentUser,
                       'leng': lengTh, 'status': company.urlchanged,'subscribedModules':subscribedModules })
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})



"""Method used to return the user information"""
@csrf_exempt
def userProfile(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        item = {}
        totalItems = []
        if 'user' in request.session:
            email = utility.getObjectFromSession(request, 'user').email
        else:
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            mainUser = utility.getUserByCompanyId(userCompany)
            email = mainUser.email
        user = User.objects.filter(email=email).values("email", "contactNo", "firstName", "lastName",
                                                       "sec_answer", "sec_question_id",
                                                        "countryCode_id",
                                                       postalCode=F("userCompanyId__postalCode"),
                                                       companyName=F("userCompanyId__companyName"),
                                                       country_id=F("userCompanyId__country"),
                                                       state_id=F("userCompanyId__state"),
                                                       country__name=F("userCompanyId__country__countryName"),
                                                       state__name=F("userCompanyId__state__stateName"),
                                                       address_Line1=F("userCompanyId__address_Line1"),
                                                       address_Line2=F("userCompanyId__address_Line2"),
                                                       unit1=F("userCompanyId__unit1"),
                                                       unit2=F("userCompanyId__unit2"))
        item['totalItem'] = list(user)
        totalItems.append(item)
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Sub-User View HTML - Page has view/edit/create subuser and also view/edit the roles functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def viewUser(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            subUserForm = SubUserFormDetails()
            editSubUserForm = EditSubUserFormDetails()
            usr = RequestAccess.objects.filter(module__planId=
                                     oTAccount.objects.get(companyId=company.pk).plan_Id).values('group')
            roles = RolesAndAccess.objects.filter(status=constants.Active).values()
            reqAccess = []
            type = ['create', 'view', 'update', 'delete']
            d = list(usr.distinct())
            # grouping the access rights as per required format
            for i in d:
                objectArray = []
                for itype in type:
                    s = list(RequestAccess.objects.filter(group=i['group'], type=itype).values_list("requestAccId",
                                                                                                    flat=True))
                    arrayString = ''
                    for string in s:
                        if arrayString == '':
                            arrayString = str(string)
                        else:
                            arrayString = arrayString + ',' + str(string)
                    objectAccess = {'type': itype, 'requestAccId': arrayString}
                    objectArray.append(objectAccess)
                reqAccessObject = {'key': i['group'], 'value': objectArray}
                reqAccess.append(reqAccessObject)
            return render(request, 'viewuser.html',
                          {'company': company,'urls':list(urls), 'profileForm': profileForm, 'reqAccess': reqAccess,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'subUserForm': subUserForm, 'editSubUserForm': editSubUserForm,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'roles':roles,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



"""Unauthorize page"""
def unauthorize(request):
    return render(request, 'unauthorize.html')



"""Service Level Agreement View HTML - Page has view/edit/create SLA functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def createOrViewSLA(request):
    if ('user' in request.session or 'subUser' in request.session):
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            shippingAddressForm = UserShippingAddressForm()
            shippingAddressEditForm = UserShippingAddressEditForm()
            return render(request, 'createOrViewSLA.html',
                          {'company': company,'urls':list(urls), 'ProfileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'shippingAddressForm': shippingAddressForm,
                           'shippingAddressEditForm': shippingAddressEditForm,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



"""Area View HTML - Page has view/edit/create Area functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def viewArea(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            areaAddForm = AreaAddForm()
            areaEditForm = AreaEditForm()
            return render(request, 'viewArea.html',
                          {'company': company,'urls':list(urls), 'ProfileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'areaAddForm': areaAddForm, 'areaEditForm': areaEditForm,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Site View HTML - Page has view/edit/create site functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def viewSite(request):
    if ('user' in request.session or 'subUser' in request.session):
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            AddSiteFormdetails = AddSiteForm()
            EditSiteFormdetails = EditSiteForm()
            return render(request, 'viewsite.html',
                          {'company': company,'urls':list(urls), 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'AddSiteForm': AddSiteFormdetails, 'EditSiteForm': EditSiteFormdetails,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'subscribedModules':subscribedModules })
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



""" loading sites from table based on selection area """
def load_sites(request):
    # get the country id
    siteArea_id = request.GET.get('siteArea_id')
    # get the states for the particular country
    sites = Sites.objects.filter(siteArea_id=siteArea_id).order_by('siteName')
    # serialize in to Json format
    data = serializers.serialize('json', sites)
    return JsonResponse({'sites': data})


"""Assign SLA to supplier HTML - page has SLA assigning to not interrelation suppliers functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def fetchAllSupplierForSlaAssign(request):
    if ('user' in request.session or 'subUser' in request.session):
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            areaAddForm = AreaAddForm()
            AddSiteFormdetails = EditSiteForm()
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            sup = Supplier.objects.filter(status=constants.Active).values('supCompanyName','supplierId')
            sla =serviceLevelAgreement.objects.filter(status=constants.Active).values('slaType','slaId')
            return render(request, 'assignSlaToSupplier.html',{'sup':sup,'sla':sla,'user': currentUser,
                                'ProfileForm': ProfileForm,'companyProfileForm': companyProfileForm,
                                'subUserProfile': subUserProfile, 'status': company.urlchanged,
                                'AddSiteForm': AddSiteFormdetails,'urls':list(urls),
                                'areaAddForm': areaAddForm,
                                'company':company,'noti': notiFy, 'leng': lengTh,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



"""Method is used to create default Area,Site,SLA for the private schema"""
def defaultAreaSiteAndSlaCreation(company):
    initialiseCsvImportPrivate()
    sla = serviceLevelAgreement()
    sla.slaDetails=constants.SlaDetailsJson
    sla.slaType=constants.Default
    sla.save()
    areaObject = Area()
    areaObject.areaName = constants.Central
    areaObject.areaDesc = constants.DefaultAreaDesc
    areaObject.areaSlaId = sla
    areaObject.save()
    try:
        address = UserAddress.objects.get(usradd_addressType=constants.HeadQuarter)
    except:
        address = UserAddress()
    address.usradd_country = company.country
    address.usradd_state = company.state
    address.usradd_unit1 = company.unit1
    address.usradd_unit2 = company.unit2
    address.usradd_address_Line1 = company.address_Line1
    address.usradd_address_Line2 = company.address_Line2
    address.usradd_postalCode = company.postalCode
    address.usradd_addressType = constants.HeadQuarter
    address.save()
    siteObject = Sites()
    siteObject.siteName = constants.HeadQuarter
    siteObject.siteDesc = constants.DefaultSiteDesc
    siteObject.siteArea = areaObject
    siteObject.siteAddress = address
    siteObject.siteType_id = 4
    siteObject.save()


"""Initialise the pre-requested model values with importing csv to respective models in the private schema"""
def initialiseCsvImportPrivate():
    csvNameArray = ['typeOfArticle.csv', 'productCategory.csv', 'merchantCategory.csv',
                    'merchantSubCategoryOne.csv', 'merchantSubCategoryTwo.csv',
                    'storageConditions.csv', 'taxCode.csv', 'itemDimension.csv', 'weightUnit.csv',
                    'itemDepartment.csv','TypeOfSites.csv','RolesAndAccess.csv']
    modelNameArray = [typeOfArticle, productCategory, merchantCategory, merchantSubCategoryOne, merchantSubCategoryTwo,
                      storageConditions, taxCode,
                      itemDimension, weightUnit, itemDepartment,TypeOfSites,RolesAndAccess]
    zipData = zip(csvNameArray, modelNameArray)
    for csvfile, modelName in zipData:
        logger.info(csvfile + " import started")
        f = open(os.path.join(IMPORT_FILES_FOLDER, csvfile))
        reader = csv.DictReader(f)
        rows = list(reader)
        modelSave(rows, modelName)
        logger.info(csvfile + " import ended")


"""View supplier SLA HTML - page has view/accept/reject supplier SLA functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def viewSupplierSLA(request):
    if ('user' in request.session or 'subUser' in request.session):
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            if 'notificationId' in request.GET:
                notiId = request.GET.get('notificationId', '')
            else:
                notiId = None
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            sup = Supplier.objects.filter(status=constants.Active).values('supCompanyName', 'supplierId')
            site = Sites.objects.filter(status=constants.Active).values('siteName', 'siteId')
            return render(request, 'viewSupplierSLA.html',
                          {'company': company,'urls':list(urls), 'ProfileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'sup': sup,
                           'site': site,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'notificationId':notiId,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Notification View HTML"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def viewallnotifications(request):
    if ('user' in request.session or 'subUser' in request.session):
        userForm = UserForm()
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(company)
        if urls:
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            lengTh = len(notiFy)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            return render(request, 'viewallnotifications.html',
                          {'company': company,'urls':list(urls), 'form': userForm, 'ProfileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Method is to get memory details for the current schema"""
def getMemoryDetails(request):
    if ('user' in request.session or 'subUser' in request.session):
        schemaName = connection.schema_name
        company = utility.getCompanyBySchemaName(schemaName)
        item = {}
        totalItems = []
        account = utility.getoTAccountByCompany(company)
        storage = float(account.storageSize)
        item['Allocated'] = int(storage)
        masterData= float(utility.getSchemaMemorySize(schemaName))
        mediaData=  float(utility.getMediaSize(schemaName))
        item['MasterData'] = int(masterData)
        item['Media'] = int(mediaData)
        item['FreeSpace'] = int(storage - masterData - mediaData)
        item['Transaction'] = 0
        item['Report'] = 0
        totalItems.append(item)
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get access previlage present for current user"""
def getAccessUrlPrevilage(request):
    if ('user' in request.session or 'subUser' in request.session):
        url = request.GET.get('url')
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, url)
            addOnModuleUrls = utility.getUrlsAccessAddonModule(company, url)
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, url)
        previlage = False
        if urls or addOnModuleUrls:
            previlage = True
        return JsonResponse(
            {'status': 'success', 'previlage': previlage})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def saveAddonFeatures(request):
   if ('user' in request.session or 'subUser' in request.session):
       if 'user' in request.session:
           mainUser = utility.getObjectFromSession(request, 'user')
           userCompany = mainUser.userCompanyId
           check = True
       else:
           currentUser = utility.getObjectFromSession(request, 'subUser')
           userCompany = utility.getCompanyBySchemaName(connection.schema_name)
           check = False
           if currentUser.superAdmin:
               if currentUser.accessRights != constants.Operational:
                   check = True
               else:
                   check = False
       account = utility.getoTAccountByCompany(userCompany)
       if not account.planSuspended:
           if check:
               try:
                   data = request.session['data']
                   unit = data["unit"]
                   sumofprice = int(data["sumofprice"])*100
                   planData = data["planData"]
                   stripe.api_key = settings.STRIPE_SECRET_KEY
                   stripe.Charge.create(
                       amount=int(sumofprice),
                       currency=unit,
                       description='A Django charge',
                       source=request.POST['stripeToken']
                   )
                   schemaName = connection.schema_name
                   for addOn in planData:
                       catDet = list(addOn.keys())
                       catQty = list(addOn.values())
                       featureDet = upgradeFeatures.objects.get(categoryDetail=catDet[0])
                       try:
                           addonfeature = addonFeatures.objects.get(otAccountDetail=account,featuresDetails=featureDet)
                       except:
                           addonfeature = addonFeatures()
                       addonfeature.otAccountDetail = account
                       addonfeature.featuresDetails = featureDet
                       if addonfeature.categoryQty:
                           addonfeature.categoryQty = int(addonfeature.categoryQty)+int(catQty[0])
                       else:
                           addonfeature.categoryQty = int(catQty[0])
                       addonfeature.purchasedPrice = featureDet.categoryPrice
                       addonfeature.purchasedPriceUnit = featureDet.categoryPriceUnit
                       addonfeature.save()
                   messages.success(request,'Payment Successfully Completed')
                   return redirect("accountinfo")
               except stripe.error.CardError as e:
                   body = e.json_body
                   err = body.get('error', {})
                   messages.error(request, f"{err.get('message')}")
                   return redirect("accountinfo")

               except stripe.error.RateLimitError as e:
                   # Too many requests made to the API too quickly
                   messages.error(request, "Rate limit error")
                   return redirect("accountinfo")

               except stripe.error.InvalidRequestError as e:
                   # Invalid parameters were supplied to Stripe's API
                   messages.error(request, "Invalid parameters")
                   return redirect("accountinfo")

               except stripe.error.AuthenticationError as e:
                   # Authentication with Stripe's API failed
                   # (maybe you changed API keys recently)
                   messages.error(request, "Not authenticated")
                   return redirect("accountinfo")

               except stripe.error.APIConnectionError as e:
                   # Network communication with Stripe failed
                   messages.warning(request, "Network error")
                   return redirect("accountinfo")

               except stripe.error.StripeError as e:
                   # Display a very generic error to the user, and maybe send
                   # yourself an email
                   messages.warning(
                       request, "Something went wrong. You were not charged. Please try again.")
                   return redirect("accountinfo")

               except Exception as e:
                   # send an email to ourselves
                   messages.warning(
                       request, "A serious error occurred. We have been notifed.")
                   return redirect("accountinfo")


           else:
               return JsonResponse(
                   {'status': 'error', 'error_msg': "Your don't have access for this action"})
       else:
           return JsonResponse(
               {'status': 'error', 'error_msg': "Your plan has suspended"})
   return JsonResponse(
       {'status': 'error', 'error_msg': 'sessionexpired',
        'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to update the storage for the current schema"""
@csrf_exempt
def upgradeStorage(request):
    if ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = False
            if currentUser.superAdmin:
                if currentUser.accessRights != constants.Operational:
                    check = True
                else:
                    check = False
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                storageType = utility.getStorageAllocationById(body['storageType'])
                previousStorage = float(account.storageSize)
                if storageType:
                    if storageType.storageListCode == 'Custom':
                        customType = body['customType']
                        customValue = body['customValue']
                    else:
                        account.storageAllocation_id = storageType
                        storageSize = utility.getStorageSizeByAllocation(storageType)
                        if constants.MegaByte in storageSize.storageSizeCode:
                            customType = constants.MegaByte
                            customValue = storageSize.storageSizeCode.replace(constants.MegaByte , "")
                        else:
                            customType = constants.GegaByte
                            customValue = storageSize.storageSizeCode.replace(constants.GegaByte , "")
                    if customType == constants.MegaByte:
                        customValue = float(customValue) * 1000000
                    elif customType == constants.GegaByte:
                        customValue = float(customValue) * 1000000000
                    updatedStorage = int(previousStorage) + int(customValue)
                    account.storageSize = str(updatedStorage)
                    account.save()
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Storage upgraded successfully'})
                else:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': 'Error in upgrade storage'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def billingDetails(request):
    if ('user' in request.session or 'subUser' in request.session):
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, "")
            superAdmin = False
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
            superAdmin = False
            if currentUser.superAdmin:
                if currentUser.accessRights != constants.Operational:
                    superAdmin = True
                else:
                    superAdmin = False
                    urls = None
        account = utility.getoTAccountByCompany(company)
        if urls or superAdmin:
            if superAdmin and currentUser.accessRights == constants.Admin:
                lengTh = 0
                notiFy = []
                urls = []
                subscribedModules = {}
            else:
                notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
                lengTh = len(notiFy)
                subscribedModules = {}
                subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
                for sub in subscribed:
                    module = Module.objects.get(moduleId=sub['modulesAccess'])
                    subscribedModules[module.moduleName] = module.moduleId
            details = list(BillingDetails.objects.all().values())
            return render(request, 'billingDetails.html',
                          {'company': company, 'urls': list(urls), 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,'details':details,
                           'leng': lengTh, 'user': currentUser,'status': company.urlchanged,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


@csrf_exempt
def paymentGateway(request):
    if ('user' in request.session or 'subUser' in request.session):
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, "")
            superAdmin = False
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
            superAdmin = False
            if currentUser.superAdmin:
                if currentUser.accessRights != constants.Operational:
                    superAdmin = True
                else:
                    superAdmin = False
                    urls = None
        account = utility.getoTAccountByCompany(company)
        if urls or superAdmin:
            if superAdmin and currentUser.accessRights == constants.Admin:
                lengTh = 0
                notiFy = []
                urls = []
                subscribedModules = {}
            else:
                notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
                lengTh = len(notiFy)
                subscribedModules = {}
                subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
                for sub in subscribed:
                    module = Module.objects.get(moduleId=sub['modulesAccess'])
                    subscribedModules[module.moduleName] = module.moduleId
            data = request.session['data']
            unit = data["unit"]
            sumofprice = data["sumofprice"]
            sumoftotalprice = int(data["sumofprice"])*100
            planData = data["planData"]
            key = settings.STRIPE_PUBLISHABLE_KEY
            return render(request, 'paymentGateway.html',
                          {'company': company, 'urls': list(urls), 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,'key':key,'planData':planData,'sumofprice':sumofprice,
                           'sumoftotalprice':sumoftotalprice,'unit':unit,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


@csrf_exempt
def saveDataInSession(request):
    a = request.body.decode('utf-8')
    body = json.loads(a)
    request.session['data'] = body
    return JsonResponse(
    {'status': 'success', 'success_msg': 'success'})

@csrf_exempt
def upgradePlan(request):
    if ('user' in request.session or 'subUser' in request.session):
        company = utility.getCompanyBySchemaName(connection.schema_name)
        storage = storageAllocation.objects.get(planDetail_id=request.POST['plan'])
        oTAccountPlan = utility.getoTAccountByCompany(company)
        oTAccountPlan.plan_Id_id = request.POST['plan']
        oTAccountPlan.storageAllocation_id = storage
        storageSizeCode = utility.getStorageSizeByAllocation(storage).storageSizeCode
        if constants.MegaByte in storageSizeCode:
            storageSizeCode = float(storageSizeCode.replace(constants.MegaByte, "")) * 1000000
        else:
            storageSizeCode = float(storageSizeCode.replace(constants.GegaByte, "")) * 1000000000
        oTAccountPlan.storageSize = str(storageSizeCode)
        oTAccountPlan.companyId_id = company
        oTAccountPlan.status = constants.Active
        oTAccountPlan.save()
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})