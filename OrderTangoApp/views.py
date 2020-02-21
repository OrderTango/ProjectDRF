import csv
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.cache import cache_control
from django.contrib.sessions.models import Session
from OrderTangoOrdermgmtApp.models import *
from OrderTangoApp.forms import *
from django.core.mail import EmailMessage
from django.contrib import messages
from OrderTangoApp.tokens import account_activation_token
import datetime
import os, io, json
from django.core import serializers
import logging
import random
from django.db.models import Q, F
from OrderTangoSubDomainApp.forms import *
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from OrderTango.settings import IMPORT_FILES_FOLDER,MEDIA_ROOT
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from OrderTangoApp import utility, constants
from OrderTangoSubDomainApp.views import addInvitedCustomerOrSupplier
from xhtml2pdf import pisa
from django.template.loader import render_to_string


# console logger
logger = logging.getLogger(__name__)

# session time for expiration
time = settings.TIME


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
    # ip is for home URL redirection
    return render(request, 'landingpage.html', {'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


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
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            itemMasterForm = ItemMasterAddForm()
            totalAddress = Sites.objects.filter(siteStatus=constants.Active).all()
            storeMasterForm = StoreForm()
            storeMasterForm.fields['storeName'].choices = [(address.siteId, address.siteName) for address in
                                                           totalAddress]
            return render(request, 'productsalescatalog.html',
                          {'company': company, 'category':list(productCategory.objects.all()), 'user': currentUser, 'form': userForm, 'ProfileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')

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
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            itemMasterForm = ItemMasterAddForm()
            totalAddress = Sites.objects.filter(siteStatus=constants.Active).all()
            storeMasterForm = StoreForm()
            storeMasterForm.fields['storeName'].choices = [(address.siteId, address.siteName) for address in
                                                           totalAddress]
            return render(request, 'productpurchasecatalog.html',
                          {'company': company, 'category':list(productCategory.objects.all()), 'user': currentUser, 'form': userForm, 'ProfileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


def subscription(request):
    # ip is for home URL redirection
    return render(request, 'subscription.html', {'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


# view supplier,customer and product page
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
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            itemMasterForm = ItemMasterAddForm()
            totalAddress = Sites.objects.filter(siteStatus=constants.Active).all()
            storeMasterForm = StoreForm()
            storeMasterForm.fields['storeName'].choices = [(address.siteId, address.siteName) for address in
                                                           totalAddress]
            return render(request, 'administrationpanel.html',
                          {'company': company, 'user': currentUser, 'form': userForm, 'ProfileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh})

        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


# view the orders from customer
def vieworders(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            return render(request, 'vieworders.html',
                          {'company': company, 'user': currentUser, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,
                           'leng': lengTh})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


# view the placed orders to supplier
def placedorderdetails(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            return render(request, 'viewplacedorders.html',
                          {'company': company, 'user': currentUser, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,
                           'leng': lengTh})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


# operational panel
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
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            return render(request, 'operationalpanel.html',
                          {'company': company, 'user': currentUser, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,
                           'leng': lengTh})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


# email validation for registered users
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def validation(request):
    if 'emailBeforevalidation' in request.session:
        wsid = ''
        if 'wsid' in request.session:
            wsid = request.session['wsid']
        return render(request, 'validation.html', {'email': request.session['emailBeforevalidation'],'wsid': wsid})
    else:
        # user not in the session it will show the error message and redirected to login page
        request.session.flush()
        messages.error(request, 'Session Expired!')
        return HttpResponseRedirect('/login/')


# Email sender
def sendingEmail(request, user, email, otp, html, subject, domain, attachment,wsid):
    # Generating the message content as HTML
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
    # Getting the mail subject
    mail_subject = subject
    # Getting the send to mail address
    to_email = email
    # Sending email
    email = EmailMessage(mail_subject, message, to=[to_email])
    if attachment:
        email.attach_file(MEDIA_ROOT+attachment)
        email.send()
    else:
        email.send()


# otp generator
def otpGenerator():
    # generate the four digit OTP
    generatedOtp = str(random.randint(1000, 10000))
    return generatedOtp


# user registration
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def registration(request):
    if request.method == 'POST':
        # getting the submitted form
        userForm = UserForm(request.POST)
        companyForm = CompanyForm(request.POST)
        # check the validation rules

        if userForm.is_valid() and companyForm.is_valid():
            # get the email from the submitted form,to send activation mail and set the email to lowercase
            email = userForm.cleaned_data.get('email').lower()

            try:
                # get the token from the submitted form
                token = userForm.cleaned_data.get('wsid')
            except:
                token = None

            user = userForm.save(commit=False)
            company = companyForm.save(commit=False)
            # generating the unique token for user
            user.token = utility.uuIdTokenGenerator()
            # make the password in to encrypted format using SHA256 algorithm
            user.password = make_password(userForm.cleaned_data.get('password'))
            # generating otp
            company.companyCode = utility.oTcompanyCodeGenerator(company.companyName, company.country.countryCode)
            company.save()
            otp = otpGenerator()
            user.otp = otp
            user.userCompanyId = company
            user.email = email
            user.sec_answer = userForm.cleaned_data.get('sec_answer').lower()
            user.save()
            oTAccountPlan = oTAccount()
            oTAccountPlan.plan_Id_id = request.POST['plan']
            oTAccountPlan.companyId_id = company
            oTAccountPlan.status = constants.Active
            oTAccountPlan.save()
            # sending email to the registered user
            sendingEmail(request, user, email, user.otp, 'acc_active_email.html', 'Activate your account',
                         request.get_host(), None,token)
            # setting email in to session for email validation
            request.session["emailBeforevalidation"] = email
            # setting the otp entering count for checking the otp attempt
            request.session["otpCount"] = 0
            if token:
                request.session["wsid"] = token
            return HttpResponseRedirect('/validation/')
        else:
            return render(request, 'registration.html',
                          {'form': userForm, 'companyform': companyForm,
                           'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})
    # existing user registration using invitation URL
    else:
        wsid= None
        if request.GET.get('wsid', None) is not None:
            wsid = request.GET.get('wsid', '')
    # for registration page
    userForm = UserForm(initial={'wsid': wsid})
    companyForm = CompanyForm(initial={'companyWsid': wsid})
    return render(request, 'registration.html',
                  {'form': userForm, 'companyform': companyForm,
                   'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


# user login
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login(request):
    if request.method == 'POST':
        # getting the submitted form
        loginform = LoginForm(request.POST)
        # check the validation rules
        # get the email from the submitted form
        email = request.POST['email'].lower()
        password = request.POST['password']
        if email and password is not None:
            try:
                # get the user using email
                user = User.objects.get(email=email)
            except:
                user = None

            rootUrl = request.get_host()
            www = ""
            if request.get_host().startswith('www.'):
                rootUrl = request.get_host().replace('www.', '')
                www = 'www.'

            if user is not None:
                if user.userCompanyId.verificationStatus == constants.Active:
                    if check_password(password, user.password):
                        # check whether request URL is not a subdomain URL
                        if settings.DOMAIN_NAME not in rootUrl:
                            # getting the schema for the user from schema table
                            userSchema = Schema.objects.get(schema_name=user.userCompanyId.schemaName)
                            # getting the schema url for the user
                            url = userSchema.domain_url
                            # connect the schema of the user
                            connection.set_schema(schema_name=user.userCompanyId.schemaName)
                            # create session for the user
                            request.session.create()
                            # setting email in to session
                            request.session['user'] = utility.setObjectToSession(user)
                            # setting session auto modification is true for every request
                            request.session.modified = True
                            # get the created session key as wsid for login
                            wsid = request.session._session_key
                            user.lastLogin = datetime.datetime.now()
                            user.save()
                            return HttpResponseRedirect(
                                settings.HTTP + www + url + ':' + settings.PORT + '/dashboard?wsid=' + wsid)
                        else:
                            if connection.schema_name == user.userCompanyId.schemaName:
                                # setting email in to session
                                request.session['user'] = utility.setObjectToSession(user)
                                # setting session auto modification is true for every request
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
                    try:
                        subUser = Subuser.objects.get(userName__iexact=email)
                    except:
                        subUser = None
                    if subUser:
                        if check_password(password, subUser.password):
                            subUser.lastLogin = datetime.datetime.now()
                            subUser.save()
                            request.session["subUser"] = utility.setObjectToSession(subUser)
                            # setting session auto modification is true for every request
                            request.session.modified = True
                            return HttpResponseRedirect('/dashboard/')
                        else:
                            return render(request, 'login.html',
                                          {'form1': loginform, 'emailError': "",
                                           'passError': "Password does not match",
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
                        subUser = Subuser.objects.get(userName__iexact=subUserName[0])
                    except:
                        subUser = None
                        connection.set_schema_to_public()
                    if subUser:
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
        if 'user' in request.session or 'subUser' in request.session:
            return HttpResponseRedirect('/dashboard/')
        else:
            # user not in the session it will redirected to login page
            loginform = LoginForm()
            return render(request, 'login.html',
                          {'form1': loginform, 'emailError': "", 'passError': "",
                           'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


# loading states from table based on selection country for add/reister users
def load_states(request):
    # get the country id
    country_id = request.GET.get('country_id')
    # get the states for the particular country
    states = State.objects.filter(country_id=country_id).order_by('stateName')
    # serialize in to Json format
    data = serializers.serialize('json', states)
    return JsonResponse({'states': data})


# loading country from table for add/reister users
def load_country(request):
    # get all the countries from table
    country = Country.objects.all().order_by('countryName')
    # serialize in to Json format
    data = serializers.serialize('json', country)
    return JsonResponse({'country': data})


# user dashboard
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dashboard(request):
    # checking whether the email present in the session
    if 'user' in request.session:
        # redirect to admin panel
        user = utility.getObjectFromSession(request, 'user')
        response = adminPanel(request, user, None)
        return response
    # checking whether the wsid present from the URL
    elif 'subUser' in request.session:
        subUser = utility.getObjectFromSession(request, 'subUser')
        response = adminPanel(request, None, subUser)
        return response
    elif request.GET.get('wsid', None) is not None:
        # checking session keys are present in the user schema
        if Session.objects.all().exists():
            try:
                # get the session details from session table using wsid(session_key)
                sessions = Session.objects.get(session_key=request.GET.get('wsid', ''))
                session_data = sessions.get_decoded()
                session_time = sessions.expire_date

            except:
                session_data = None
            try:
                user = list(serializers.deserialize("json", session_data.get('user', None)))[0].object
            except:
                user = None
            try:
                subUser = list(serializers.deserialize("json", session_data.get('subUser', None)))[0].object
            except:
                subUser = None
            # session expiration check
            if (user or subUser is not None) and datetime.datetime.now() - session_time < datetime.timedelta(0, time):
                request.session.delete()
                Session.objects.get(session_key=request.GET.get('wsid', '')).delete()
                # setting email in to session
                if user:
                    request.session['user'] = utility.setObjectToSession(user)
                    response = adminPanel(request, user, None)
                if subUser:
                    request.session['subUser'] = utility.setObjectToSession(subUser)
                    response = adminPanel(request, None, subUser)
                # setting session auto modification is true for every request
                request.session.modified = True
                # redirect to admin panel
                return response
    # user not in the session or wsid not present then it will delete the sessions and redirected to login page
    request.session.flush()
    return HttpResponseRedirect('/login/')


# adminstration panel
def adminPanel(request, user, subUser):
    profileForm = UserProfileForm()
    companyProfileForm = CompanyProfileForm()
    if subUser:
        currentUser = subUser
        subUserProfile = constants.Yes
        company = utility.getCompanyBySchemaName(connection.schema_name)
        urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
    if user:
        currentUser = user
        subUserProfile = constants.No
        company = user.userCompanyId
        urls = utility.checkRequesURLisPresentForCompany(company.companyId, request.path)
    if user or subUser is not None:
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            itemMasterAddForm = EditItemMasterManualForm()
            attributeForm = EditproductAttributeForm()
            purchasingForm = EditpurchasingItemsForm()
            salesForm = EditsalesItemsForm()
            measurementForm = EdititemMeasurementForm()
            storageForm = EdititemStorageForm()
            parameterForm = EdititemParameterForm()
            totalAddress = Sites.objects.filter(siteStatus=constants.Active).all()
            storeMasterForm = StoreForm()
            storeMasterForm.fields['storeName'].choices = [(address.siteId, address.siteName) for address in
                                                           totalAddress]
            return render(request, 'viewall.html',
                          {'company': company, 'user': currentUser, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'itemMasterAddForm': itemMasterAddForm,
                           'storageForm': storageForm,'attributeForm': attributeForm,'purchasingForm':purchasingForm,'salesForm':salesForm,'measurementForm':measurementForm,'parameterForm':parameterForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'status': company.urlchanged,
                           'leng': lengTh})
        else:
            return HttpResponseRedirect('/unauthorize/')
    else:
        # user not present in the system it will redirect into registration page
        return HttpResponseRedirect('/registration/')


# user logged out
def logout(request):
    # delete all the session for the particular user
    request.session.flush()
    return HttpResponseRedirect('/login/')


# user forget their password
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def forgetpassword(request):
    if request.method == 'POST':
        # getting the submitted form
        Forgetform = ForgetpasswordForm(request.POST)
        # get the email from the form
        email = request.POST['email'].lower()
        # check the validation rules
        if Forgetform.is_valid():
            user = User.objects.get(email=email)
            # modify the updated date time for the user to create session expiry
            user.updatedDateTime = datetime.datetime.now()
            user.save()
            # sending change password link to the user via email
            sendingEmail(request, user, email, None, 'forgot_password_email.html', 'Change your password',
                         request.get_host(), None,None)
            messages.error(request, 'Change password link has been sent to your mail')
            return HttpResponseRedirect('/forgetpassword/')
        else:
            return render(request, 'forgetpassword.html', {'form1': Forgetform})
    else:
        Forgetform = ForgetpasswordForm()
        return render(request, 'forgetpassword.html', {'form1': Forgetform})


# password change form with getting user from URL
def newpassword(request, uidb64, token):
    newPassForm = newpasswordForm()
    # getting the primary key of user from the UID
    uid = force_text(urlsafe_base64_decode(uidb64))
    try:
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        user = None
    if user is not None:
        timenow = datetime.datetime.now()
        updatedtime = user.updatedDateTime
        # checking the link expiration
        if account_activation_token.check_token(user, token) and timenow - updatedtime < datetime.timedelta(0, time):
            return render(request, 'newpassword.html', {'form1': newPassForm, 'email': user.email.lower()})
    messages.error(request, 'Link is Expired!')
    return HttpResponseRedirect('/forgetpassword/')


# change password method
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def changePassword(request):
    if request.method == 'POST' and request.POST['emailId'] is not None:
        newPassForm = newpasswordForm(request.POST)
        if newPassForm.is_valid():
            # get the email from the submitted form
            email = request.POST['emailId'].lower()
            try:
                # get the user using email
                user = User.objects.get(email=email)
            except:
                user = None
            if user is not None:
                # get the password from the submitted form
                pwd = request.POST['password']
                # make the password in to encrypted format using SHA256 algorithm
                user.password = make_password(pwd)
                user.save()
                # getting the schema for the user from schema table
                userSchema = Schema.objects.get(schema_name=user.userCompanyId.schemaName)
                # check whether request URL is not a subdomain URL
                if settings.DOMAIN_NAME not in request.build_absolute_uri():
                    # getting the schema url for the user
                    url = userSchema.domain_url
                    request.session.flush()
                    # connect the schema of the user
                    connection.set_schema(schema_name=user.userCompanyId.schemaName)
                    # create session for the user
                    request.session.create()
                    # setting email in to session
                    request.session["user"] = utility.setObjectToSession(user)
                    # setting session auto modification is true for every request
                    request.session.modified = True
                    # get the created session key as wsid for login
                    wsid = request.session._session_key
                    return HttpResponseRedirect(settings.HTTP + url + ':' + settings.PORT + '/dashboard?wsid=' + wsid)
                else:
                    request.session.flush()
                    # setting email in to session
                    request.session["user"] = utility.setObjectToSession(user)
                    # setting session auto modification is true for every request
                    request.session.modified = True
                    return HttpResponseRedirect('/dashboard/')
            else:
                return HttpResponseRedirect('/registration/')

        else:
            # submitted form is invalid it will throw the errors in the page
            return render(request, 'newpassword.html', {'form1': newPassForm, 'email': request.POST['emailId'].lower()})

    else:
        # user not in the session it will redirected to login page
        return HttpResponseRedirect('/login/')


# validate the entered otp page
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def validateotp(request):
    if request.method == 'POST' and 'emailBeforevalidation' in request.session and 'otpCount' in request.session:
        # get the email from session
        email = request.session["emailBeforevalidation"]
        try:
            # get the user using email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        # check the user is inactive
        if user.userCompanyId.verificationStatus != constants.Active:
            # get the generated otp for the user
            savedOtp = user.otp
            # get the entered otp from the form
            enterOtp = request.POST['otp']
            updatedtime = user.updatedDateTime
            timenow = datetime.datetime.now()
            # setting the otp attempts count
            request.session["otpCount"] += 1
            # check the otp attempt reaches the less than 3
            if request.session["otpCount"] < 3:
                # session expiration check
                if timenow - updatedtime < datetime.timedelta(0, time):
                    if savedOtp == enterOtp:
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
                    else:
                        messages.error(request, "Please enter the valid otp")
                        return HttpResponseRedirect('/validation/')
                # entered otp is correct but session is expired
                elif timenow - updatedtime >= datetime.timedelta(0, time) and savedOtp == enterOtp:
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
            # otp attempts exceeded the limit then it will regenerate the otp and send as mail to user
            else:
                # otp generator
                otp = otpGenerator()
                user.otp = otp
                user.save()
                # reset the otp attempt count
                request.session["otpCount"] = 0
                # send the otp via Email
                sendingEmail(request, user, email, user.otp, 'acc_active_email.html', 'Activate your account',
                             request.get_host(), None,None)
                messages.error(request, "OTP attempts has been reached.New OTP has been sent to your mail.")
                return HttpResponseRedirect('/validation/')
        # user is already active then it will redirect to login page
        else:
            request.session.flush()
            messages.error(request, 'You have already registered')
            return HttpResponseRedirect('/login/')
    # form is not submitted but user in session then it will redirect to security question form
    else:
        if 'emailBeforevalidation' in request.session:
            try:
                user = User.objects.get(email=request.session["emailBeforevalidation"])
            except User.DoesNotExist:
                user = None
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


# security question verification page
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def securityquestion(request):
    if request.method == 'POST' and request.POST['emailId'] is not None:
        secQuesForm = securityQuestionForm(request.POST)
        # get the email from the submitted form
        email = request.POST['emailId'].lower()
        # get the entered answer from the submitted form
        enterAnswer = request.POST['sec_answer'].lower()
        try:
            # get the user using email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
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
                        company = Company.objects.get(pk=user.userCompanyId)
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


# activate the user using uidb64
def activate(request, uidb64, token):
    try:
        # getting the primary key of user from the UID
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        updatedtime = user.updatedDateTime
        timenow = datetime.datetime.now()

    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None:
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


# onboard page
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def onboard(request):
    if request.method == "POST":
        # get the email from the submitted form
        email = request.POST.get('emailId', None)
        if email is not None:
            try:
                user = User.objects.get(email=email)
            except:
                user = None
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


# method is used get the details from csv and save into model
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


# create schema for the user
def tenantSchema(company):
    # getting the current schema from the connection
    currentSchema = connection.schema_name
    # set the connection schema in to public
    connection.set_schema_to_public()
    # creating unique schema for the user
    name = 'ot' + uuid.uuid4().hex[:8].lower()
    while True:
        # check the schema name already exists in the system
        if schemaNameAlreadyExist(name):
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


# rename the domain url
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
                    tenantScheMaURL = getTenantUrl(newDomainName + settings.DOMAIN_NAME)
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


# get the schema url for the user
def getTenantUrl(url):
    try:
        # get the schema from domain url
        tenantScheMaURL = Schema.objects.get(domain_url=url)
    except:
        tenantScheMaURL = None

    return tenantScheMaURL


# customer adding form
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def customermanualform(request):
    customerForm = CustomerManualAddingForm()
    customerShippingForm = CustomerShippingAddressForm()
    return render(request, 'customermanualform.html',
                  {'customerForm':customerForm,'customerShippingForm':customerShippingForm})


# customer csv upload form
def customerautoform(request):
    return render(request, 'customerautoform.html')


# supplier adding form
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def suppliermanualform(request):
    supplierForm = SupplierManualAddingForm()
    supplierShippingForm = SupplierShippingAddressForm()
    return render(request, 'suppliermanualform.html',
                  {'supplierForm': supplierForm, 'supplierShippingForm': supplierShippingForm})

# supplier csv upload form
def supplierautoform(request):
    return render(request, 'supplierautoform.html')


# product adding form
# cahe control is for not allowing the page cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productmanualform(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            # get the current user company name
            userCompany = currentUser.userCompanyId
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            # get the current user company name
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
        itemMasterAddForm = ItemMasterManualForm()
        totalAddress = Sites.objects.filter(siteStatus=constants.Active).all()
        attributeForm = productAttributeForm()
        purchasingForm = purchasingItemsForm()
        salesForm = salesItemsForm()
        measurementForm = itemMeasurementForm()
        storageForm = itemStorageForm()
        parameterForm = itemParameterForm()
        #storeForm = StoreForm()
        #storeForm.fields['storeName'].choices = [(address.siteId, address.siteName) for address in totalAddress]
        return render(request, 'productmanualform.html',
                      {'itemMasterAddForm': itemMasterAddForm, 'attributeForm': attributeForm, 'purchasingForm': purchasingForm,
                       'salesForm': salesForm, 'measurementForm': measurementForm,'storageForm': storageForm, 'parameterForm':parameterForm})
    return HttpResponseRedirect('/login/')


# product csv upload form
def productautoform(request):
    return render(request, 'productautoform.html')


# add the existing customer/supplier into the system
def addExistingTraders(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        # get the email from the session
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            # get the current user company name
            userCompany = currentUser.userCompanyId
            mainUser = currentUser
            email = currentUser.email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            # get the current user company name
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            mainUser = utility.getUserByCompanyId(userCompany)
            email = mainUser.email
        # get the current user company name
        userCompanyName = userCompany.companyName
        emailId = request.POST['email'].lower()
        # get the type of the trader
        type = request.POST['type'].lower()
        site = request.POST['site']
        # check the customer or supplier already exists in the system
        trader = alreadyExistTraders(request, emailId, type, userCompanyName)
        # check entered and user email are same
        if email != emailId:
            if trader[0] is None:
                user = utility.getUserByEmail(emailId)
                # save the customer or supplier into the users system
                customerAndSupplierSave(user.userCompanyId, userCompany, type, 0, site)
                # send mail to the customer/supplier
                sendingEmail(request, mainUser, emailId, user,
                             "add_existing_traders_email.html",
                             userCompanyName + " added you as a " + type, type, None,None)
                return JsonResponse({'status': 'success', 'success_msg': type + ' added successfully'})
            else:
                # customer/supplier already exists in to tne system
                return JsonResponse(
                    {'status': 'error', 'error_msg': 'This ' + type + ' already exist in your system'})
        else:
            # entered and user email are same
            return JsonResponse(
                {'status': 'error', 'error_msg': 'Oops! You cannot add yourself as ' + type})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# check the customer or supplier already exists in user schema
def alreadyExistTraders(request, traderEmail, type, com):
    try:
        # check the customer or supplier already exist in the public schema
        user = User.objects.get(email__iexact=traderEmail)
    except:
        user = None
        UserTrader = None
        add = None

    if user is not None:
        try:
            add = None
            company = user.userCompanyId
            tradersSchema = user.userCompanyId.schemaName
            # check the customer or supplier already exist in the user schema
            if type.lower() == constants.Customer:
                customerObject = Customer.objects.get(companyId=company)
                UserTrader = customerObject
                if customerObject.status == constants.Inactive:
                    customerObject.status = constants.Active
                    customerObject.save()
                    currentSchema = connection.schema_name
                    connection.set_schema(schema_name=tradersSchema)
                    supplierObject = Supplier.objects.get(relId=customerObject.relId)
                    supplierObject.status = constants.Active
                    supplierObject.save()
                    notificationView(request, None,  com + " added you as a " + type, None)
                    connection.set_schema(schema_name=currentSchema)
                    UserTrader = None
                    add = not None
            else:
                supplierObject = Supplier.objects.get(companyId=company)
                UserTrader = supplierObject
                if supplierObject.status == constants.Inactive:
                    supplierObject.status = constants.Active
                    supplierObject.save()
                    currentSchema = connection.schema_name
                    connection.set_schema(schema_name=tradersSchema)
                    customerObject = Customer.objects.get(relId=supplierObject.relId)
                    customerObject.status = constants.Active
                    customerObject.save()
                    notificationView(request,None, com + " added you as a " + type, None)
                    connection.set_schema(schema_name=currentSchema)
                    UserTrader = None
                    add = not None

        except:
            UserTrader = None
            add = None

    return UserTrader, add

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
                            if addressLine1Match >= 90 and addressLine2Match >= 90 and unit1Match >= 90 and unit2Match >= 90:
                                listOfUsersLessPerc.append(comPanyName)
        else:
            for individualUser in company:
                comPanyName = individualUser["companyName"].lower()
                companyMatch = fuzz.ratio(companyName, comPanyName)
                if companyMatch >= 90:
                    listOfUsersHighPerc.append(individualUser)
                elif companyMatch >= 60 and companyMatch < 90:
                    if country == individualUser["country"] and state == individualUser["state"] and pincode.lower() == \
                            individualUser["postalCode"]:
                        addressLine1Match = fuzz.ratio(addressLine1.lower(), individualUser["address_Line1"].lower())
                        addressLine2Match = fuzz.ratio(addressLine2.lower(), individualUser["address_Line2"].lower())
                        unit1Match = fuzz.ratio(unit1.lower(), individualUser["unit1"].lower())
                        unit2Match = fuzz.ratio(unit2.lower(), individualUser["unit2"].lower())
                        if addressLine1Match >= 90 and addressLine2Match >= 90 and unit1Match >= 90 and unit2Match >= 90:
                            listOfUsersLessPerc.append(individualUser)
    return (listOfUsersHighPerc, listOfUsersLessPerc)

# save the customer or supplier into the user schema
def customerAndSupplierSave(traderCompany, company, type, invitationStatus, site):
    # get the current schema name
    currentSchema = connection.schema_name
    # get the customer/supplier schema
    tradersSchema = traderCompany.schemaName
    # generate the unique id for the relationship between user and trader
    relId = uuid.uuid4().hex
    # add customer/supplier in to the user schema
    if type.lower() == constants.Customer:
        if site is None:
            customerSite = utility.getSiteBySiteName(constants.HeadQuarter)
            slaJson = customerSite.siteArea.areaSlaId.slaDetails
        else:
            customerSite = utility.getSiteBySiteId(site)
            slaJson = customerSite.siteArea.areaSlaId.slaDetails
        customerCode = utility.oTtradersCodeGenerator(company.companyName, constants.Customer)
        Customer.objects.create(relId=relId, trdersId=traderCompany, customerCode=customerCode,
                                invitationStatus=invitationStatus, customerSite=customerSite)
        # connect the supplier schema
        connection.set_schema(schema_name=tradersSchema)
        area = utility.getAreaByAreaName(constants.Central)
        if area is None:
            defaultAreaSiteAndSlaCreation(traderCompany)
        supplierSite = utility.getSiteBySiteName(constants.HeadQuarter)
        supplierCode = utility.oTtradersCodeGenerator(traderCompany.companyName, constants.Supplier)
        Supplier.objects.create(relId=relId, trdersId=company, supplierCode=supplierCode, supplierSite=supplierSite,
                                slaFromSupplier=slaJson)
    else:
        if site is None:
            supplierSite = utility.getSiteBySiteName(constants.HeadQuarter)
        else:
            supplierSite = utility.getSiteBySiteId(site)
        supplierCode = utility.oTtradersCodeGenerator(company.companyName, constants.Supplier)
        Supplier.objects.create(relId=relId, trdersId=traderCompany, supplierCode=supplierCode,
                                invitationStatus=invitationStatus, supplierSite=supplierSite,
                                slaFromSupplier=constants.SlaDetailsJson)

        # connect the supplier schema
        connection.set_schema(schema_name=tradersSchema)
        area = utility.getAreaByAreaName(constants.Central)
        if area is None:
            defaultAreaSiteAndSlaCreation(traderCompany)
        customerSite = utility.getSiteBySiteName(constants.HeadQuarter)
        customerCode = utility.oTtradersCodeGenerator(traderCompany.companyName, constants.Customer)
        Customer.objects.create(relId=relId, trdersId=company, customerCode=customerCode, customerSite=customerSite)
        # connect the customer schema
    # reset the connection to user schema
    connection.set_schema(schema_name=currentSchema)


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


def upload_pic(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            usr = utility.getObjectFromSession(request, 'user')
            currentSchemaName = usr.userCompanyId.schemaName
            model = User
            sessionKey = 'user'
            pk = usr.pk
            # get the user from session using email
        if 'subUser' in request.session:
            usr = utility.getObjectFromSession(request, 'subUser')
            currentSchemaName = connection.schema_name
            model = Subuser
            sessionKey = 'subUser'
            pk = usr.pk
        type = request.POST['type'].lower()
        fs = FileSystemStorage(location=settings.MEDIA_ROOT + "/" + currentSchemaName)
        userimage = request.FILES['myfile']
        name = fs.save(userimage.name, userimage)
        if type == constants.Company:
            cmpny = Company.objects.get(pk=usr.userCompanyId)
            cmpny.companyImage = currentSchemaName + "/" + name
            cmpny.save()
        elif type == constants.Profile:
            usr.profilepic = currentSchemaName + "/" + name
            usr.save()
            utility.updateSessionforObject(request, sessionKey, model, pk)

        return JsonResponse({'status': 'success', 'success_msg': type})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def getUserAddress(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'subUser' in request.session:
            loginUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
            a = Subuser.objects.get(userName = loginUser.userName)
            subSites = SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=a).values('subuserSiteAssignSites__siteAddress')
            total = []
            address = UserAddress.objects.filter(status=constants.Active,usradd_id__in = subSites).values('usradd_addressType', 'usradd_id',
                                                                                     'usradd_address_Line1',
                                                                                     'usradd_address_Line2',
                                                                                     'usradd_unit1', 'usradd_unit2',
                                                                                     'usradd_postalCode',
                                                                                     usradd_country_name=F(
                                                                                         'usradd_country__countryName'),
                                                                                     usradd_state__name=F(
                                                                                         'usradd_state__stateName'))
        if 'user' in request.session:
            loginUser = utility.getObjectFromSession(request, 'user')
            company = loginUser.userCompanyId
            total = []
            address = UserAddress.objects.filter(status=constants.Active).values('usradd_addressType', 'usradd_id',
                                                                                 'usradd_address_Line1',
                                                                                 'usradd_address_Line2',
                                                                                 'usradd_unit1', 'usradd_unit2',
                                                                                 'usradd_postalCode',
                                                                                 usradd_country_name=F(
                                                                                     'usradd_country__countryName'),
                                                                                 usradd_state__name=F(
                                                                                     'usradd_state__stateName'))
        for a in list(address):
            item = {}
            item["type"] = a['usradd_addressType']
            item["address"] = a
            total.append(item)
        return JsonResponse({'status': 'success', 'address': total})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def placeOrder(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            subUserForm = SubUserFormDetails()
            editSubUserForm = EditSubUserFormDetails()
            return render(request, 'placeOrder.html',
                          {'company': company, 'user': currentUser, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'status': company.urlchanged,
                           'noti': notiFy, 'subUserForm': subUserForm, 'editSubUserForm': editSubUserForm,
                           'leng': lengTh})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


def customerProductPanel(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            subUserForm = SubUserFormDetails()
            editSubUserForm = EditSubUserFormDetails()
            return render(request, 'customerproductpanel.html',
                          {'company': company, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'subUserForm': subUserForm, 'editSubUserForm': editSubUserForm,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged, })
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


def supplierProductPanel(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            itemMasterAddForm = ItemMasterAddForm()
            return render(request, 'supplierproductpanel.html',
                          {'company': company, 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'itemMasterAddForm': itemMasterAddForm, 'user': currentUser,
                           'leng': lengTh, 'status': company.urlchanged, })
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


def initialiseCsvImport(request):
    connection.set_schema_to_public()
    addressType = Country.objects.all().order_by('countryName')
    if not addressType:
        csvNameArray = ['Countries.csv', 'CurrencyType.csv', 'ItemStatus.csv',
                        'QuantityType.csv', 'CountryCode.csv',
                        'Questions.csv', 'States.csv', 'plan.csv', 'basemodulelist.csv', 'module.csv',
                        'requestaccess.csv']
        modelNameArray = [Country, CurrencyType, ItemStatus, QuantityType, CountryCode, SecurityQuestion, State,
                          Plan, baseModuleList, Module, RequestAccess]
        zipData = zip(csvNameArray, modelNameArray)
        for csvfile, modelName in zipData:
            f = open(os.path.join(IMPORT_FILES_FOLDER, csvfile),encoding='ISO-8859-1')
            reader = csv.DictReader(f)
            rows = list(reader)
            # modelName.objects.all().delete()
            a = modelSave(rows, modelName)
        return HttpResponse('Successfully csv imported ☺')
    else:
        return HttpResponse('Already you have initialized the database ☺')



def notificationView(request,id, desc, types):
    noti = Notification()
    if id == None:
        id = "Null"
    else:
        noti.sendFromId = id
        noti.desc = desc
        noti.type = types
        noti.save()
    return JsonResponse(
        {'status': 'success'})


@csrf_exempt
def notificationStatus(request):
    if 'user' in request.session or 'subUser' in request.session:
        id = request.POST['notificationId']
        noti = Notification.objects.get(pk=id)
        noti.viewed = constants.Yes
        msg = noti.desc
        email = noti.sendFromId
        noti.save()
        return JsonResponse({'status': 'success', 'msg': msg, 'email': email})


@csrf_exempt
def updateProductDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        category = body['type']
        if category == "customer":
            relId = body['relId']
            productId = body['itemCode']
            ordStatus = OrderPlacementfromCustomer.objects.filter(itemCode=productId, customerId=relId,
                                                                  ordstatus=constants.Pending).values()
            if ordStatus:
                currentSchema = connection.schema_name
                userCustomerSchema = Customer.objects.get(relId=relId).trdersId.schemaName
                connection.set_schema(schema_name=userCustomerSchema)
                itemfromSup = ItemFromSupplier.objects.get(itemCode=productId, relId=relId)
                desc = "Rate of " + itemfromSup.itemName + " has been changed. Do you wish to accept the new rate?"
                types = constants.UpdateProductDetails
                notificationView(request,1, desc, types)
                connection.set_schema(schema_name=currentSchema)
                return JsonResponse({'status': 'success', 'success_msg': 'Notification sent successfully'})
            else:
                item = ItemForCustomer.objects.get(itemCode=productId, relId=relId)
                item.price = body['price']
                item.save()
                currentSchema = connection.schema_name
                userCustomerSchema = Customer.objects.get(relId=relId).trdersId.schemaName
                connection.set_schema(schema_name=userCustomerSchema)
                item = ItemFromSupplier.objects.get(itemCode=productId, relId=relId)
                item.price = body['price']
                item.save()
                connection.set_schema(schema_name=currentSchema)
                return JsonResponse({'status': 'success', 'success_msg': 'Product updated successfully'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def resetPassword(request):
    if 'user' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        currentUser = utility.getObjectFromSession(request, 'user')
        subUserProfile = constants.No
        company = currentUser.userCompanyId
        notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
        # getting the length of the notification
        lengTh = len(notiFy)
        if request.method != 'POST':
            Resetpassword = ResetpasswordForm()
        else:
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
                    utility.updateSessionforObject(request, 'user', User, currentUser.pk)
                    return HttpResponseRedirect('/dashboard/')
        return render(request, 'resetpassword.html',
                      {'company': company, 'profileForm': profileForm, 'formreset': Resetpassword,
                       'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                       'noti': notiFy, 'user': currentUser,
                       'leng': lengTh, 'status': company.urlchanged, })
    # user not in the session it will redirect to login page
    return HttpResponseRedirect('/login/')


@csrf_exempt
def userProfile(request):
    if 'user' in request.session and request.method == 'POST':
        email = utility.getObjectFromSession(request, 'user').email
        item = {}
        totalItems = []
        user = User.objects.filter(email=email).values("email", "contactNo", "firstName", "lastName",
                                                       "sec_answer", "sec_question_id",
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
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})



def profileUpdate(request):
    if 'user' in request.session:
        usr = utility.getObjectFromSession(request, 'user')
        cmpny = Company.objects.get(pk=usr.userCompanyId)
        usraddr = UserAddress.objects.get(usradd_addressType=constants.HeadQuarter)
        usr.firstName = request.POST['firstName']
        usr.lastName = request.POST['lastName']
        usr.sec_question_id = request.POST['sec_question']
        usr.sec_answer = request.POST['sec_answer']
        usr.save()
        cmpny.country_id = request.POST['country']
        cmpny.address_Line1 = request.POST['address_Line1']
        cmpny.address_Line2 = request.POST['address_Line2']
        cmpny.unit1 = request.POST['unit1']
        cmpny.unit2 = request.POST['unit2']
        cmpny.state_id = request.POST['state']
        cmpny.postalCode = request.POST['postalCode']
        cmpny.save()
        usraddr.usradd_country_id = request.POST['country']
        usraddr.usradd_address_Line1 = request.POST['address_Line1']
        usraddr.usradd_address_Line2 = request.POST['address_Line2']
        usraddr.usradd_unit1 = request.POST['unit1']
        usraddr.usradd_unit2 = request.POST['unit2']
        usraddr.usradd_state_id = request.POST['state']
        usraddr.usradd_postalCode = request.POST['postalCode']
        usraddr.save()
        return JsonResponse({'status': 'success', 'success_msg': 'Profile Updated successfully'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def schemaNameAlreadyExist(schema_name):
    try:
        scheMa = Schema.objects.get(schema_name=schema_name)
    except:
        scheMa = None
    return scheMa


@csrf_exempt
def inviteSend(request):
    if 'user' in request.session or 'subUser' in request.session:
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            company = mainUser.userCompanyId
            token = mainUser.token
        if 'subUser' in request.session:
            subUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
            mainUser = utility.getUserByCompanyId(company.companyId)
            token = mainUser.token
        userCompanyName = company.companyName
        mail = body['email']
        type = body['type']
        status = body['status']
        if status == "Invite":
            if type.lower() == constants.Customer:
                userTrd = utility.getCustomerByEmail(mail)
                mailId = userTrd.cusAlterNateEmail
                url = settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT + '/subscription/?wsid=' + token + constants.C
            else:
                userTrd = utility.getSupplierByEmail(mail)
                mailId = userTrd.supAlterNateEmail
                url = settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT + '/subscription/?wsid=' + token + constants.S
            userTrd.invitationStatus = 1
            userTrd.save()
            sendingEmail(request, userTrd, mailId, userCompanyName, 'traders_adding_email.html',
                         '' + userCompanyName + ' invite you to join in OrderTango',
                         url , None,None)
            return JsonResponse({'status': 'success', 'success_msg': status + ' sent successfully'})
        else:
            traderUser = utility.getUserByEmail(mail)
            if traderUser:
                wsid = uuid.uuid4().hex
                currentSchema = connection.schema_name
                if type.lower() == constants.Customer:
                    userTrd = utility.getCustomerByEmail(mail)
                    mailId = userTrd.cusAlterNateEmail
                    traderUser = utility.getUserByEmail(mail)
                    traderCompany = traderUser.userCompanyId
                    connection.set_schema(schema_name=traderCompany.schemaName)
                    notificationView(request, userTrd.customerId,
                                           str(traderCompany.companyName) +" sent connection link to your mail",
                                             "inviteSend")
                    connection.set_schema(schema_name=currentSchema)
                else:
                    userTrd = utility.getSupplierByEmail(mail)
                    mailId = userTrd.supAlterNateEmail
                    traderUser = utility.getUserByEmail(mail)
                    traderCompany = traderUser.userCompanyId
                    connection.set_schema(schema_name=traderCompany.schemaName)
                    notificationView(request, userTrd.supplierId,
                                     str(traderCompany.companyName) + " sent connection link to your mail",
                                     "inviteSend")
                    connection.set_schema(schema_name=currentSchema)
                userTrd.connectionCode = wsid
                userTrd.invitationStatus = 2
                userTrd.save()

                sendingEmail(request, mainUser, mailId, traderUser,
                             "add_existing_traders_email.html",
                             userCompanyName + " added you as a " + type, type, None, wsid)
                return JsonResponse({'status': 'success', 'success_msg': status + ' sent successfully'})
            else:
                return JsonResponse({'status': 'success', 'success_msg': 'Requested '+type+' not in the system'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def placedOrderUpdate(request):
    if 'user' in request.session or 'subUser' in request.session:
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        ordNumber = body['orderNo']
        currentSchema = connection.schema_name
        if 'user' in request.session:
            user = utility.getObjectFromSession(request, 'user')
            company = user.userCompanyId
        if 'subUser' in request.session:
            subUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        try:
            ordNumSupAccept = OrderPlacementtoSupplier.objects.get(ordNumber=ordNumber, ordstatus=constants.Accept)
        except:
            ordNumSupAccept = None
            try:
                ordNumSupPending = OrderPlacementtoSupplier.objects.get(~Q(ordstatus=constants.Accept),
                                                                        ordNumber=ordNumber)
            except:
                ordNumSupPending = None

        if ordNumSupAccept:
            return JsonResponse({'status': 'success', 'success_msg': 'Product cannot update or delete'})
        else:
            a = OrderPlacementtoSupplier.objects.get(productId__itemCode = body['productCode'],ordNumber=ordNumber)
            quantity = body['quantity']
            a.quantity = quantity
            a.save()
            desc = company.companyName + " deleted you from their supplier list"
            types = constants.RemoveCustomerOrSupplierOrProduct
            notificationView(request,1, desc, types)
            userCustomerSchema = Supplier.objects.get(relId=a.productId.relId).trdersId.schemaName
            connection.set_schema(schema_name=userCustomerSchema)
            ordNumCus = OrderPlacementfromCustomer.objects.get(itemCode=body['productCode'],ordNumber=ordNumber)
            ordNumCus.quantity = quantity
            ordNumCus.save()
            connection.set_schema(schema_name=currentSchema)
            return JsonResponse({'status': 'success', 'success_msg': 'Product Updated successfully'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def placedOrderDelete(request):
    if 'user' in request.session or 'subUser' in request.session:
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        ordNumber = body['orderNo']
        currentSchema = connection.schema_name
        if 'user' in request.session:
            user = utility.getObjectFromSession(request, 'user')
            company = user.userCompanyId
        if 'subUser' in request.session:
            subUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        try:
            ordNumSupAccept = OrderPlacementtoSupplier.objects.get(ordNumber=ordNumber, ordstatus=constants.Accept)
        except:
            ordNumSupAccept = None
            try:
                ordNumSupPending = OrderPlacementtoSupplier.objects.get(~Q(ordstatus=constants.Accept),
                                                                        ordNumber=ordNumber)
            except:
                ordNumSupPending = None
        if ordNumSupAccept:
            return JsonResponse({'status': 'success', 'success_msg': 'Product cannot update or delete'})
        else:
            userCustomerSchema = Supplier.objects.get(relId=ordNumSupPending.productId.relId).trdersId.schemaName
            connection.set_schema(schema_name=userCustomerSchema)
            ordPlaceFromCus = OrderPlacementfromCustomer.objects.get(ordNumber=ordNumber)
            ordPlaceFromCus.status = constants.Inactive
            ordPlaceFromCus.save()
            connection.set_schema(schema_name=currentSchema)
            ordPlacetoSup = OrderPlacementtoSupplier.objects.get(ordNumber=ordNumber)
            ordPlacetoSup.status = constants.Inactive
            ordPlacetoSup.save()
            return JsonResponse({'status': 'success', 'success_msg': 'Product removed successfully'})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})



# view user page
def viewUser(request):
    if 'user' in request.session or 'subUser' in request.session:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            company = utility.getCompanyBySchemaName(connection.schema_name)
            totalAddress = UserAddress.objects.filter(status=constants.Active).all()
            subUserForm = SubUserFormDetails()

            editSubUserForm = EditSubUserFormDetails()

            usr = RequestAccess.objects.all().values("group")
            reqAccess = []
            type = ['create', 'view', 'update', 'delete']
            d = list(usr.distinct())
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
                          {'company': company, 'profileForm': profileForm, 'reqAccess': reqAccess,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'subUserForm': subUserForm, 'editSubUserForm': editSubUserForm,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


@csrf_exempt
def createSubUser(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        invalidChars = set(string.punctuation.replace("_", ""))
        minLength = 8
        existsUserName = checkExistUserName(request.POST['userName'])
        existsEmail = False
        if request.POST['email']:
            existsEmail = checkExistSubUserEmail(request.POST['email'])
        passWord = request.POST['password']
        if existsUserName is False and existsEmail is False:
            if passWord.isdigit() or not any(x.isupper() for x in passWord) or not any(
                    x.islower() for x in passWord) or len(passWord) < minLength or not any(
                x.isdigit() for x in passWord) or not any(
                char in invalidChars for char in passWord):
                return JsonResponse({'status': 'error',
                                     'error_msg': "Password should contain at least %d characters with a mix of uppercase,lowercase,special character,numeric " % minLength})
            if request.POST['confirm_password'] != passWord:
                return JsonResponse({'status': 'error', 'error_msg': 'Password does not match!!!'})
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            subuser = Subuser()
            subuser.password = make_password(request.POST['password'])
            if 'myfile' in request.FILES:
                subuserimage = request.FILES['myfile']
                imagename = fs.save(subuserimage.name, subuserimage)
                subuser.profilepic = imagename
            subuser.firstName = request.POST['firstName']
            subuser.lastName = request.POST['lastName']
            subuser.userName = request.POST['userName']
            subuser.designation = request.POST['designation']
            subuser.contactNo = request.POST['contactNo']
            subuser.role = request.POST['role']
            subuser.email = request.POST['email'].lower()
            subuser.DOJ = request.POST['DOJ']
            subuser.DOD = ""
            subuser.save()
            sites = request.POST["siteId"]
            if sites == "All":
                sitesAll = Sites.objects.filter(siteArea__areaId=request.POST['areaId']).values()
                for i in sitesAll:
                    subusersiteaassign = SubuserSiteAssign()
                    subusersiteaassign.subuserSiteAssignSubUser = subuser
                    subusersiteaassign.subuserSiteAssignSites_id = i['siteId']
                    subusersiteaassign.save()
            else:
                subusersiteaassign = SubuserSiteAssign()
                subusersiteaassign.subuserSiteAssignSubUser = subuser
                subusersiteaassign.subuserSiteAssignSites = Sites.objects.get(siteId=request.POST["siteId"])
                subusersiteaassign.save()
            s = ''.join(request.POST['subUserAccessJSON'])
            s = s.split(',')
            for req in s:
                subUserAcccess = userSubReqAcc()
                subUserAcccess.subUserId = subuser
                subUserAcccess.subReqAccId = RequestAccess.objects.get(pk=req)
                subUserAcccess.save()
            return JsonResponse({'status': 'success', 'success_msg': 'User created successfully'})
        else:
            if existsUserName:
                return JsonResponse({'status': 'error', 'error_msg': 'User Name is already exists!!!'})
            elif existsEmail:
                return JsonResponse({'status': 'error', 'error_msg': 'Email is already exists!!!'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def updateSubUser(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        try:
            subuser = Subuser.objects.get(pk=request.POST['subUserId'], userName__iexact=request.POST['userName'])
            existsUserName = False
            existsEmail = False
        except:
            subuser = None
        if subuser is None:
            existsUserName = checkExistUserName(request.POST['userName'])
        if request.POST['email']:
            try:
                subuserEmail = Subuser.objects.get(pk=request.POST['subUserId'],
                                                   email__iexact=request.POST['email'])
                existsEmail = False
            except:
                existsEmail = checkExistSubUserEmail(request.POST['email'])
        if existsUserName is False and existsEmail is False:
            subuser = Subuser.objects.get(pk=request.POST['subUserId'])
            subuser.DOD = request.POST['DOD']
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            if 'myfile' in request.FILES:
                subuserimage = request.FILES['myfile']
                imagename = fs.save(subuserimage.name, subuserimage)
                subuser.profilepic = imagename
            subuser.firstName = request.POST['firstName']
            subuser.lastName = request.POST['lastName']
            subuser.userName = request.POST['userName']
            subuser.designation = request.POST['designation']
            subuser.contactNo = request.POST['contactNo']
            subuser.role = request.POST['role']
            subuser.email = request.POST['email'].lower()
            subuser.DOJ = request.POST['DOJ']
            subuser.save()
            sites = request.POST["siteId"]
            SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=subuser.subUserId).delete()
            if sites == "All":
                sitesAll = Sites.objects.filter(siteArea__areaId=request.POST['areaId']).values()
                for i in sitesAll:
                    subusersiteaassign = SubuserSiteAssign()
                    subusersiteaassign.subuserSiteAssignSubUser = subuser
                    subusersiteaassign.subuserSiteAssignSites_id = i['siteId']
                    subusersiteaassign.save()
            else:
                subusersiteaassign = SubuserSiteAssign()
                subusersiteaassign.subuserSiteAssignSubUser = subuser
                subusersiteaassign.subuserSiteAssignSites = Sites.objects.get(siteId=request.POST["siteId"])
                subusersiteaassign.save()
            createAccessArray = request.POST['createAccessArray']
            updateAccessArray = request.POST['updateAccessArray']
            deleteAccessArray = request.POST['deleteAccessArray']
            deleteAccess = deleteAccessArray.split(',')
            createAccess = createAccessArray.split(',')
            try:
                for i in deleteAccess:
                    dele = userSubReqAcc.objects.get(subUserId=request.POST['subUserId'], subReqAccId=i)
                    dele.delete()
            except:
                dele = None
            try:
                for create in createAccess:
                    subUserAcccess = userSubReqAcc()
                    subUserAcccess.subUserId = subuser
                    subUserAcccess.subReqAccId = RequestAccess.objects.get(pk=create)
                    subUserAcccess.save()
            except:
                subUserAcccess = None
            return JsonResponse({'status': 'success', 'success_msg': 'User updated successfully'})
        else:
            if existsUserName:
                return JsonResponse({'status': 'error', 'error_msg': 'User Name is already exists!!!'})
            elif existsEmail:
                return JsonResponse({'status': 'error', 'error_msg': 'Email is already exists!!!'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# check the username is in subuser table
@csrf_exempt
def checkExistUserName(userName):
    try:
        data = Subuser.objects.filter(userName=userName, status=constants.Active).exists()
        if data is not None and data is True:
            return True
        elif data is not None and data is False:
            return False

    except:
        return JsonResponse({'status': 'error'})


# # view user page
# @csrf_exempt
# def viewUser(request):
#     if 'email' in request.session:
#         try:
#             # get the user from session using email
#             user = User.objects.get(email=request.session['email'])
#             username = user.firstName
#             profileForm = UserProfileForm()
#             companyProfileForm = CompanyProfileForm()
#         except:
#             user = None
#         if 'subUserName' in request.session:
#             username = request.session['subUserName']
#         if user is not None:
#             # getting the unviewed notifications for the user
#             notiFy = Notification.objects.filter(viewed="No").order_by('-createdDateTime')
#             # getting the length of the notification
#             lengTh = len(notiFy)
#             return render(request, 'viewuser.html',
#                           {'user': user,'username':username, 'ProfileForm': profileForm, 'companyProfileForm': companyProfileForm,
#                             'noti': notiFy,
#                            'leng': lengTh})
#
#     return HttpResponseRedirect('/login/')


# Fetch the Sub User Data
@csrf_exempt
def fetchSubUserData(request):
    if 'user' in request.session or 'subUser' in request.session:
        try:
            # get the subuser active data from private schema
            userData = Subuser.objects.filter(status=constants.Active).values('subUserId', 'userName', 'designation',
                                                                              'role',
                                                                              'contactNo')

        except:
            userData = None

        if userData is not None:
            return JsonResponse({'status': 'success', 'userData': list(userData)})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# Fetch the Sub User Data
@csrf_exempt
def fetchSubUserDataViaId(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        try:
            body = json.loads(request.body.decode('utf-8'))
            subUserId = body['subUserId']
            # Fetch the User status in subuser data from private schema
            userData = Subuser.objects.filter(pk=subUserId)
        except:
            userData = None

    if userData is not None:
        item = {}
        totalItems = []
        subuseracc = []
        user = SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=subUserId).values("subuserSiteAssignSites__siteId","subuserSiteAssignSubUser__firstName",
                                                                    "subuserSiteAssignSubUser__lastName", "subuserSiteAssignSubUser__userName",
                                                                  "subuserSiteAssignSubUser__designation", "subuserSiteAssignSubUser__contactNo",
                                                            "subuserSiteAssignSubUser__role", "subuserSiteAssignSubUser__DOJ", "subuserSiteAssignSubUser__DOD",
                                                            "subuserSiteAssignSubUser__DOD", "subuserSiteAssignSubUser__profilepic","subuserSiteAssignSubUser__email",
                                                                                           "subuserSiteAssignSites__siteArea")
        subUserAcccess = userSubReqAcc.objects.filter(subUserId=subUserId).values('subReqAccId_id')
        item['totalItem'] = list(user)
        for i in subUserAcccess:
            subuseracc.append(i['subReqAccId_id'])
        totalItems.append(item)
        item['subuseracc'] = subuseracc
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# Delete the Sub User Data
@csrf_exempt
def deleteSubUserData(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        try:
            body = json.loads(request.body.decode('utf-8'))
            subUserId = body['subUserId']
            # Update the status in subuser data from private schema
            Subuser.objects.filter(pk=subUserId).update(status=constants.Inactive)
            userData = 1
        except:
            userData = None

        if userData is not None:
            return JsonResponse({'status': 'success'})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def checkExistSubUserEmail(email):
    try:
        data = Subuser.objects.filter(email__iexact=email, status=constants.Active).exists()
        if data is not None and data is True:
            return True
        elif data is not None and data is False:
            return False

    except:
        return JsonResponse({'status': 'error'})


# Unauthorize page
def unauthorize(request):
    # ip is for home URL redirection
    return render(request, 'unauthorize.html')


# View Address page
def viewAddress(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            shippingAddressForm = UserShippingAddressForm()
            shippingAddressEditForm = UserShippingAddressEditForm()
            return render(request, 'viewaddress.html',
                          {'company': company, 'form': userForm, 'ProfileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'shippingAddressForm': shippingAddressForm,
                           'shippingAddressEditForm': shippingAddressEditForm,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged, })
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


def fetchAddressViaCompanyId(request):
    if 'user' in request.session or 'subUser' in request.session:
        shipAddr = UserAddress.objects.filter(status=constants.Active).values('usradd_id',
                                                                              'usradd_addressType',
                                                                              'usradd_address_Line1',
                                                                              'usradd_address_Line2',
                                                                              'usradd_unit1', 'usradd_unit2',
                                                                              'usradd_postalCode',
                                                                              usradd_country_name=F(
                                                                                  'usradd_country__countryName'),
                                                                              usradd_state__name=F(
                                                                                  'usradd_state__stateName'))
        return JsonResponse({'status': 'success', 'addressArray': list(shipAddr)})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def addUserAddressUpdate(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)

        if 'user' in request.session:
            loginUser = utility.getObjectFromSession(request, 'user')
            company = loginUser.userCompanyId
            # get the user from session using email
        if 'subUser' in request.session:
            loginUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        if body['type'] == constants.Update:
            userAdd = UserAddress.objects.get(usradd_id=body['usradd_id'])
            addNewUserAddress(request, userAdd, body)
            return JsonResponse({'status': 'success', 'success_msg': 'Updated successfully'})
        else:
            try:
                userAdd = UserAddress.objects.filter(usradd_addressType=body['usradd_addressType'])
            except:
                userAdd = None
            if userAdd:
                return JsonResponse({'status': 'success', 'success_msg': 'Already Exist Address Type'})
            else:
                userAdd = UserAddress()
                userAdd.usradd_userid = company
                addNewUserAddress(request, userAdd, body)
                return JsonResponse({'status': 'success', 'success_msg': 'Address added successfully'})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def addNewUserAddress(request, userAdd, body):
    userAdd.usradd_addressType = body['usradd_addressType']
    userAdd.usradd_country = Country.objects.get(pk=body['usradd_country'])
    userAdd.usradd_address_Line1 = body['usradd_address_Line1']
    userAdd.usradd_address_Line2 = body['usradd_address_Line2']
    userAdd.usradd_unit1 = body['usradd_unit1']
    userAdd.usradd_unit2 = body['usradd_unit2']
    userAdd.usradd_state = State.objects.get(pk=body['usradd_state'])
    userAdd.usradd_postalCode = body['usradd_postalCode']
    userAdd.save()


@csrf_exempt
def fetchUserAddressDataViaId(request):
    if 'user' in request.session or 'subUser' in request.session:
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(request.body.decode('utf-8'))
        address = UserAddress.objects.filter(pk=body['userAddressId']).values('usradd_id',
                                                                              'usradd_addressType',
                                                                              'usradd_address_Line1',
                                                                              'usradd_address_Line2',
                                                                              'usradd_unit1', 'usradd_unit2',
                                                                              'usradd_postalCode',
                                                                              'usradd_country_id',
                                                                              'usradd_state_id',
                                                                              usradd_country_name=F(
                                                                                  'usradd_country__countryName'),
                                                                              usradd_state__name=F(
                                                                                  'usradd_state__stateName'))
        return JsonResponse({'status': 'success', 'userAddress': list(address)})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def removeUserAddressDataViaId(request):
    if 'user' in request.session or 'subUser' in request.session:
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(request.body.decode('utf-8'))
        address = UserAddress.objects.get(pk=body['userAddressId'])
        address.status = constants.Inactive
        address.save()
        return JsonResponse({'status': 'success', 'success_msg': 'Deleted successfully'})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def createSla(request):
    if 'user' in request.session or 'subUser' in request.session:
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(request.body.decode('utf-8'))
        slaType = body['slaType']
        alreadyExistsSla = utility.getSlaBySlaName(slaType)
        if alreadyExistsSla is None:
            slaJson = body['slaJson']
            sla = serviceLevelAgreement(slaType=slaType,
                                        slaDetails=slaJson,
                                        )
            sla.save()
            return JsonResponse({'status': 'success', 'success_msg': 'SLA Added successfully'})
        else:
            return JsonResponse({'status': 'error', 'error_msg': 'SLA Name already exists'})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# Create Or View SLA panel
def createOrViewSLA(request):
    if ('user' or 'subUser') in request.session:
        userForm = UserForm()
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Active
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            shippingAddressForm = UserShippingAddressForm()
            shippingAddressEditForm = UserShippingAddressEditForm()
            return render(request, 'createOrViewSLA.html',
                          {'company': company, 'form': userForm, 'ProfileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'shippingAddressForm': shippingAddressForm,
                           'shippingAddressEditForm': shippingAddressEditForm,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



# unauthorizepage page
def unauthorizepage(request):
    # ip is for home URL redirection
    return render(request, 'unauthorizepage.html', {'ip': settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT})


# View Area page
def viewArea(request):
    if 'user' in request.session or 'subUser' in request.session:
        userForm = UserForm()
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            areaAddForm = AreaAddForm()
            areaEditForm = AreaEditForm()
            return render(request, 'viewArea.html',
                          {'company': company, 'form': userForm, 'ProfileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'areaAddForm': areaAddForm, 'areaEditForm': areaEditForm,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


# Fetch the Area Data
@csrf_exempt
def fetchAreaData(request):
    if 'user' in request.session or 'subUser' in request.session:
        areaData = Area.objects.filter(areaStatus=constants.Active).values('areaId', 'areaName', 'areaDesc', 'areaSlaId__slaType').order_by('areaId')
        return JsonResponse({'status': 'success', 'areaData': list(areaData)})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def createAreaDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        if 'user' in request.session:
            loginUser = utility.getObjectFromSession(request, 'user')
            company = loginUser.userCompanyId
            # get the user from session using email
        if 'subUser' in request.session:
            loginUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        if body['type'] == constants.Create:
            AreaDet = utility.getAreaByAreaName(body['areaName'])
            if AreaDet:
                return JsonResponse({'status': 'error', 'error_msg': 'Area Name is already exist'})
            else:
                areaDetails = Area()
                addNewArea(request, areaDetails, body)
                return JsonResponse({'status': 'success', 'success_msg': 'Area added successfully'})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def addNewArea(request, areaDetails, body):
    areaDetails.areaName = body['areaName']
    areaDetails.areaDesc = body['areaDesc']
    areaDetails.areaSlaId_id = body['areaSla']
    areaDetails.save()


@csrf_exempt
def fetchAreaDataViaId(request):
    if 'user' in request.session or 'subUser' in request.session:
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(request.body.decode('utf-8'))
        areaData = Area.objects.filter(pk=body['areaId']).values('areaId', 'areaName', 'areaDesc', 'areaSlaId')
        return JsonResponse({'status': 'success', 'areaData': list(areaData)})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def updateAreaDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        if 'user' in request.session:
            loginUser = utility.getObjectFromSession(request, 'user')
            company = loginUser.userCompanyId
            # get the user from session using email
        if 'subUser' in request.session:
            loginUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        if body['type'] == constants.Update:
            try:
                AreaDet = Area.objects.filter(~Q(areaId=body['areaId']), areaName=body['areaName'])
            except:
                AreaDet = None
            if AreaDet:
                return JsonResponse({'status': 'error', 'error_msg': 'Already Exist Area Name'})
            else:
                areaDetails = Area.objects.get(areaId=body['areaId'])
                if areaDetails.pk == 1:
                    body['areaName'] = constants.Central
                addNewArea(request, areaDetails, body)
                return JsonResponse({'status': 'success', 'success_msg': 'Area updated successfully'})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def removeAreaDataViaId(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        if 'user' in request.session:
            loginUser = utility.getObjectFromSession(request, 'user')
            company = loginUser.userCompanyId
            # get the user from session using email
        if 'subUser' in request.session:
            loginUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        try:
            siteDet = Sites.objects.filter(siteArea=body['areaId'], siteStatus=constants.Active).values()
        except:
            siteDet = None

        if siteDet:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'Area has active sites.So cannot able to delete the area'})
        else:
            areaDetails = Area.objects.get(areaId=body['areaId'])
            areaDetails.areaStatus = constants.Inactive
            areaDetails.save()
            return JsonResponse({'status': 'success', 'success_msg': 'Area removed successfully'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# Fetch the Pending Area Data (which area data are not create sla)
@csrf_exempt
def fetchPendingAreaDataForSLA(request):
    if 'user' in request.session or 'subUser' in request.session:
        areaData = []
        activeAreaData = Area.objects.filter(areaStatus=constants.Active).values()
        for i in activeAreaData:
            SLAData = serviceLevelAgreement.objects.filter(slaAreaId_id=i['areaId'],
                                                           slaStatus=constants.Active).values()
            if SLAData.count() == 0:
                areaData.append(i)
        return JsonResponse({'status': 'success', 'areaData': list(areaData)})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def viewSite(request):
    if ('user' or 'subUser') in request.session:
        userForm = UserForm()
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if True:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            AddSiteFormdetails = AddSiteForm()
            EditSiteFormdetails = EditSiteForm()
            return render(request, 'viewsite.html',
                          {'company': company, 'form': userForm, 'ProfileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy, 'AddSiteForm': AddSiteFormdetails, 'EditSiteForm': EditSiteFormdetails,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged, })
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



def statusChangeForTrader(trader, status):
    trader.status = status
    trader.save


def createPlaceOrderHtml(userObject,supplierObject,orderObjects,supplierUser, orderDetail):
    return render_to_string('poorder.html', {'userObject':userObject,'supplierObject':supplierObject,'orderArray':orderObjects,'supplierUser':supplierUser,'orderDetail':orderDetail})


@csrf_exempt
def fetchSiteDataForSlaAssign(request):
    if ('user' in request.session or 'subUser' in request.session):
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            noti = Notification.objects.get(pk=request.GET['notificationId'])
            noti.viewed = constants.Yes
            noti.save()
            # getting the length of the notification
            lengTh = len(notiFy)
            usrId = request.GET['id']
            cusItems = {}
            supItems = {}
            supAreaName = Sites.objects.all().values('siteName', 'siteId')
            totalItems = list(supAreaName)
            supItems['supArea'] = totalItems
            cusAreaName = CustomerSiteDetails.objects.filter(userCustSitesCompany=usrId).values('userCustSiteName','userCustSiteId')
            totalItems = list(cusAreaName)
            cusItems['cusSites'] = totalItems
            return render(request, 'assignsla.html',{'cusItems': cusItems, 'supItems': supItems, 'company': company, 'user': currentUser, 'form': userForm,
                                                     'ProfileForm': ProfileForm,'companyProfileForm': companyProfileForm,'subUserProfile': subUserProfile, 'status': company.urlchanged,
                                                     'noti': notiFy, 'leng': lengTh,'usrId': usrId})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



def initialiseCsvImportPrivate():
    csvNameArray = ['typeOfArticle.csv', 'productCategory.csv', 'merchantCategory.csv',
                    'merchantSubCategoryOne.csv', 'merchantSubCategoryTwo.csv',
                    'storageConditions.csv', 'taxCode.csv', 'itemDimension.csv', 'weightUnit.csv',
                    'itemDepartment.csv','TypeOfSites.csv']
    modelNameArray = [typeOfArticle, productCategory, merchantCategory, merchantSubCategoryOne, merchantSubCategoryTwo, storageConditions, taxCode,
                      itemDimension, weightUnit, itemDepartment,TypeOfSites]
    zipData = zip(csvNameArray, modelNameArray)
    for csvfile, modelName in zipData:
        logger.info(csvfile + " import started")
        f = open(os.path.join(IMPORT_FILES_FOLDER, csvfile))
        reader = csv.DictReader(f)
        rows = list(reader)
        # modelName.objects.all().delete()
        a = modelSave(rows, modelName)
        logger.info(csvfile + " import ended")



# loading states from table based on selection country for add/reister users
def load_sites(request):
    # get the country id
    siteArea_id = request.GET.get('siteArea_id')
    # get the states for the particular country
    sites = Sites.objects.filter(siteArea_id=siteArea_id).order_by('siteName')
    # serialize in to Json format
    data = serializers.serialize('json', sites)
    return JsonResponse({'sites': data})


def fetchAllSupplierForSlaAssign(request):
    if ('user' in request.session or 'subUser' in request.session):
        userForm = UserForm()
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
        if urls:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            lengTh = len(notiFy)
            sup = Supplier.objects.all().values('supCompanyName','supplierId')
            sla =serviceLevelAgreement.objects.all().values('slaType','slaId')
            return render(request, 'assignSlaToSupplier.html',{'sup':sup,'sla':sla,'user': currentUser, 'form': userForm, 'ProfileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile, 'status': company.urlchanged,
                                                     'noti': notiFy, 'leng': lengTh})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



