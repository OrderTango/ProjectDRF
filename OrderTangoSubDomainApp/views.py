from django.shortcuts import render, redirect
from django.http import  HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control
from OrderTangoSubDomainApp.forms import *
from OrderTangoSubDomainApp import utilitySD
from OrderTangoApp import utility
from OrderTangoApp import views as mainView
from OrderTangoApp.tokens import account_activation_token
from django.template.loader import render_to_string
import csv,datetime,xlrd
from django.utils.encoding import force_bytes
import uuid, io, json
from django.db.models import Q, F
from django.core.files.storage import FileSystemStorage
from django.utils.http import  urlsafe_base64_decode,urlsafe_base64_encode
from OrderTangoApp.forms import *
from django.utils.encoding import  force_text
from OrderTangoOrdermgmtApp.models import OrderPlacementtoSupplier
from OrderTangoOrderFulfilmtApp.models import OrderPlacementfromCustomer,OrderDetails
from django.contrib.auth.hashers import make_password
import stripe
from django.contrib import messages

"""Customer save by manual form post. Check all the user defined valdations for customer adding functionalities,
If invitation is requested by the supplier then the invitation link sent to the customer via Email to join the system"""
def customerSave(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            userCompanyName = userCompany.companyName
            token = currentUser.token
            email = currentUser.email
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            userCompanyName = userCompany.companyName
            mainUser = utility.getUserByCompanyId(userCompany)
            token = mainUser.token
            email = mainUser.email
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                if utility.checkEntryCountBasedOnPlanAndFeatures(utility.getCompanyBySchemaName(connection.schema_name),
                                                                 'Customer',
                                                                 utilitySD.getCountOftheModelByModelName(
                                                                     "Customer")):
                    # get the customer/supplier email from the submitted form
                    emailId = request.POST['cusEmail'].lower()
                    # get the contact number from the submitted form
                    contactNumber = request.POST['cusContactNo']
                    # get the company name from the submitted form
                    companyName = request.POST['cusCompanyName']
                    cusCommunicationEmail = request.POST['cusCommunicationEmail'].lower()
                    resultSet = []
                    resultAlreadyExistSet = []
                    a = {}
                    b = {}
                    # create an object for validating email,country,state,contactnumber,company name
                    key = {}
                    key['email'] = request.POST['cusEmail']
                    key['country'] = Country.objects.get(pk=request.POST['cusCountry']).countryName
                    key['state'] = State.objects.get(pk=request.POST['cusState']).stateName
                    key['contactNo'] = contactNumber
                    key['companyName'] = companyName
                    # get the user type customer/supplier
                    postalCode = request.POST['cusPostalCode']
                    a["currentData"] = key
                    # check the company address and shipping address are same
                    if 'sameAddress' in request.POST:
                        usradd_country = key['country']
                        usradd_state =  key['state']
                        shippingPostalCode = postalCode
                    else:
                        usradd_country = Country.objects.get(pk=request.POST['cusShipCountry']).countryName
                        usradd_state = State.objects.get(pk=request.POST['cusShipState']).stateName
                        shippingPostalCode= request.POST['cusShipPostalCode']
                    # check the fields validations
                    if 'cusSameEmail' in request.POST:
                        cusAlterNateEmail = emailId
                    else:
                        cusAlterNateEmail = request.POST['cusAlterNateEmail'].lower()
                    valiadtions = csvFieldValidation(emailId, contactNumber, key['country'], key['state'],
                                                     usradd_country,
                                                     usradd_state,postalCode,shippingPostalCode, b,
                                                     cusAlterNateEmail,cusCommunicationEmail)
                    # check entered and user email are same
                    if email != emailId:
                        if valiadtions is True:
                            # check entered user is already exists in our system
                            trader = alreadyExistCustomerOrSupplier(emailId, contactNumber, companyName,
                                                                    constants.Customer)
                            if trader[0] is None and trader[1] is None:
                                # email check using fuzzy logic
                                userList = views.fuzzyEmail(emailId, "csv")
                                if not userList:
                                    # contact number check using fuzzy logic
                                    contactFuzzy = views.fuzzyContactNumber(contactNumber)
                                    if contactFuzzy:
                                        userList += contactFuzzy
                                if not userList:
                                    # company name check using fuzzy logic
                                    temp = views.fuzzyCompanyName(companyName, key['country'], key['state'],
                                                                  request.POST['cusPostalCode'],
                                                            request.POST['cusUnit1'], request.POST['cusUnit2'],
                                                            request.POST['cusAddress_Line1'],
                                                            request.POST['cusAddress_Line2'], "csv")
                                    if temp[0]:
                                        userList += (temp[0])
                                    if not userList and temp[1]:
                                        userList += (temp[1])
                                # show rhe matched data for the entered cutomer/supplier from the system
                                if userList:
                                    b["matchedData"] = list(userList)
                                    a.update(b)
                                    resultSet.append(a)
                                else:
                                    customer = Customer()
                                    customer.customerCode = utilitySD.oTtradersCodeGenerator(userCompanyName,
                                                                                             constants.Customer)
                                    invitationStatus = 0
                                    if request.POST.getlist('emailSent'):
                                        url = settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT \
                                              + '/subscription/?wsid=' + token + constants.C
                                        mainView.sendingEmail(request, customer, emailId, userCompanyName,
                                                              'traders_adding_email.html',
                                                     userCompanyName + ' invite you to join in OrderTango',
                                                     url, None, None)
                                        invitationStatus = 1
                                    customerDetailSave(customer,companyName,request.POST['cusCountry'],
                                                       request.POST['cusAddress_Line1'],
                                                       request.POST['cusAddress_Line2'],request.POST['cusUnit1'],
                                                       request.POST['cusUnit2'],
                                                       request.POST['cusState'],request.POST['cusPostalCode'],
                                                       request.POST['contactPerson'],
                                                       emailId,request.POST['cusCountryCode'],
                                                       request.POST['cusContactNo'],
                                                       invitationStatus,cusAlterNateEmail,cusCommunicationEmail)
                                    # save the customer/supplier info
                                    customerShipping = CustomerShippingAddress()
                                    customerShipping.shippingCustomer =customer
                                    if 'sameAddress' in request.POST:
                                        customerShippingAddressSave(customerShipping, customer.cusAddress_Line1,
                                                                    customer.cusAddress_Line2, customer.cusUnit1,
                                                                    customer.cusUnit2, customer.cusCountry_id,
                                                                    customer.cusState_id, customer.cusPostalCode)
                                    else:
                                        customerShippingAddressSave(customerShipping,
                                                                    request.POST['cusShipAddress_Line1'],
                                                                    request.POST['cusShipAddress_Line2'],
                                                                    request.POST['cusShipUnit1'],
                                                                    request.POST['cusShipUnit2'],
                                                                    request.POST['cusShipCountry'],
                                                                    request.POST['cusShipState'],
                                                                    request.POST['cusShipPostalCode'])
                            elif trader[1] is not None:
                                b["error"] = 'This customer is activated again in OT'
                                a.update(b)
                                resultAlreadyExistSet.append(a)
                            # customer/supplier already exists in to tne system
                            else:
                                b["error"] = 'The below customer already exist in your system'
                                a.update(b)
                                resultAlreadyExistSet.append(a)
                        # field validations fails
                        else:
                            a.update(valiadtions)
                            resultAlreadyExistSet.append(a)
                    # entered and user email are same
                    else:
                        b["error"] = 'Oops! You cannot add yourself as a customer'
                        a.update(b)
                        resultAlreadyExistSet.append(a)
                    # matched data or validation failure data present then it will show the data details
                    if resultSet or resultAlreadyExistSet:
                        errormessages = errormessage(constants.Customer, resultSet, resultAlreadyExistSet, "")
                        return JsonResponse({'status': 'error', 'error_msg': 'matchedData',
                                             'matchedDataContent': errormessages})
                    # no matched data or validation failures it will show success message
                    else:
                        return JsonResponse({'status': 'success', 'success_msg': 'Customer added successfully'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Your Purchased Customer Limit Is Exceeded'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to save all the customer information into current schema"""
def customerDetailSave(customer,companyName,country,address1,address2,unit1,unit2,
                        state,postalCode,contactPerson,email,countryCode,contactNo,
                    invitationStatus,cusAlterNateEmail,cusCommunicationEmail):
    customer.cusCompanyName = companyName
    customer.cusCountry_id = country
    customer.cusAddress_Line1 = address1
    customer.cusAddress_Line2 = address2
    customer.cusUnit1 = unit1
    customer.cusUnit2 = unit2
    customer.cusState_id = state
    customer.cusPostalCode = postalCode
    customer.contactPerson = contactPerson
    customer.cusEmail = email
    customer.cusCountryCode_id = countryCode
    customer.cusContactNo = contactNo
    customer.invitationStatus = invitationStatus
    customer.cusAlterNateEmail = cusAlterNateEmail
    customer.cusCommunicationEmail = cusCommunicationEmail
    customer.save()


"""Method is used to save the customer shipplng address information into current schema"""
def customerShippingAddressSave(customerAddress,address1,address2,unit1,unit2,country,state,postalCode):
    customerAddress.cusShipAddress_Line1=address1
    customerAddress.cusShipAddress_Line2=address2
    customerAddress.cusShipUnit1=unit1
    customerAddress.cusShipUnit2=unit2
    customerAddress.cusShipCountry_id=country
    customerAddress.cusShipState_id=state
    customerAddress.cusShipPostalCode=postalCode
    customerAddress.save()


"""Supplier save by manual form post. Check all the user defined valdations for supplier adding functionalities,
If invitation is requested by the customer then the invitation link sent to the supplier via Email to join the system"""
def supplierSave(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        # get the current user
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            userCompanyName = userCompany.companyName
            token = currentUser.token
            email = currentUser.email
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            userCompanyName = userCompany.companyName
            mainUser = utility.getUserByCompanyId(userCompany)
            token = mainUser.token
            email = mainUser.email
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                if utility.checkEntryCountBasedOnPlanAndFeatures(utility.getCompanyBySchemaName(connection.schema_name),
                                                                 'Supplier',
                                                                 utilitySD.getCountOftheModelByModelName(
                                                                     "Supplier")):
                    # get the customer/supplier email from the submitted form
                    emailId = request.POST['supEmail'].lower()
                    # get the contact number from the submitted form
                    contactNumber = request.POST['supContactNo']
                    # get the company name from the submitted form
                    companyName = request.POST['supCompanyName']
                    supCommunicationEmail = request.POST['supCommunicationEmail'].lower()
                    resultSet = []
                    resultAlreadyExistSet = []
                    a = {}
                    b = {}
                    # create an object for validating email,country,state,contactnumber,company name
                    key = {}
                    key['email'] = request.POST['supEmail']
                    key['country'] = Country.objects.get(pk=request.POST['supCountry']).countryName
                    key['state'] = State.objects.get(pk=request.POST['supState']).stateName
                    key['contactNo'] = contactNumber
                    key['companyName'] = companyName
                    # get the user type customer/supplier
                    postalCode = request.POST['supPostalCode']
                    a["currentData"] = key
                    # check the company address and shipping address are same
                    if 'supSameAddress' in request.POST:
                        usradd_country = key['country']
                        usradd_state =  key['state']
                        shippingPostalCode = postalCode
                    else:
                        usradd_country = Country.objects.get(pk=request.POST['supShipCountry']).countryName
                        usradd_state = State.objects.get(pk=request.POST['supShipState']).stateName
                        shippingPostalCode = request.POST['supShipPostalCode']
                    # check the fields validations
                    if 'supSameEmail' in request.POST:
                        supAlterNateEmail = emailId
                    else:
                        supAlterNateEmail = request.POST['supAlterNateEmail'].lower()
                    valiadtions = csvFieldValidation(emailId, contactNumber, key['country'], key['state'],
                                                     usradd_country,
                                                     usradd_state,postalCode,shippingPostalCode
                                                     ,b,supAlterNateEmail,supCommunicationEmail)
                    # check entered and user email are same
                    if email != emailId:
                        if valiadtions is True:
                            # check entered user is already exists in our system
                            trader = alreadyExistCustomerOrSupplier(emailId, contactNumber, companyName,
                                                                    constants.Supplier)
                            if trader[0] is None and trader[1] is None:
                                # email check using fuzzy logic
                                userList = views.fuzzyEmail(emailId, "csv")
                                if not userList:
                                    # contact number check using fuzzy logic
                                    contactFuzzy = views.fuzzyContactNumber(contactNumber)
                                    if contactFuzzy:
                                        userList += contactFuzzy
                                if not userList:
                                    # company name check using fuzzy logic
                                    temp = views.fuzzyCompanyName(companyName, key['country'], key['state'],
                                                                  request.POST['supPostalCode'],
                                                            request.POST['supUnit1'], request.POST['supUnit2'],
                                                            request.POST['supAddress_Line1'],
                                                            request.POST['supAddress_Line2'], "csv")
                                    if temp[0]:
                                        userList += (temp[0])
                                    if not userList and temp[1]:
                                        userList += (temp[1])
                                # show rhe matched data for the entered cutomer/supplier from the system
                                if userList:
                                    b["matchedData"] = list(userList)
                                    a.update(b)
                                    resultSet.append(a)
                                else:
                                    supplier = Supplier()
                                    supplier.supplierCode = utilitySD.oTtradersCodeGenerator(userCompanyName,
                                                                                             constants.Supplier)
                                    invitationStatus = 0
                                    if request.POST.getlist('supEmailSent'):
                                        url = settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT + \
                                              '/subscription/?wsid=' + token + constants.S
                                        mainView.sendingEmail(request, supplier, emailId, userCompanyName,
                                                              'traders_adding_email.html',
                                                      userCompanyName + ' invite you to join in OrderTango',
                                                     url, None, None)
                                        invitationStatus = 1
                                    supplierDetailSave(supplier, companyName, request.POST['supCountry'],
                                                       request.POST['supAddress_Line1'],
                                                       request.POST['supAddress_Line2'], request.POST['supUnit1'],
                                                       request.POST['supUnit2'],
                                                       request.POST['supState'], request.POST['supPostalCode'],
                                                       request.POST['supContactPerson'],
                                                       emailId, request.POST['supCountryCode'],
                                                       request.POST['supContactNo'],
                                                       invitationStatus,supAlterNateEmail,supCommunicationEmail)

                                    supplierShipping = SupplierShippingAddress()
                                    supplierShipping.shippingSupplier =supplier
                                    if 'supSameAddress' in request.POST:
                                        supplierShippingAddressSave(supplierShipping, supplier.supAddress_Line1,
                                                                    supplier.supAddress_Line2, supplier.supUnit1,
                                                                    supplier.supUnit2, supplier.supCountry_id,
                                                                    supplier.supState_id, supplier.supPostalCode)
                                    else:
                                        supplierShippingAddressSave(supplierShipping,
                                                                    request.POST['supShipAddress_Line1'],
                                                                    request.POST['supShipAddress_Line2'],
                                                                    request.POST['supShipUnit1'],
                                                                    request.POST['supShipUnit2'],
                                                                    request.POST['supShipCountry'],
                                                                    request.POST['supShipState'],
                                                                    request.POST['supShipPostalCode'])
                            elif trader[1] is not None:
                                b["error"] = 'This supplier is activated again in OT'
                                a.update(b)
                                resultAlreadyExistSet.append(a)
                            # customer/supplier already exists in to tne system
                            else:
                                b["error"] = 'The below supplier already exist in your system'
                                a.update(b)
                                resultAlreadyExistSet.append(a)
                        # field validations fails
                        else:
                            a.update(valiadtions)
                            resultAlreadyExistSet.append(a)
                    # entered and user email are same
                    else:
                        b["error"] = 'Oops! You cannot add yourself as a supplier'
                        a.update(b)
                        resultAlreadyExistSet.append(a)
                    # matched data or validation failure data present then it will show the data details
                    if resultSet or resultAlreadyExistSet:
                        errormessages = errormessage(constants.Supplier, resultSet, resultAlreadyExistSet, "")
                        return JsonResponse({'status': 'error', 'error_msg': 'matchedData',
                                             'matchedDataContent': errormessages})
                    # no matched data or validation failures it will show success message
                    else:
                        return JsonResponse({'status': 'success', 'success_msg': 'Vendor added successfully'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Your Purchased Vendor Limit Is Exceeded'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to save all the supplier information into current schema"""
def supplierDetailSave(supplier,companyName,country,address1,address2,unit1,unit2,
                        state,postalCode,contactPerson,email,countryCode,contactNo,
                       invitationStatus,alternateEmail,communicationEmail):
    supplier.supCompanyName = companyName
    supplier.supCountry_id = country
    supplier.supAddress_Line1 = address1
    supplier.supAddress_Line2 = address2
    supplier.supUnit1 = unit1
    supplier.supUnit2 = unit2
    supplier.supState_id = state
    supplier.supPostalCode = postalCode
    supplier.contactPerson = contactPerson
    supplier.supEmail = email
    supplier.supCountryCode_id = countryCode
    supplier.supContactNo = contactNo
    supplier.invitationStatus = invitationStatus
    supplier.supAlterNateEmail = alternateEmail
    supplier.supCommunicationEmail = communicationEmail
    supplier.save()


"""Method is used to save the supplier shipplng address information into current schema"""
def supplierShippingAddressSave(supplierAddress,address1,address2,unit1,unit2,country,state,postalCode):
    supplierAddress.supShipAddress_Line1=address1
    supplierAddress.supShipAddress_Line2=address2
    supplierAddress.supShipUnit1=unit1
    supplierAddress.supShipUnit2=unit2
    supplierAddress.supShipCountry_id=country
    supplierAddress.supShipState_id=state
    supplierAddress.supShipPostalCode=postalCode
    supplierAddress.save()


"""Method is to check whether customer/supplier already exists in the current schema
Parameters - email = Customer/Supplier Email, contactNo =  Customer/Supplier contact number,
companyName = Customer/Supplier company name, type = Customer/Supplier"""
def alreadyExistCustomerOrSupplier(email,contactNo,companyName,type):
    try:
        add = None
        if type.lower() == constants.Customer:
            customerObject = utilitySD.getCustomerByEmail(email)
            if customerObject is None:
                customerObject = utilitySD.getCustomerByContactNo(contactNo)
            if customerObject is None:
                customerObject = utilitySD.getCustomerByCompanyName(companyName)
            UserTrader = customerObject
            if customerObject:
                if customerObject.status == constants.Inactive:
                    UserTrader = None
                    add = None
        else:
            supplierObject = utilitySD.getSupplierByEmail(email)
            if supplierObject is None:
                supplierObject = utilitySD.getSupplierByContactNo(contactNo)
            if supplierObject is None:
                supplierObject = utilitySD.getSupplierByCompanyName(companyName)
            UserTrader = supplierObject
            if supplierObject:
                if supplierObject.status == constants.Inactive:
                    UserTrader = None
                    add = None
    except:
        UserTrader = None
        add = None
    return UserTrader, add


"""Method is to add invited Customer/Supplier to the current schema at the registration time.
Parameters - wsid = customer/supplier token,companyName = current user company name"""
def addInvitedCustomerOrSupplier(wsid,companyName):
    token = wsid[:-1]
    user = utility.getUserByToken(token)
    company = user.userCompanyId
    if wsid[-1] == constants.C:
        supplier = Supplier()
        supplier.supplierCode = utilitySD.oTtradersCodeGenerator(companyName, constants.Supplier)
        supplierDetailSave(supplier, company.companyName, company.country_id,
                           company.address_Line1,company.address_Line2,company.unit1,
                           company.unit2,company.state_id,company.postalCode,user.firstName+' '+user.lastName,
                           user.email,user.countryCode_id,user.contactNo,1,user.email
                           ,user.email)
        supplierShipping = SupplierShippingAddress()
        supplierShipping.shippingSupplier = supplier
        supplierShippingAddressSave(supplierShipping, supplier.supAddress_Line1, supplier.supAddress_Line2,
                                    supplier.supUnit1, supplier.supUnit2, supplier.supCountry_id,
                                    supplier.supState_id, supplier.supPostalCode)
    else:
        customer = Customer()
        customer.customerCode = utilitySD.oTtradersCodeGenerator(companyName, constants.Customer)
        customerDetailSave(customer, company.companyName, company.country_id,
                           company.address_Line1, company.address_Line2, company.unit1,
                           company.unit2, company.state_id,company.postalCode,
                           user.firstName+' '+user.lastName, user.email, user.countryCode_id, user.contactNo, 1,
                           user.email,user.email)
        customerShipping = CustomerShippingAddress()
        customerShipping.shippingCustomer = customer
        customerShippingAddressSave(customerShipping, customer.cusAddress_Line1, customer.cusAddress_Line2,
                                    customer.cusUnit1, customer.cusUnit2, customer.cusCountry_id,
                                    customer.cusState_id, customer.cusPostalCode)


"""Customer/ Supplier save by CSV uploding. Check all the user defined valdations for Customer/ Supplier adding 
functionalities, If invitation is requested by the current user then the invitation link sent to the Customer/ Supplier
 via Email to join the system"""
def customerOrSupplierCsvSave(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        resultSet = []
        resultAlreadyExistSet = []
        resultSuccessfulSet = []
        type = request.POST['type'].lower()
        try:
            if 'user' in request.session:
                currentUser = utility.getObjectFromSession(request, 'user')
                userCompany = currentUser.userCompanyId
                email = currentUser.email
                check = True
            else:
                currentUser = utility.getObjectFromSession(request, 'subUser')
                userCompany = utility.getCompanyBySchemaName(connection.schema_name)
                email = utility.getUserByCompanyId(userCompany).email
                if type == constants.Customer:
                    check = utility.checkRequesURLisPresentForSubUser(currentUser, "customerSave")
                else:
                    check = utility.checkRequesURLisPresentForSubUser(currentUser, "supplierSave")
            # get the csv file
            inputCsv = request.FILES.get('myfile', False)
            # read the csv file as IextIO and make the text as object using DictReader
            listCsv = list(csv.DictReader(io.TextIOWrapper(inputCsv)))
            # takes an object and produces a string
            dumps = json.dumps(listCsv)
            # would take a file-like object, read the data from that object, and use that string to create an object
            usersFromCsv = json.loads(dumps)
            # get the type of the trader

            userCompanyName = userCompany.companyName
            # check the csv file has data
            account = utility.getoTAccountByCompany(userCompany)
            if not account.planSuspended:
                if check:
                    if len(usersFromCsv) > 0:
                        if type == constants.Customer:
                            modelName = "Customer"
                        else:
                            modelName = "Supplier"
                        customerCount = utilitySD.getCountOftheModelByModelName(modelName)
                        if utility.checkEntryCountBasedOnPlanAndFeatures(userCompany,
                                                                         modelName,
                                                                         customerCount+len(usersFromCsv)):
                            # get the individual customer/supplier from the csv
                            for customerOrsupplier in usersFromCsv:
                                a = {}
                                b = {}

                                # check the manadatory fields are present in the csv
                                try:
                                    emailId = customerOrsupplier['EMAIL'].lower()
                                    contactNumber = customerOrsupplier['CONTACT_NUMBER']
                                    country = customerOrsupplier['COUNTRY']
                                    state = customerOrsupplier['STATE']
                                    usradd_country = customerOrsupplier['SHIPPING_COUNTRY']
                                    usradd_state = customerOrsupplier['SHIPPING_STATE']
                                    companyName = customerOrsupplier['COMPANY_NAME']
                                    a["currentData"] = {'email':emailId,'country':country,'state':state,
                                                        'contactNo':contactNumber,
                                                        'companyName':companyName}
                                # mandatory fields are not present it will show the error messsage
                                except:
                                    return JsonResponse(
                                        {'status': 'showerror',
                                         'error_msg': 'Please upload the csv with proper headers/mandotary fields'})

                                # check the fields validations
                                valiadtions = csvFieldValidation(emailId, contactNumber, country, state, usradd_country,
                                                                 usradd_state,customerOrsupplier['POSTAL_CODE'],
                                                                 customerOrsupplier['SHIPPING_POSTAL_CODE'],
                                                                 b,customerOrsupplier['ALTERNATE_EMAIL'].lower(),
                                                                 customerOrsupplier['COMMUNICATION_EMAIL'].lower())
                                # check entered and user email are same
                                if email != emailId:
                                    if valiadtions is True:
                                        # check customer/supplier is already exists in our system
                                        trader = alreadyExistCustomerOrSupplier(emailId,contactNumber,companyName,type)
                                        if trader[0] is None and trader[1] is None:
                                            # email check using fuzzy logic
                                            userList = views.fuzzyEmail(emailId, "csv")
                                            if not userList:
                                                # contact number check using fuzzy logic
                                                contactFuzzy = views.fuzzyContactNumber(contactNumber)
                                                if contactFuzzy:
                                                    userList += contactFuzzy
                                            if not userList:
                                                # company name check using fuzzy logic
                                                temp = views.fuzzyCompanyName(companyName, country, state,
                                                                        customerOrsupplier['POSTAL_CODE'],
                                                                        customerOrsupplier['UNIT1'],
                                                                              customerOrsupplier['UNIT2'],
                                                                        customerOrsupplier['ADDRESS1'],
                                                                        customerOrsupplier['ADDRESS2'], "csv")
                                                if temp[0]:
                                                    userList += (temp[0])
                                                if not userList and temp[1]:
                                                    userList += (temp[1])
                                            # show rhe matched data for the entered cutomer/supplier from the system
                                            if userList:
                                                b["matchedData"] = list(userList)
                                                a.update(b)
                                                resultSet.append(a)
                                            else:
                                                try:
                                                    user_Country = Country.objects.get(countryName__iexact=
                                                                                       usradd_country)
                                                except:
                                                    user_Country = ''
                                                try:
                                                    user_State = State.objects.get(stateName__iexact=usradd_state)
                                                except:
                                                    user_State = user_Country
                                                if type==constants.Customer:
                                                    customer= Customer()
                                                    customer.customerCode = utilitySD.oTtradersCodeGenerator(
                                                        userCompanyName,constants.Customer)
                                                    customerDetailSave(customer,companyName,
                                                                       Country.objects.get(countryName__iexact=
                                                                                           country).countryId,
                                                                       customerOrsupplier['ADDRESS1'],
                                                                       customerOrsupplier['ADDRESS2'],
                                                                       customerOrsupplier['UNIT1'],
                                                                       customerOrsupplier['UNIT2'],
                                                                       State.objects.get(stateName__iexact=
                                                                                         state).stateId,
                                                                       customerOrsupplier['POSTAL_CODE'],
                                                                       customerOrsupplier['CONTACT_PERSON'],
                                                                       emailId,
                                                                       CountryCode.objects.get(countryCodeType=
                                                                                customerOrsupplier['COUNTRY_CODE'].
                                                                                    replace('+', '')).countryCodeId,
                                                                       contactNumber,0,
                                                                       customerOrsupplier['ALTERNATE_EMAIL'].lower(),
                                                                       customerOrsupplier['COMMUNICATION_EMAIL'].
                                                                       lower())

                                                    if user_Country != '' and user_State != '':
                                                        customerAddress = CustomerShippingAddress()
                                                        customerAddress.shippingCustomer = customer
                                                        customerShippingAddressSave(customerAddress,
                                                                            customerOrsupplier['SHIPPING_ADDRESS1'],
                                                                            customerOrsupplier['SHIPPING_ADDRESS2'],
                                                                            customerOrsupplier['SHIPPING_UNIT1'],
                                                                            customerOrsupplier['SHIPPING_UNIT2'],
                                                                            user_Country.countryId,
                                                                            user_State.stateId,
                                                                            customerOrsupplier['SHIPPING_POSTAL_CODE'])
                                                else:
                                                    supplier = Supplier()
                                                    supplier.supplierCode = utilitySD.oTtradersCodeGenerator(
                                                        userCompanyName,constants.Supplier)
                                                    supplierDetailSave(supplier, companyName,
                                                                       Country.objects.get(countryName__iexact=
                                                                                           country).countryId,
                                                                       customerOrsupplier['ADDRESS1'],
                                                                       customerOrsupplier['ADDRESS2'],
                                                                       customerOrsupplier['UNIT1'],
                                                                       customerOrsupplier['UNIT2'],
                                                                       State.objects.get(stateName__iexact=
                                                                                         state).stateId,
                                                                       customerOrsupplier['POSTAL_CODE'],
                                                                       customerOrsupplier['CONTACT_PERSON'],
                                                                       emailId,
                                                                       CountryCode.objects.get(countryCodeType=
                                                                                customerOrsupplier['COUNTRY_CODE'].
                                                                                replace('+','')).countryCodeId,
                                                                       contactNumber, 0,
                                                                       customerOrsupplier['ALTERNATE_EMAIL'].lower(),
                                                                       customerOrsupplier['COMMUNICATION_EMAIL'].
                                                                       lower())

                                                    if user_Country != '' and user_State != '':
                                                        supplierAddress = SupplierShippingAddress()
                                                        supplierAddress.shippingSupplier = supplier
                                                        supplierShippingAddressSave(supplierAddress,
                                                                            customerOrsupplier['SHIPPING_ADDRESS1'],
                                                                            customerOrsupplier['SHIPPING_ADDRESS2'],
                                                                            customerOrsupplier['SHIPPING_UNIT1'],
                                                                            customerOrsupplier['SHIPPING_UNIT2'],
                                                                            user_Country.countryId,
                                                                            user_State.stateId,
                                                                            customerOrsupplier['SHIPPING_POSTAL_CODE'])
                                                b["error"] = 'The below ' + type + ' is added successfully'
                                                a.update(b)
                                                resultSuccessfulSet.append(a)
                                        elif trader[1] is not None:
                                            b["error"] = 'This ' + type + '  is activated again in OT'
                                            a.update(b)
                                            resultAlreadyExistSet.append(a)
                                        # customer/supplier already exists in to tne system
                                        else:
                                            b["error"] = 'The below ' + type + ' already exist in your system'
                                            a.update(b)
                                            resultAlreadyExistSet.append(a)
                                    # field validations fails
                                    else:
                                        a.update(valiadtions)
                                        resultAlreadyExistSet.append(a)
                                # entered and user email are same
                                else:
                                    b["error"] = 'Oops! You cannot add yourself as a ' + type
                                    a.update(b)
                                    resultAlreadyExistSet.append(a)
                            # matched data or validation failure data present then it will show the data details
                            if resultSet or resultAlreadyExistSet:
                                errormessages = errormessage(type, resultSet,
                                                             resultAlreadyExistSet + resultSuccessfulSet, "")
                                return JsonResponse(
                                    {'status': 'error','error_msg':'matchedData','matchedDataContent': errormessages})
                            # no matched data or validation failures it will show success message
                            else:
                                return JsonResponse({'status': 'success',
                                                     'success_msg': type + '(s) were added successfully'})
                        else:
                            planFeatureCount = utility.planFeaturesCountByCompanyAndModelName(userCompany, modelName)
                            remainingCount = str(int(planFeatureCount) - int(customerCount))
                            return JsonResponse({'status': 'error',
                                                 'error_msg': "Plan has only "+ remainingCount +" left"})
                    # csv is empty
                    else:
                        return JsonResponse(
                            {'status': 'showerror', 'error_msg': 'Please upload csv with data'})
                else:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': "Your don't have access for this action"})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your plan has suspended"})
        # exception is customer or supplier save it will give the saved and matched details with error messsage
        except:
            if resultSet or resultSuccessfulSet or resultAlreadyExistSet:
                errormessages = errormessage(type, [], resultAlreadyExistSet + resultSuccessfulSet,
                                        "Some of the " + type + "(s) not added please check and update the valid csv")
                return JsonResponse(
                    {'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
            return JsonResponse(
                {'status': 'showerror', 'error_msg': 'Please upload valid csv'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method used to add existing customer/supplier in to the current system.If connection is requested by the current 
user then the connection link sent to the Customer/ Supplier via Email and Notification to join the system"""
@csrf_exempt
def addExistingCustomerOrSupplier(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        # get the email from the session
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            mainUser = currentUser
            email = currentUser.email
            check = True
        else:
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            currentUser = utility.getObjectFromSession(request, 'subUser')
            mainUser = utility.getUserByCompanyId(userCompany)
            email = mainUser.email
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                userCompanyName = userCompany.companyName
                emailId = request.POST['email'].lower()
                # get the type of the trader
                type = request.POST['type'].lower()
                if type == constants.Customer:
                    modelName = "Customer"
                else:
                    modelName = "Supplier"
                customerCount = utilitySD.getCountOftheModelByModelName(modelName)
                if utility.checkEntryCountBasedOnPlanAndFeatures(userCompany,modelName,customerCount ):
                    status = request.POST['status']
                    traderUser = utility.getUserByEmail(emailId)
                    traderCompany = traderUser.userCompanyId
                    # check the customer or supplier already exists in the system
                    trader = alreadyExistCustomerOrSupplier(emailId,traderUser.contactNo,traderCompany.companyName,type)
                    invitationStatus = 1
                    mailSent = False
                    if status == "2":
                        invitationStatus = 2
                        mailSent = True
                    # check entered and user email are same
                    if email != emailId:
                        if trader[0] is None :
                            wsid = uuid.uuid4().hex
                            if type== constants.Customer:
                                customer = Customer()
                                if trader[1]:
                                    customer = trader[1]
                                    customerAddress = CustomerShippingAddress.objects.get(shippingCustomer = customer)
                                else:
                                    customerAddress = CustomerShippingAddress()
                                customer.customerCode = utilitySD.oTtradersCodeGenerator(userCompanyName,
                                                                                         constants.Customer)
                                customer.connectionCode = wsid
                                customerDetailSave(customer, traderCompany.companyName, traderCompany.country_id,
                                                   traderCompany.address_Line1, traderCompany.address_Line2,
                                                   traderCompany.unit1,
                                                   traderCompany.unit2,traderCompany.state_id,traderCompany.postalCode,
                                                   traderUser.firstName + ' ' + traderUser.lastName,
                                                   traderUser.email,
                                                   traderUser.countryCode_id, traderUser.contactNo, invitationStatus,
                                                   traderUser.email,traderUser.email)
                                customerAddress.shippingCustomer = customer
                                customerShippingAddressSave(customerAddress, traderCompany.address_Line1,
                                                            traderCompany.address_Line2, traderCompany.unit1,
                                                            traderCompany.unit2, traderCompany.country_id,
                                                            traderCompany.state_id,
                                                            traderCompany.postalCode)
                                mainUrl = "/acceptSupplier"
                                trader = constants.Supplier
                            else:
                                supplier = Supplier()
                                if trader[1]:
                                    supplier = trader[1]
                                    supplierAddress = SupplierShippingAddress.objects.get(shippingSupplier = supplier)
                                else:
                                    supplierAddress = SupplierShippingAddress()
                                supplier.connectionCode = wsid
                                supplier.supplierCode = utilitySD.oTtradersCodeGenerator(userCompanyName,
                                                                                         constants.Supplier)
                                supplierDetailSave(supplier, traderCompany.companyName, traderCompany.country_id,
                                                   traderCompany.address_Line1, traderCompany.address_Line2,
                                                   traderCompany.unit1,traderCompany.unit2, traderCompany.state_id,
                                                   traderCompany.postalCode,
                                                   traderUser.firstName+' '+traderUser.lastName,
                                                   traderUser.email,traderUser.countryCode_id, traderUser.contactNo,
                                                   invitationStatus,traderUser.email,traderUser.email)
                                supplierAddress.shippingSupplier = supplier
                                supplierShippingAddressSave(supplierAddress, traderCompany.address_Line1,
                                                            traderCompany.address_Line2, traderCompany.unit1,
                                                            traderCompany.unit2, traderCompany.country_id,
                                                            traderCompany.state_id,
                                                            traderCompany.postalCode)
                                mainUrl = "/acceptCustomer"
                                trader = constants.Customer
                            # send mail to the customer/supplier
                            if mailSent:
                                currentSchema = connection.schema_name
                                connection.set_schema(schema_name=traderCompany.schemaName)
                                uid = urlsafe_base64_encode(force_bytes(mainUser.pk)).decode()
                                token = account_activation_token.make_token(mainUser)
                                url = mainUrl+"/"+uid+"/"+token+"/?wsid="+wsid
                                mainView.notificationView(trader,url,userCompanyName + " added you as a " + type,"href"
                                                          ,None,1)
                                connection.set_schema(schema_name=currentSchema)
                            return JsonResponse({'status': 'success', 'success_msg': type + ' added successfully'})
                        else:
                            # customer/supplier already exists in to tne system
                            return JsonResponse(
                                {'status': 'error', 'error_msg': 'This ' + type + ' already exist in your system'})
                    else:
                        # entered and user email are same
                        return JsonResponse(
                            {'status': 'error', 'error_msg': 'Oops! You cannot add yourself as ' + type})
                else:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': "Your purchased " + type + " limit is exceeded"})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})



"""Method is used for field validations."""
def csvFieldValidation(emailId, contactNumber, country, state, shippingCountry, shippingState,postalCode,
                       shippingpostalCode,
                       errorArray,alternateEmail,communicationEmail):
    # check email contains '@'
    emailTestOne = emailId.split('@')
    # check the length of the email
    if len(emailTestOne[0]) > 0 and len(emailTestOne) > 1 and len(emailTestOne[1].split('.')) > 0:
        # check howmany '.' present only after '@'
        emailTestTwo = emailTestOne[1].split('.')
        if len(emailTestTwo[0]) > 0 and len(emailTestTwo[1]) > 1:
            # check the contact number is numeric and length of it
            alterTestOne = alternateEmail.split('@')
            if len(alterTestOne[0]) > 0 and len(alterTestOne) > 1 and len(alterTestOne[1].split('.')) > 0:
                alterTestTwo = alterTestOne[1].split('.')
                if len(alterTestTwo[0]) > 0 and len(alterTestTwo[1]) > 1:
                    communicationTestOne = communicationEmail.split('@')
                    if len(communicationTestOne[0]) > 0 and len(communicationTestOne) > 1 and \
                            len(communicationTestOne[1].split('.')) > 0:
                        communicationTestTwo = communicationTestOne[1].split('.')
                        if len(communicationTestTwo[0]) > 0 and len(communicationTestTwo[1]) > 1:
                            if variableIsNumeric(contactNumber) is True and len(contactNumber) < 13 and \
                                    len(contactNumber) > 4:
                                # validating country / state present in the model
                                if len(postalCode) <= 7 and len(postalCode)!=0:
                                    try:
                                        countryName = Country.objects.get(countryName__iexact=country)
                                    except:
                                        countryName = None
                                    if countryName is not None:
                                        try:
                                            stateName = State.objects.get(stateName__iexact=state)
                                        except:
                                            stateName = None
                                        if stateName is not None:
                                            if shippingCountry or shippingState:
                                                try:
                                                    shippingCountryName = Country.objects.get(countryName__iexact=
                                                                                              shippingCountry)
                                                except:
                                                    shippingCountryName = None
                                                if shippingCountryName is not None:
                                                    try:
                                                        shippingStateName = State.objects.get(stateName__iexact=
                                                                                              shippingState)
                                                    except:
                                                        shippingStateName = None
                                                    if shippingStateName is not None:
                                                        if len(shippingpostalCode)<=7 and len(shippingpostalCode)!=0:
                                                            return True
                                                        else:
                                                            errorArray['error']='Please enter valid shipping postalcode'
                                                            return errorArray
                                                    else:
                                                        errorArray['error'] = 'Please enter valid shipping state'
                                                        return errorArray
                                                else:
                                                    errorArray['error'] = 'Please enter valid shipping country'
                                                    return errorArray
                                            else:
                                                return True
                                        else:
                                            errorArray['error'] = 'Please enter valid State'
                                            return errorArray
                                    else:
                                        errorArray['error'] = 'Please enter valid Country'
                                        return errorArray
                                else:
                                    errorArray['error'] = 'Please enter valid Postal Code'
                                    return errorArray
                            else:
                                errorArray['error'] = 'Please enter valid Contact Number'
                                return errorArray
                    errorArray['error'] = 'Please enter valid Communication Email ID'
                    return errorArray
            errorArray['error'] = 'Please enter valid Alternate Email ID'
            return errorArray
    errorArray['error'] = 'Please enter valid Email ID'
    return errorArray


""" Method is to check whether the variable is numeric """
def variableIsNumeric(variable):
    # check the variable is an integer
    if isinstance(variable, int):
        return True
    # check only it contains digits
    elif variable.isdigit():
        return True
    return False


"""Method is to accept the requested customer. Customer request is accepted then the customer is added into 
current schema and accept notification is send to the customer."""
@csrf_exempt
def acceptRequestedCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                relId = body['relId']
                traderUser = utility.getUserByEmail(body['email'])
                traderCompany = traderUser.userCompanyId
                customerCount = utilitySD.getCountOftheModelByModelName("Customer")
                if utility.checkEntryCountBasedOnPlanAndFeatures(userCompany, "Customer", customerCount):
                    customer = utilitySD.getCustomerByEmail(body['email'])
                    if customer is None:
                        customer = Customer()
                        customerAddress = CustomerShippingAddress()
                    else:
                        customerAddress = CustomerShippingAddress.objects.get(shippingCustomer=customer)
                    customer.customerCode = utilitySD.oTtradersCodeGenerator(userCompany.companyName,constants.Customer)
                    customer.connectionCode = relId
                    customer.relationshipStatus = True
                    customer.status = constants.Active
                    noti = utilitySD.getNotificationById(body['notiId'])
                    noti.viewed = constants.Yes
                    noti.save()
                    customer.cusCompanyCode = traderCompany.companyCode
                    customerDetailSave(customer, traderCompany.companyName, traderCompany.country_id,
                                       traderCompany.address_Line1, traderCompany.address_Line2, traderCompany.unit1,
                                       traderCompany.unit2, traderCompany.state_id, traderCompany.postalCode,
                                       traderUser.firstName + ' ' + traderUser.lastName,
                                       traderUser.email,
                                       traderUser.countryCode_id, traderUser.contactNo, 2,traderUser.email,
                                       traderUser.email)
                    customerAddress.shippingCustomer = customer
                    customerShippingAddressSave(customerAddress,traderCompany.address_Line1,traderCompany.address_Line2
                                                , traderCompany.unit1, traderCompany.unit2, traderCompany.country_id,
                                                traderCompany.state_id,traderCompany.postalCode)
                    mainView.notificationView(constants.Customer, customer.customerId,
                                              "You are connected with " + str(customer.cusCompanyName),"Connected",None,1)
                    currentSchema = connection.schema_name
                    connection.set_schema(schema_name=traderCompany.schemaName)
                    supplier = utilitySD.getSupplierByConnectionCode(relId)
                    supplier.supCompanyCode = userCompany.companyCode
                    supplier.relationshipStatus = True
                    supplier.save()
                    mainView.notificationView(constants.Supplier, supplier.supplierId,
                                              "Do you allow vendor " +
                                              str(supplier.supCompanyName)+" to assign SLA for your site? ",
                                              "SiteAssign",None,1)
                    connection.set_schema(schema_name=currentSchema)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Customer added successfully',
                         'redirect_url': settings.HTTP + request.get_host() + '/dashboard'})

                else:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': "Your purchased customer limit is exceeded"})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to reject the requested customer.Customer request is rejected then the reject notification is 
send to the customer"""
@csrf_exempt
def rejectRequestedCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                relId = body['relId']
                traderUser = utility.getUserByEmail(body['email'])
                traderCompany = traderUser.userCompanyId
                currentSchema = connection.schema_name
                connection.set_schema(schema_name=traderCompany.schemaName)
                supplier = utilitySD.getSupplierByConnectionCode(relId)
                supplier.invitationStatus = 4
                supplier.save()
                mainView.notificationView(constants.Supplier, supplier.supplierId,
                                          str(supplier.supCompanyName) + " rejected your request",
                                          "Supplier", None, 1)
                connection.set_schema(schema_name=currentSchema)
                return JsonResponse(
                    {'status': 'success', 'success_msg': 'Customer rejected successfully',
                     'redirect_url': settings.HTTP + request.get_host() + '/dashboard'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to accept the requested supplier. Supplier request is accepted then the supplier is added into 
current schema and accept notification is send to the supplier."""
@csrf_exempt
def acceptRequestedSupplier(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                relId = body['relId']
                traderUser = utility.getUserByEmail(body['email'])
                traderCompany = traderUser.userCompanyId
                supplierCount = utilitySD.getCountOftheModelByModelName("Supplier")
                if utility.checkEntryCountBasedOnPlanAndFeatures(userCompany, "Supplier", supplierCount):
                    supplier = utilitySD.getSupplierByEmail(body['email'])
                    if supplier is None:
                        supplier = Supplier()
                        supplierAddress = SupplierShippingAddress()
                    else:
                        supplierAddress = SupplierShippingAddress.objects.get(shippingSupplier=supplier)
                    supplier.connectionCode = relId
                    supplier.supplierCode = utilitySD.oTtradersCodeGenerator(userCompany.companyName,constants.Supplier)
                    supplier.relationshipStatus = True
                    supplier.status = constants.Active
                    noti = utilitySD.getNotificationById(body['notiId'])
                    noti.viewed = constants.Yes
                    noti.save()
                    supplier.supCompanyCode = traderCompany.companyCode
                    supplierDetailSave(supplier, traderCompany.companyName, traderCompany.country_id,
                                       traderCompany.address_Line1, traderCompany.address_Line2, traderCompany.unit1,
                                       traderCompany.unit2, traderCompany.state_id, traderCompany.postalCode,
                                       traderUser.firstName + ' ' + traderUser.lastName,
                                       traderUser.email,
                                       traderUser.countryCode_id, traderUser.contactNo, 2,traderUser.email,
                                       traderUser.email)
                    supplierAddress.shippingSupplier = supplier
                    supplierShippingAddressSave(supplierAddress,traderCompany.address_Line1,traderCompany.address_Line2
                                                , traderCompany.unit1, traderCompany.unit2, traderCompany.country_id,
                                                traderCompany.state_id,
                                                traderCompany.postalCode)
                    mainView.notificationView(constants.Supplier, supplier.supplierId,
                                              "Do you allow vendor " +
                                              str(supplier.supCompanyName)+" to assign SLA for your site? ",
                                              "SiteAssign",None,1)
                    currentSchema = connection.schema_name
                    connection.set_schema(schema_name=traderCompany.schemaName)
                    customer = utilitySD.getCustomerByConnectionCode(relId)
                    customer.relationshipStatus = True
                    customer.cusCompanyCode = userCompany.companyCode
                    customer.save()
                    mainView.notificationView(constants.Customer, customer.customerId,
                                              str(customer.cusCompanyName) + " accepted your request",
                                              "CustomerAcceptRequest",None,1)
                    connection.set_schema(schema_name=currentSchema)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Vendor added successfully',
                         'redirect_url': settings.HTTP + request.get_host() + '/dashboard'})
                else:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': "Your purchased vendor limit is exceeded"})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})

    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to reject the requested supplier.Supplier request is rejected then the reject notification is 
send to the supplier"""
@csrf_exempt
def rejectRequestedSupplier(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                relId = body['relId']
                traderUser = utility.getUserByEmail(body['email'])
                traderCompany = traderUser.userCompanyId
                currentSchema = connection.schema_name
                connection.set_schema(schema_name=traderCompany.schemaName)
                customer = utilitySD.getCustomerByConnectionCode(relId)
                customer.invitationStatus = 4
                customer.save()
                mainView.notificationView(constants.Customer, customer.customerId,
                                          str(customer.cusCompanyName) + " rejected your request",
                                          "CustomerRejectRequest", None, 1)
                connection.set_schema(schema_name=currentSchema)
                return JsonResponse(
                    {'status': 'success', 'success_msg': 'Vendor rejected successfully',
                     'redirect_url': settings.HTTP + request.get_host() + '/dashboard'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


""" creating customer/supplier/product error message html.Parameter - type = Customer/Supplier/Product, 
responseData= error/main data, alreadyExistData = matched data, message=error message """
def errormessage(type, responseData, alreadyExistData, message):
    return render_to_string('errormessage.html',
                            {'type': type, 'data': responseData, 'alreadyExistData': alreadyExistData,
                             'message': message})


"""Accept Customer HTML - Page has accept/reject customer functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def acceptCustomer(request, uidb64, token):
    if ('user' in request.session or 'subUser' in request.session) and 'wsid' in request.GET:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, '/acceptCustomer')
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, '/acceptCustomer')
        account = utility.getoTAccountByCompany(company)
        if urls:
            try:
                # getting the primary key of user from the UID
                uid = force_text(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)

            except(TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None
            # getting the unviewed notifications for the user
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            # getting the length of the notification
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            if 'notificationId' in request.GET:
                notiId = request.GET.get('notificationId', '')
            else:
                notiId = "false"
            relation = False
            if user:
                customer = utilitySD.getCustomerByEmail(user.email)
                relId = request.GET.get('wsid', '')
                alert = None
                if customer:
                    relation = customer.relationshipStatus
                    alert = 'This Customer information is already present in your system.If you accept, ' \
                            'the customer details override the existing'
                    if customer.status == constants.Inactive:
                        alert = 'This Customer deactivated by your request.If you accept, this customer reactivated'
                    if customer.relationshipStatus and customer.status == constants.Active:
                        alert ='This Customer is already linked with your system'

                userForm = AcceptTraderForm(
                    initial={'email': user.email, 'contactNo': user.contactNo,
                             'countryCode': user.countryCode.countryCodeName,
                             'firstName': user.firstName, 'lastName': user.lastName,'type': "customer",'relId': relId})
                companyForm = AcceptTraderCompanyForm(
                    initial={'companyName': user.userCompanyId.companyName,
                             'country': user.userCompanyId.country.countryName,
                             'state': user.userCompanyId.state.stateName,
                             'address_Line1': user.userCompanyId.address_Line1,
                             'address_Line2': user.userCompanyId.address_Line2, 'unit1': user.userCompanyId.unit1,
                             'unit2': user.userCompanyId.unit2, 'postalCode': user.userCompanyId.postalCode})

                return render(request, 'acceptTrader.html',
                              {'company': company,'urls':list(urls), 'ProfileForm': profileForm,
                               'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                               'noti': notiFy, 'form': userForm, 'companyform': companyForm,'alert':alert,
                               'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,
                               'relationshipStatus': relation,'notificationId':notiId,'subscribedModules':subscribedModules })
            else:
                return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Accept Supplier HTML - Page has accept/reject supplier functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def acceptSupplier(request, uidb64, token):
    if ('user' in request.session or 'subUser' in request.session) and 'wsid' in request.GET:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, '/acceptSupplier')
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, '/acceptSupplier')
        relation = False
        account = utility.getoTAccountByCompany(company)
        if urls:
            try:
                # getting the primary key of user from the UID
                uid = force_text(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)

            except(TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None
            # getting the unviewed notifications for the user
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            # getting the length of the notification
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            if 'notificationId' in request.GET:
                notiId = request.GET.get('notificationId', '')
            else:
                notiId = "false"
            if user :
                supplier = utilitySD.getSupplierByEmail(user.email)
                relId = request.GET.get('wsid', '')
                alert = None
                if supplier:
                    relation = supplier.relationshipStatus
                    alert = 'This Vendor information is already present in your system.If you accept,' \
                            'vendor details will override the existing'
                    if supplier.status == constants.Inactive:
                        alert = 'This Vendor deactivated by your request.If you accept, this vendor reactivated'
                    if supplier.relationshipStatus and supplier.status == constants.Active:
                        alert = 'The Vendor already linked with your system'
                userForm = AcceptTraderForm(
                    initial={'email': user.email, 'contactNo': user.contactNo,
                             'countryCode': "+" + user.countryCode.countryCodeType,
                             'firstName': user.firstName, 'lastName': user.lastName,'type': "supplier",'relId': relId})
                companyForm = AcceptTraderCompanyForm(
                    initial={'companyName': user.userCompanyId.companyName,
                             'country': user.userCompanyId.country.countryName,
                             'state': user.userCompanyId.state.stateName,
                             'address_Line1': user.userCompanyId.address_Line1,
                             'address_Line2': user.userCompanyId.address_Line2, 'unit1': user.userCompanyId.unit1,
                             'unit2': user.userCompanyId.unit2, 'postalCode': user.userCompanyId.postalCode})
                return render(request, 'acceptTrader.html',
                              {'company': company, 'ProfileForm': profileForm,'urls':list(urls),
                               'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                               'noti': notiFy, 'form': userForm, 'companyform': companyForm, 'alert': alert,
                               'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,
                               'relationshipStatus': relation,'notificationId':notiId,'subscribedModules':subscribedModules })
            else:
                return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Method is used to save all product attributes"""
def saveproductAttribute(Attribute,color,size,design,style,other):
    Attribute.attributeColor = color
    Attribute.attributeSize = size
    Attribute.attributeDesign = design
    Attribute.attributeStyle = style
    Attribute.attributeOther = other
    Attribute.save()


"""Method is used to save all product purchasing information"""
def savepurchasingItems(Purchase,uom,tax,price,currency,priceUnit,uomforKg,text):
    Purchase.purchasingUom_id = uom
    Purchase.purchasingTax_id = tax
    Purchase.purchasingPrice = price
    Purchase.purchasingCurrency_id = currency
    Purchase.purchasingPriceUnit = priceUnit
    Purchase.purchasingUomForKg_id = uomforKg
    Purchase.purchasingOrderText = text
    Purchase.save()


"""Method is used to save all product sales information"""
def savesalesItems(Sales,uom,tax,category,price,currency,priceUnit,uomforKg,text):
    Sales.salesUom_id = uom
    Sales.salesTax_id = tax
    Sales.salesPrice = price
    Sales.salesCurrency_id = currency
    if priceUnit != '':
        Sales.salesPriceUnit = priceUnit
    if uomforKg != '':
        Sales.salesUomForKg_id = uomforKg
    Sales.salesOrderText = text
    Sales.salesCategoryGrp = category
    Sales.save()


"""Method is used to save all product Measurement information"""
def saveitemMeasurement(Measurement,dimension,dimensionUnit,length,width,height,weight,weightUnit):
    Measurement.measurementDimension = dimension
    Measurement.measurementDimensionUnit_id = dimensionUnit
    if length !='':
        Measurement.measurementLength = length
    if width != '':
        Measurement.measurementWidth = width
    if height != '':
        Measurement.measurementHeight = height
    if weight != '':
        Measurement.measurementWeight = weight
    Measurement.measurementWeightUnit_id = weightUnit
    Measurement.save()


"""Method is used to save all product Storage information"""
def saveitemStorage(Storage,shelf,case,tier,pallet,dept,rack):
    Storage.storageShelfLife = shelf
    Storage.storageCase = case
    Storage.storageTier = tier
    Storage.storagePallet = pallet
    Storage.storageDept_id = dept
    Storage.storageRack = rack
    Storage.save()


"""Method is used to save all product Parameter information"""
def saveitemParameter(Parameter,one,two,three,four):
    Parameter.alterNateParamOne = one
    Parameter.alterNateParamTwo = two
    Parameter.alterNateParamThree = three
    Parameter.alterNateParamFour = four
    Parameter.save()


"""Method is used to save all product information"""
def saveItemMaster(Product,itemCode,itemName,alterItemCode,alterItemName,brandName,itemDesc,articleType
                   ,itemCategory,merchantCategory,merchantCategory1,merchantCategory2,storageCondition
                   ,uom,unit,self,lead,productDetail):
    Product.itemCode = itemCode.replace(" ","")
    Product.itemName = itemName
    Product.alterItemCode = alterItemCode
    Product.alterItemName = alterItemName
    Product.brandName = brandName
    Product.itemDesc = itemDesc
    Product.articleType_id = articleType
    Product.itemCategory_id = itemCategory
    Product.itemMerchantCategory_id = merchantCategory
    Product.itemMerchantCategoryOne_id = merchantCategory1
    Product.itemMerchantCategoryTwo_id = merchantCategory2
    Product.itemStorageCondition_id = storageCondition
    Product.baseUom_id = uom
    Product.packingUnit = unit
    Product.selfManufacturing = self
    Product.manufacturingLeadTime = lead
    Product.productDetail = productDetail
    Product.save()


"""Method is used to delete all product sub catagory information"""
def deleteProductSubModels(product):
    productAttribute.objects.get(attributeItem=product).delete()
    purchasingItems.objects.get(purchasingItem=product).delete()
    salesItems.objects.get(salesItem=product).delete()
    itemMeasurement.objects.get(measurementItem=product).delete()
    itemStorage.objects.get(storageItem=product).delete()
    itemParameter.objects.get(parameterItem=product).delete()


"""Product save by manual form post. Check all the user defined valdations for product adding functionalities"""
def saveMasterProduct(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                if utility.checkEntryCountBasedOnPlanAndFeatures(utility.getCompanyBySchemaName(connection.schema_name),
                                                                 'ItemMaster',
                                                                 utilitySD.getCountOftheModelByModelName("ItemMaster")):
                    itemCode = request.POST['itemCode']
                    itemName = request.POST['itemName']
                    resultSet = []
                    a = {}
                    b = {}
                    key = request.POST
                    masterItemCode = utilitySD.getProductByItemCode(itemCode)
                    masterItemName = utilitySD.getProductByItemName(itemName)
                    if (not masterItemCode and not masterItemName) or (masterItemCode and
                                                                       masterItemCode.status == constants.Inactive) or \
                            (masterItemName and masterItemName.status == constants.Inactive):
                        Product = ItemMaster()
                        if masterItemCode:
                            Product = masterItemCode
                            deleteProductSubModels(Product)
                            Product.status = constants.Active
                        elif masterItemName:
                            Product = masterItemName
                            deleteProductSubModels(Product)
                            Product.status = constants.Active
                        selfManufacturing = False
                        if 'selfManufacturing' in request.POST:
                            selfManufacturing = True
                        saveItemMaster(Product, itemCode, itemName, request.POST['alterItemCode'],
                                       request.POST['alterItemName'],
                                       request.POST['brandName'], request.POST['itemDesc'], request.POST['articleType']
                                       , request.POST['itemCategory'], request.POST['itemMerchantCategory'],
                                       request.POST['itemMerchantCategoryOne'], request.POST['itemMerchantCategoryTwo'],
                                       request.POST['itemStorageCondition'], request.POST['baseUom']
                                       , request.POST['packingUnit'],selfManufacturing,
                                       request.POST['manufacturingLeadTime'],
                                       request.POST['productDetail']
                                       )
                        if request.POST['attributeColor'] or request.POST['attributeSize'] or \
                                request.POST['attributeDesign'] or request.POST['attributeStyle'] or\
                                request.POST['attributeOther']:
                            Attribute =productAttribute()
                            Attribute.attributeItem = Product
                            ProdAttributeSave(request, Attribute)
                        if request.POST['purchasingUom']:
                            Purchase = purchasingItems()
                            Purchase.purchasingItem = Product
                            savepurchasingItems(Purchase, request.POST['purchasingUom'], request.POST['purchasingTax'],
                                                request.POST['purchasingPrice'], request.POST['purchasingCurrency'],
                                                request.POST['purchasingPriceUnit'], request.POST['purchasingUomForKg'],
                                                request.POST['purchasingOrderText'])
                        if request.POST['salesUom']:
                            Sales = salesItems()
                            Sales.salesItem = Product
                            savesalesItems(Sales, request.POST['salesUom'], request.POST['salesTax'],
                                           request.POST['salesCategoryGrp'],
                                           request.POST['salesPrice'], request.POST['salesCurrency'],
                                           request.POST['salesPriceUnit'],
                                           request.POST['salesUomForKg'], request.POST['salesOrderText'])
                        if request.POST['measurementDimension'] or request.POST['measurementDimensionUnit'] or \
                                request.POST['measurementLength'] or request.POST['measurementHeight'] or \
                                request.POST['measurementWidth'] or request.POST['measurementWeight'] or \
                                request.POST['measurementWeightUnit']:
                            Measurement =itemMeasurement()
                            Measurement.measurementItem = Product
                            saveitemMeasurement(Measurement, request.POST['measurementDimension'],
                                                request.POST['measurementDimensionUnit'],
                                                request.POST['measurementLength'], request.POST['measurementWidth'],
                                                request.POST['measurementHeight'], request.POST['measurementWeight'],
                                                request.POST['measurementWeightUnit'])
                        if request.POST['storageShelfLife'] or request.POST['storageCase'] or \
                                request.POST['storageTier'] or request.POST['storagePallet'] or \
                                request.POST['storageDept'] or request.POST['storageRack'] :
                            Storage = itemStorage()
                            Storage.storageItem = Product
                            saveitemStorage(Storage, request.POST['storageShelfLife'], request.POST['storageCase'],
                                            request.POST['storageTier'], request.POST['storagePallet'],
                                            request.POST['storageDept'],
                                            request.POST['storageRack'])
                        if request.POST['alterNateParamOne'] or request.POST['alterNateParamTwo'] or \
                                request.POST['alterNateParamThree'] or request.POST['alterNateParamFour']:
                            Parameter = itemParameter()
                            Parameter.parameterItem = Product
                            saveitemParameter(Parameter, request.POST['alterNateParamOne'],
                                              request.POST['alterNateParamTwo'],
                                              request.POST['alterNateParamThree'], request.POST['alterNateParamFour'])
                        return JsonResponse({'status': 'success', 'success_msg': 'Product added successfully'})

                    else:
                        a["currentData"] = key
                        if masterItemCode:
                            b["error"] = 'This Product Code is already exist'
                        elif masterItemName:
                            b["error"] = 'This Product Name is already exist'
                        a.update(b)
                        resultSet.append(a)
                        errormessages = errormessage("product", [], resultSet, "")
                        return JsonResponse(
                            {'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Your Purchased Product Limit Is Exceeded'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is for assigning product/sale catalog to customer"""
@csrf_exempt
def assignProductForCustomer(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                type = body['type']
                primaryObject = body['primaryObject']
                currentSchema = connection.schema_name
                cusProLis = []
                if type == 'product':
                    objectList = body['data']
                    masterItem = utilitySD.getProductByItemCode(primaryObject)
                    salesDetails = utilitySD.getSalesDetailsByProduct(masterItem)
                    modifiedPrice = body['price']
                    discount = body['discount']
                    absolute = body['absolute']
                    for dictionaries in objectList:
                        singleCustomer = utilitySD.getCustomerById(dictionaries['customerId'])
                        try:
                            customerCatalog = CustomerProductCatalog.objects.get(itemCode=masterItem.itemCode,
                                                                                 customerId=singleCustomer)
                            itemSup = True
                        except:
                            customerCatalog = CustomerProductCatalog()
                            customerCatalog.customerId = singleCustomer
                            itemSup = False
                        customerCatalog.productId = masterItem
                        saveCustomerCatalog(customerCatalog, masterItem, salesDetails.salesUom,
                                            salesDetails.salesTax,
                                            salesDetails.salesCurrency,
                                            salesDetails.salesPrice,
                                            salesDetails.salesUomForKg,modifiedPrice)

                        if singleCustomer.relationshipStatus:
                            userSchema = utility.getCompanyByCompanyCode(singleCustomer.cusCompanyCode).schemaName
                            connection.set_schema(schema_name=userSchema)
                            supplier = utilitySD.getSupplierByConnectionCode(singleCustomer.connectionCode)
                            if itemSup:
                                supplierCatalog = SupplierProductCatalog.objects.get(supplierItemCode=primaryObject,
                                                                           supplierId=supplier)
                            else:
                                supplierCatalog = SupplierProductCatalog()
                                supplierCatalog.supplierId = supplier
                            desc = supplier.supCompanyName + " assigned a product to you "
                            types = constants.AssignProductForCustomer
                            mainView.notificationView(constants.Supplier, supplier.pk, desc, types, None, 1)
                            noti = Notification()
                            noti.sendFromId = supplier.pk
                            noti.sendingTrader = constants.Supplier
                            noti.desc = desc
                            noti.type = types
                            noti.href = None
                            noti.notificationSite_id = 1
                            noti.save()
                            supplierCatalog.status = constants.Pending
                            supplierCatalog.notificationId = Notification.objects.get(notificationId=noti.notificationId)
                            saveSupplierCatalog(supplierCatalog, masterItem, salesDetails.salesUom,
                                            salesDetails.salesTax,
                                            salesDetails.salesCurrency,
                                            salesDetails.salesPrice,
                                            salesDetails.salesUomForKg, modifiedPrice,True)

                            connection.set_schema(schema_name=currentSchema)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Product added successfully to the customer(s)'})
                elif type == 'catalog':
                    objectList = body['data']
                    productListSale = ProductCatalogForSaleDetails.objects.filter(productCatelogId_id=primaryObject,
                                                                                  status=constants.Active).values(
                        'salePrdtCatDetId')
                    for singleProduct in productListSale:
                        productDetail =utilitySD.getProductFromSaleProductCatelogById(singleProduct['salePrdtCatDetId'])
                        for dictionaries in objectList:
                            singleCustomer = utilitySD.getCustomerById(dictionaries['customerId'])
                            try:
                                customerCatalog = CustomerProductCatalog.objects.get(itemCode=productDetail.itemCode,
                                                                                     customerId=singleCustomer)
                                itemSup = True
                            except:
                                customerCatalog = CustomerProductCatalog()
                                customerCatalog.customerId = singleCustomer
                                itemSup = False
                            customerCatalog.discountAbsolute = productDetail.discountAbsolute
                            customerCatalog.discountPercentage = productDetail.discountPercentage
                            customerCatalog.productId = productDetail.productId
                            customerCatalog.productCatId_id = primaryObject
                            saveCustomerCatalog(customerCatalog, productDetail, productDetail.salesUom,
                                                productDetail.salesTax,
                                                productDetail.salesCurrency,
                                                productDetail.salesPrice,
                                                productDetail.salesUomForKg,productDetail.discountPrice)

                            if singleCustomer.relationshipStatus:
                                userSchema = utility.getCompanyByCompanyCode(singleCustomer.cusCompanyCode).schemaName
                                connection.set_schema(schema_name=userSchema)
                                supplier = utilitySD.getSupplierByConnectionCode(singleCustomer.connectionCode)

                                if itemSup:
                                    supplierCatalog = SupplierProductCatalog.objects.get(supplierItemCode=
                                                                                         productDetail.itemCode,
                                                                               supplierId=supplier)
                                else:
                                    supplierCatalog = SupplierProductCatalog()
                                    supplierCatalog.supplierId = supplier
                                    supplierCatalog.status = constants.Pending
                                saveSupplierCatalog(supplierCatalog, productDetail, productDetail.salesUom,
                                                productDetail.salesTax,
                                                productDetail.salesCurrency,
                                                productDetail.salesPrice,
                                                productDetail.salesUomForKg, productDetail.discountPrice,True)
                                connection.set_schema(schema_name=currentSchema)
                    for dictionaries in objectList:
                        singleCustomer = utilitySD.getCustomerById(dictionaries['customerId'])
                        if singleCustomer.relationshipStatus:
                            userSchema = utility.getCompanyByCompanyCode(singleCustomer.cusCompanyCode).schemaName
                            connection.set_schema(schema_name=userSchema)
                            desc = supplier.supCompanyName + " assigned a product to you "
                            types = constants.AssignProductForCustomer
                            mainView.notificationView(constants.Supplier,supplier.pk, desc, types,None,1)
                            connection.set_schema(schema_name=currentSchema)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Catalog added successfully to the customer(s)'})
                else:
                    objectList = body['data']
                    customer = utilitySD.getCustomerById(primaryObject)
                    statusCheck = False
                    userSchema = None
                    if customer.relationshipStatus:
                        statusCheck = True
                        userSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                        connection.set_schema(schema_name=userSchema)
                        supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                        desc = supplier.supCompanyName + " assigned products to you "
                        types = constants.AssignProductForCustomer
                        mainView.notificationView(constants.Supplier, supplier.supplierId, desc, types,None,1)
                        connection.set_schema(schema_name=currentSchema)
                    for dictionaries in objectList:
                        masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                        salesDetails = utilitySD.getSalesDetailsByProduct(masterItem)
                        try:
                            customerCatalog = CustomerProductCatalog.objects.get(
                                itemCode__iexact=dictionaries['itemCode'], customerId=customer)
                            itemSup = True
                        except:
                            customerCatalog = CustomerProductCatalog()
                            customerCatalog.customerId = customer
                            itemSup = False
                        customerCatalog.productId = masterItem
                        saveCustomerCatalog(customerCatalog, masterItem, salesDetails.salesUom,
                                            salesDetails.salesTax,
                                            salesDetails.salesCurrency,
                                            salesDetails.salesPrice,
                                            salesDetails.salesUomForKg, dictionaries['price'])
                        if statusCheck:
                            connection.set_schema(schema_name=userSchema)
                            supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                            if itemSup:
                                supplierCatalog = SupplierProductCatalog.objects.get(
                                    supplierItemCode__iexact=dictionaries['itemCode'],supplierId=supplier)
                            else:
                                supplierCatalog = SupplierProductCatalog()
                                supplierCatalog.supplierId = supplier
                            supplierCatalog.status = constants.Pending
                            saveSupplierCatalog(supplierCatalog, masterItem, salesDetails.salesUom,
                                            salesDetails.salesTax,
                                            salesDetails.salesCurrency,
                                            salesDetails.salesPrice,
                                            salesDetails.salesUomForKg, dictionaries['price'],True)
                            cusProLis.append(masterItem.itemCode)
                            connection.set_schema(schema_name=currentSchema)
                    return JsonResponse({'status': 'success',
                                         'success_msg': 'Product(s) added successfully to the customer'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Save product details into customer catalog"""
def saveCustomerCatalog(customerCatalog,masterItem,salesUom,salesTax,salesCurrency,
                        salesPrice,salesUomForKg,modifiedPrice):
    customerCatalog.itemCode = masterItem.itemCode
    customerCatalog.itemName = masterItem.itemName
    customerCatalog.itemCategory = masterItem.itemCategory
    customerCatalog.salesUom = salesUom
    customerCatalog.salesTax = salesTax
    customerCatalog.salesCurrency = salesCurrency
    customerCatalog.salesPrice = salesPrice
    customerCatalog.salesUomForKg = salesUomForKg
    customerCatalog.discountPrice = modifiedPrice
    customerCatalog.status = constants.Active
    customerCatalog.save()


"""Save product details into supplier catalog"""
def saveSupplierCatalog(supplierCatalog,masterItem,purchaseUom,purchaseTax,purchaseCurrency,
                        purchasePrice,purchaseUomForKg,modifiedPrice,status):
    if status:
        supplierCatalog.supplierItemCode = masterItem.itemCode
        supplierCatalog.supplierItemName = masterItem.itemName
    else:
        supplierCatalog.itemCode = masterItem.itemCode
        supplierCatalog.itemName = masterItem.itemName
    supplierCatalog.itemCategory = masterItem.itemCategory
    supplierCatalog.purchaseUom = purchaseUom
    supplierCatalog.purchaseTax = purchaseTax
    supplierCatalog.purchaseCurrency = purchaseCurrency
    supplierCatalog.purchasePrice = purchasePrice
    supplierCatalog.purchaseUomForKg = purchaseUomForKg
    supplierCatalog.discountPrice = modifiedPrice
    supplierCatalog.save()


"""Method is for assigning product/sale catalog to not interrelation suppliers"""
@csrf_exempt
def assignProductToSupplier(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                type = body['type']
                primaryObject = body['primaryObject']
                if type == 'product':
                    objectList = body['data']
                    masterItem = utilitySD.getProductByItemCode(primaryObject)
                    purchaseDetails = utilitySD.getPurchaseDetailsByProduct(masterItem)
                    modifiedPrice = body['price']
                    for dictionaries in objectList:
                        singleSupplier = utilitySD.getSupplierById(dictionaries['supplierId'])
                        try:
                            defaultSupplier = SupplierProductCatalog.objects.get(productId=masterItem,
                                                                                 defaultSupplier=True)
                        except:
                            defaultSupplier = None
                        try:
                            supplierCatalog = SupplierProductCatalog.objects.get(itemCode__iexact=masterItem.itemCode,
                                                                                 supplierId=singleSupplier)
                            supplierCatalog.status = constants.Active
                            supplierCatalog.linked = False
                        except:
                            supplierCatalog = SupplierProductCatalog()
                            supplierCatalog.supplierId = singleSupplier
                        if defaultSupplier is None:
                            supplierCatalog.defaultSupplier = True
                            supplierCatalog.productId = masterItem
                            saveSupplierCatalog(supplierCatalog, masterItem, purchaseDetails.purchasingUom,
                                                purchaseDetails.purchasingTax,
                                                purchaseDetails.purchasingCurrency,
                                                purchaseDetails.purchasingPrice,
                                                purchaseDetails.purchasingUomForKg,
                                                modifiedPrice,False)
                        else:
                            supplierCatalog.productId = masterItem
                            saveSupplierCatalog(supplierCatalog, masterItem, purchaseDetails.purchasingUom,
                                                purchaseDetails.purchasingTax,
                                                purchaseDetails.purchasingCurrency,
                                                purchaseDetails.purchasingPrice,
                                                purchaseDetails.purchasingUomForKg,
                                                modifiedPrice, False)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Product added successfully to the vendor(s)'})
                elif type == 'catalog':
                    objectList = body['data']
                    productListSale = ProductCatalogForPurchaseDetails.objects.filter(productCatelogId_id=primaryObject,
                                                                                  status=constants.Active).values(
                        'purPrdtCatDetId')
                    for singleProduct in productListSale:
                        productDetail = utilitySD.getProductFromPurchaseProductCatelogById(
                            singleProduct['purPrdtCatDetId'])
                        for dictionaries in objectList:
                            singleSupplier = utilitySD.getSupplierById(dictionaries['supplierId'])
                            try:
                                defaultSupplier = SupplierProductCatalog.objects.get(productId=productDetail.productId,
                                                                                     defaultSupplier=True)
                            except:
                                defaultSupplier = None
                            try:
                                supplierCatalog = SupplierProductCatalog.objects.get(
                                    itemCode__iexact=productDetail.itemCode,supplierId=singleSupplier)
                            except:
                                supplierCatalog = SupplierProductCatalog()
                                supplierCatalog.supplierId = singleSupplier
                            if defaultSupplier is None:
                                supplierCatalog.defaultSupplier = True
                                supplierCatalog.productId = productDetail.productId
                                supplierCatalog.productCatId_id = primaryObject
                                saveSupplierCatalog(supplierCatalog, productDetail, productDetail.purchaseUom,
                                                    productDetail.purchaseTax,
                                                    productDetail.purchaseCurrency,
                                                    productDetail.purchasePrice,
                                                    productDetail.purchaseUomForKg,
                                                    productDetail.purchasePrice,False)
                            else:
                                supplierCatalog.productId = productDetail.productId
                                supplierCatalog.productCatId_id = primaryObject
                                saveSupplierCatalog(supplierCatalog, productDetail, productDetail.purchaseUom,
                                                    productDetail.purchaseTax,
                                                    productDetail.purchaseCurrency,
                                                    productDetail.purchasePrice,
                                                    productDetail.purchaseUomForKg,
                                                    productDetail.purchasePrice, False)
                    return JsonResponse({'status': 'success',
                                         'success_msg': 'Catalog added successfully to the vendor'})
                else:
                    objectList = body['data']
                    supplier = utilitySD.getSupplierById(primaryObject)
                    for dictionaries in objectList:
                        masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                        purchaseDetails = utilitySD.getPurchaseDetailsByProduct(masterItem)
                        try:
                            defaultSupplier = SupplierProductCatalog.objects.get(productId=masterItem,
                                                                                 defaultSupplier=True)
                        except:
                            defaultSupplier = None
                        try:
                            supplierCatalog = SupplierProductCatalog.objects.get(
                                itemCode__iexact=dictionaries['itemCode'], supplierId=supplier)
                        except:
                            supplierCatalog = SupplierProductCatalog()
                            supplierCatalog.supplierId = supplier
                        if defaultSupplier is None:
                            supplierCatalog.defaultSupplier = True
                            saveSupplierCatalog(supplierCatalog, masterItem, purchaseDetails.purchasingUom,
                                                purchaseDetails.purchasingTax,
                                                purchaseDetails.purchasingCurrency,
                                                purchaseDetails.purchasingPrice,
                                                purchaseDetails.purchasingUomForKg,
                                                dictionaries['price'],False)
                        else:
                            supplierCatalog.productId = masterItem
                            setAsDefault = False
                            if dictionaries['setAsDefault'] == "True":
                                setAsDefault = True
                            supplierCatalog.defaultSupplier = setAsDefault
                            saveSupplierCatalog(supplierCatalog, masterItem, purchaseDetails.purchasingUom,
                                                purchaseDetails.purchasingTax,
                                                purchaseDetails.purchasingCurrency,
                                                purchaseDetails.purchasingPrice,
                                                purchaseDetails.purchasingUomForKg,
                                                dictionaries['price'], False)
                    return JsonResponse({'status': 'success',
                                         'success_msg': 'Product(s) added successfully to the vendor'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Save cutomer/supplier HTML - page has adding cutomer/supplier with or without connection request functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def saveTradersById(request):
    if ('user' in request.session or 'subUser' in request.session) and 'type' in request.GET and 'code' in request.GET:
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
            companyTrader = utility.getCompanyByCompanyCode(request.GET.get('code'))
            if companyTrader and companyTrader.companyId != company.companyId:
                userTrder = utility.getUserByCompanyId(companyTrader.companyId)
                companyFormAccept = AcceptTraderCompanyForm(
                initial={'companyName': companyTrader.companyName, 'country': companyTrader.country.countryName,
                         'state': companyTrader.state.stateName, 'address_Line1': companyTrader.address_Line1,
                         'address_Line2': companyTrader.address_Line2, 'unit1': companyTrader.unit1,
                         'unit2': companyTrader.unit2, 'postalCode': companyTrader.postalCode})
                userFormAccept = AcceptTraderForm(
                initial={'email': userTrder.email, 'contactNo': userTrder.contactNo,
                         'countryCode': userTrder.countryCode.countryCodeName,
                         'firstName': userTrder.firstName,'lastName': userTrder.lastName,
                         'type': request.GET.get('type')})
                return render(request, 'addTraderById.html',
                              {'company': company,'urls':list(urls),'ProfileForm': profileForm,
                               'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                               'noti': notiFy, 'companyFormAccept': companyFormAccept, 'userFormAccept': userFormAccept,
                               'leng': lengTh, 'user': currentUser, 'status': company.urlchanged,'subscribedModules':subscribedModules })
            else:
                return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Method is for view all supplier informations and also particular supplier information by passing supplierId"""
@csrf_exempt
def viewSupplier(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        a = request.body.decode('utf-8')
        body = json.loads(a)
        if 'supplierId' in body:
            supplierId = body['supplierId']
            detailList = SupplierShippingAddress.objects.filter(shippingSupplier_id=supplierId).values(
                "supShipAddress_Line1","supShipAddress_Line2","supShipUnit1","supShipUnit2","supShipCountry_id",
                "supShipState_id","supShipPostalCode","shippingSupplier__supplierId","shippingSupplier__supCompanyName",
                "shippingSupplier__supCompanyCode","shippingSupplier__supEmail",
                "shippingSupplier__supCountryCode_id","shippingSupplier__supContactNo",
                "shippingSupplier__supCountry_id","shippingSupplier__supState_id",
                "shippingSupplier__supAddress_Line1","shippingSupplier__supAddress_Line2","shippingSupplier__supUnit1",
                "shippingSupplier__supUnit2","shippingSupplier_id","shippingSupplier__supPostalCode",
                "shippingSupplier__supplierCode","shippingSupplier__supAlterNateEmail",
                "shippingSupplier__supCommunicationEmail","shippingSupplier__contactPerson"
            )
        else:
            detailList = Supplier.objects.filter(status=constants.Active).values("supCompanyName", "supContactNo",
                                                                                 "supplierCode",
                                                                                 "supCountryCode__countryCodeType",
                                                                                 "supEmail",
                                                                                 "supplierId", "invitationStatus",
                                                                                 "relationshipStatus")
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No Vendors found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is for view all customer informations and also particular customer information by passing customerId"""
@csrf_exempt
def viewCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        if 'customerId' in body:
            customerId = body['customerId']
            detailList = CustomerShippingAddress.objects.filter(shippingCustomer_id=customerId).values(
                "cusShipAddress_Line1", "cusShipAddress_Line2", "cusShipUnit1", "cusShipUnit2",
                "cusShipCountry_id",
                "cusShipState_id", "cusShipPostalCode", "shippingCustomer__customerId",
                "shippingCustomer__cusCompanyName",
                "shippingCustomer__cusCompanyCode", "shippingCustomer__cusEmail",
                "shippingCustomer__cusCountryCode_id", "shippingCustomer__cusContactNo",
                "shippingCustomer__cusCountry_id","shippingCustomer__customerCode",
                "shippingCustomer__cusAddress_Line1", "shippingCustomer__cusAddress_Line2",
                "shippingCustomer__cusUnit1",
                "shippingCustomer__cusUnit2", "shippingCustomer__cusState_id",
                "shippingCustomer__cusPostalCode",
                 "shippingCustomer__cusAlterNateEmail",
                "shippingCustomer__cusCommunicationEmail", "shippingCustomer__contactPerson"
            )
        else:
            detailList = Customer.objects.filter(status=constants.Active).values("cusCompanyName","cusContactNo","customerCode",
                                                                             "cusCountryCode__countryCodeType","cusEmail",
                                                                             "customerId","invitationStatus",
                                                                             "relationshipStatus")
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No Customers found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is for view all product informations"""
@csrf_exempt
def viewProduct(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        detailList = ItemMaster.objects.filter(status=constants.Active).values('itemCode','itemName'
                                                                               ,'brandName','articleType__articleName',
                                                                               'baseUom__quantityTypeCode')
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No Products found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get customer catalog product details.By passing category and subcategory method return the list of 
items based on the request"""
@csrf_exempt
def listOfItemsCustomer(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        a = request.body.decode('utf-8')
        body = json.loads(a)
        category = body['type']
        if 'sup' in body:
            subCategory = body['sup']
        else:
            subCategory = None
        # category = customer,subCategory = customerId
        if category == 'customer' and subCategory:
            excludeItems = CustomerProductCatalog.objects.filter(customerId_id=subCategory,
                                                                 status=constants.Active).values('itemCode')
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),
                                                 status=constants.Active).exclude(itemCode__in=excludeItems).values(
                                                                         'itemCode', 'itemName', 'itemCategory',
                                                                         'itemCategory__prtCatName',
                                                                         'salesItem__salesPrice',
                                                                         'salesItem__salesCurrency__currencyTypeCode',
                                                                         'baseUom__quantityTypeCode')
            item['totalItem'] = list(itemList)
            customerList = Customer.objects.filter(status=constants.Active).values('customerId',
                                                                                   'cusCompanyName'
                                                                                   )
            item["totalCategory"] = list(customerList)
        # category = product,subCategory = itemCode
        elif category == 'product' and subCategory:
            itemList = ItemMaster.objects.get(~Q(productDetail=constants.Purchase),itemCode__iexact=subCategory,
                                              status=constants.Active)
            excludeCustomers = CustomerProductCatalog.objects.filter(itemCode__iexact=subCategory,
                                                                     status=constants.Active).values('customerId')
            customerList = Customer.objects.filter(status=constants.Active).exclude(
                customerId__in=excludeCustomers).values('customerId', 'customerCode','cusCountryCode__countryCodeType',
                                                   'cusCompanyName',
                                                   'cusContactNo',
                                                   'cusCountry__countryName',
                                                   'cusState__stateName',
                                                   'cusEmail',
                                                   )
            salesItemCustomer = salesItems.objects.get(salesItem=itemList)
            item["price"] = salesItemCustomer.salesPrice
            item["priceUnit"] = str(salesItemCustomer.salesCurrency.currencyTypeCode)
            item['totalItem'] = list(customerList)
        # category = catalog,subCategory = sale catalog id
        elif category == 'catalog' and subCategory:
            excludeCustomers = CustomerProductCatalog.objects.filter(productCatId_id=subCategory,
                                                                     status=constants.Active).values(
                'customerId')
            customerList = Customer.objects.filter(status=constants.Active).exclude(
                customerId__in=excludeCustomers).values('customerId', 'customerCode',
                                                        'cusCompanyName',
                                                        'cusContactNo',
                                                        'cusCountry__countryName',
                                                        'cusState__stateName',
                                                        'cusEmail',
                                                        'cusCountryCode__countryCodeType',
                                                        )
            item['totalItem'] = list(customerList)
        elif category == 'customer':
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),status=constants.Active).values(
                                                                        'itemCode', 'itemName', 'itemCategory',
                                                                         'itemCategory__prtCatName',
                                                                         'salesItem__salesPrice',
                                                                         'salesItem__salesCurrency__currencyTypeCode',
                                                                         'baseUom__quantityTypeCode')
            item['totalItem'] = list(itemList)
            customerList = Customer.objects.filter(status=constants.Active).values('customerId',
                                                                                   'cusCompanyName'
                                                                                   )
            item["totalCategory"] = list(customerList)
        elif category == 'catalog':
            itemList=ProductCatalogForSale.objects.filter(status=constants.Active).values('salePrdtCatId','catalogName')
            customerList = Customer.objects.filter(status=constants.Active).values('customerId', 'cusEmail',
                                                                                   'cusCompanyName',
                                                                                   'cusContactNo',
                                                                                   'cusCountry__countryName',
                                                                                   'cusState__stateName',
                                                                                   'cusCountryCode__countryCodeType',
                                                                                   )
            item["totalCategory"] = list(itemList)
            item['totalItem'] = list(customerList)
        else:
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),status=constants.Active).values(
                            'itemName', 'itemCode')
            customerList = Customer.objects.filter(status=constants.Active).values('customerId',"cusEmail",
                                                                                   'cusCompanyName',
                                                                                   'cusContactNo',
                                                                                   'cusCountry__countryName',
                                                                                   'cusState__stateName',
                                                                                   'cusCountryCode__countryCodeType',
                                                                                   )
            item["totalCategory"] = list(itemList)
            item['totalItem'] = list(customerList)
        if item:
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No products found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get supplier catalog product details.By passing category and subcategory method return the list of 
items based on the request"""
@csrf_exempt
def listOfItemsSupplier(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        a = request.body.decode('utf-8')
        body = json.loads(a)
        category = body['type']
        if 'sup' in body:
            subCategory = body['sup']
        else:
            subCategory = None
        # category = supplier,subCategory = supplierId
        if category == 'supplier' and subCategory:
            excludeItems = SupplierProductCatalog.objects.filter(supplierId_id=subCategory,
                                                                 status=constants.Active).values('itemCode')
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Sale),status=constants.Active).exclude(
                itemCode__in=excludeItems).values('itemCode', 'itemName', 'itemCategory__prtCatName',
                                                                                 'purchasingItem__purchasingPrice',
                                                                                 'baseUom__quantityTypeCode')
            # itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),status=constants.Active).exclude(
            #     itemCode__in=excludeItems).values('itemCode', 'itemName', 'itemCategory__prtCatName',
            #                                                                     'purchasingItem__purchasingPrice',
            #                                                                     'baseUom__quantityTypeCode')
            item['totalItem'] = list(itemList)
            supplierList = Supplier.objects.filter(status=constants.Active,relationshipStatus=False).values('supplierId',
                                                                                   'supCompanyName'
                                                                                   )
            item["totalCategory"] = list(supplierList)
        # category = product,subCategory = itemCode
        elif category == 'product' and subCategory:
            itemList = ItemMaster.objects.get(~Q(productDetail=constants.Sale),itemCode__iexact=subCategory,
                                              status=constants.Active)
            excludeCustomers = SupplierProductCatalog.objects.filter(itemCode__iexact=subCategory,
                                                                     status=constants.Active).values('supplierId')
            supplierList = Supplier.objects.filter(status=constants.Active,relationshipStatus=False).exclude(
                supplierId__in=excludeCustomers).values('supplierId', 'supplierCode',
                                                   'supCompanyName',
                                                   'supContactNo',
                                                   'supCountry__countryName',
                                                   'supState__stateName',
                                                   'supEmail','supCountryCode'
                                                   )
            purchasingItemCustomer = purchasingItems.objects.get(purchasingItem=itemList)
            item["price"] = purchasingItemCustomer.purchasingPriceUnit
            item["priceUnit"] = str(purchasingItemCustomer.purchasingCurrency.currencyTypeCode)
            item['totalItem'] = list(supplierList)
        # category = catalog,subCategory = purchase catalog id
        elif category == 'catalog' and subCategory:
            excludeCustomers = SupplierProductCatalog.objects.filter(productCatId_id=subCategory,
                                                                     status=constants.Active).values(
                'supplierId')
            supplierList = Supplier.objects.filter(status=constants.Active,relationshipStatus=False).exclude(
                supplierId__in=excludeCustomers).values('supplierId', 'supplierCode',
                                                        'supCompanyName',
                                                        'supContactNo',
                                                        'supCountry__countryName',
                                                        'supState__stateName',
                                                        'supEmail','supCountryCode'
                                                        )
            item['totalItem'] = list(supplierList)
        elif category == 'supplier':
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Sale),status=constants.Active).values(
                'itemCode', 'itemName', 'itemCategory__prtCatName',
                                                                                 'purchasingItem__purchasingPrice',
                                                                                 'baseUom__quantityTypeCode')
            item['totalItem'] = list(itemList)
            supplierList = Supplier.objects.filter(status=constants.Active,relationshipStatus=False).values('supplierId',
                                                                                   'supCompanyName'
                                                                                   )
            item["totalCategory"] = list(supplierList)
        elif category == 'catalog':
            itemList = ProductCatalogForPurchase.objects.filter(status=constants.Active).values('purPrdtCatId',
                                                                                            'catalogName')
            supplierList = Supplier.objects.filter(status=constants.Active,relationshipStatus=False).values('supplierId', 'supplierCode',
                                                                                   'supCompanyName',
                                                                                   'supContactNo',
                                                                                   'supCountry__countryName',
                                                                                   'supState__stateName',
                                                                                   'supEmail','supCountryCode'
                                                                                   )
            item["totalCategory"] = list(itemList)
            item['totalItem'] = list(supplierList)
        else:
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Sale),status=constants.Active).values(
                'itemName', 'itemCode')
            supplierList = Supplier.objects.filter(status=constants.Active,relationshipStatus=False).values('supplierId', 'supplierCode',
                                                                                   'supCompanyName',
                                                                                   'supContactNo',
                                                                                   'supCountry__countryName',
                                                                                   'supState__stateName',
                                                                                   'supEmail','supCountryCode'
                                                                                   )
            item["totalCategory"] = list(itemList)
            item['totalItem'] = list(supplierList)
        if item:
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No products found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""list the products for user for place order.method return the list of items based on the selected categories"""
@csrf_exempt
def listOfItemsSupplierOrCustomer(request):
   if 'user' in request.session or 'subUser' in request.session:
       filterBy = None
       item = {}
       itemList = []
       totalItems = []
       a = request.body.decode('utf-8')
       body = json.loads(a)
       type = body['type']
       if 'cat' in body:
           category = body['cat']
           supplier = body['sup']
       else:
           category = []
           supplier = []

       if (len(category) == 0 and len(supplier) == 0):
           # view the assigned products from the supplier
           if type == 'customer':
               itemListDefault = SupplierProductCatalog.objects.filter(~Q(supplierId__status=constants.Inactive),
                                                          ~Q(status=constants.Inactive),defaultSupplier=True).values(
                           'itemCode', 'itemName', 'itemCategory','itemCategory__prtCatName','supplierId__supCompanyName',
                   price=F('discountPrice'),
                           relId_id=F('supplierId'), priceUnit__type=F(
                               'purchaseCurrency__currencyTypeCode'), uOm__type=F('purchaseUom__quantityTypeCode'),
                           id=F('supplierCatId'))
               for items in itemListDefault:
                   subItems = {}
                   defaultList = items
                   subItems['itemSup'] = list(
                       SupplierProductCatalog.objects.filter(~Q(supplierId__status=constants.Inactive),
                                                             ~Q(status=constants.Inactive),~Q(supplierId_id=items['relId_id']),
                                                             itemCode=items['itemCode']).values
                       ('supplierId','supplierId__supCompanyName'))
                   defaultList.update(subItems)
                   itemList.append(defaultList)
               totalCategory = productCategory.objects.all().values('prtCatName', 'prtCatId')
               item["totalCategory"] = list(totalCategory)
               totalSupplier = Supplier.objects.filter(status=constants.Active).values(relId=F('supplierId'),
                                                                                       trdersId__companyName=
                                                                                       F('supCompanyName')
                                                                                       )
               item["totalSupplier"] = list(totalSupplier)

           else:
               itemList = ItemMaster.objects.all().values('itemName')
               customerList = Customer.objects.filter(status=constants.Active).values('relId',
                                                                                      'trdersId__companyName'
                                                                                      )
               item["totalCustomer"] = list(customerList)
       else:
           if type == 'customer':
               if 'single' in body:
                   itemList = SupplierProductCatalog.objects.filter( Q(supplierId__in=supplier),
                                                                     status=constants.Active).values(
                       'itemCode',
                       'itemName',
                       'itemCategory',
                       'itemCategory__prtCatName',
                       'supplierId__supCompanyName',
                       price=F('discountPrice'),
                       relId_id=F('supplierId'),
                       id=F(
                           'supplierCatId'),
                       priceUnit__type=F(
                           'purchaseCurrency__currencyTypeCode'),
                       uOm__type=F(
                           'purchaseUom__quantityTypeCode'))

                   currentSupplier= Supplier.objects.filter(pk=supplier).values(
                                                                   relId=F('supplierId'),
                                                                   trdersId__companyName=
                                                                   F('supCompanyName')
                                                                   )
                   item["totalSupplier"] = list(currentSupplier)
                   totalCategory = productCategory.objects.all().values('prtCatName', 'prtCatId')
                   item["totalCategory"] = list(totalCategory)

               elif category and supplier:
                   itemList = SupplierProductCatalog.objects.filter(
                       Q(itemCategory__in=category) & Q(supplierId__in=supplier), status=constants.Active).values(
                       'itemCode',
                       'itemName',
                       'itemCategory',
                       'itemCategory__prtCatName',
                       'supplierId__supCompanyName',
                        price=F('discountPrice'),
                       relId_id=F('supplierId'),
                       id=F(
                           'supplierCatId'),
                       priceUnit__type=F(
                           'purchaseCurrency__currencyTypeCode'),
                       uOm__type=F(
                           'purchaseUom__quantityTypeCode'))
               elif category:
                   itemList = SupplierProductCatalog.objects.filter(Q(itemCategory__in=category),
                                                              status=constants.Active,defaultSupplier=True).values(
                       'itemCode',
                       'itemName',
                       'itemCategory',
                       'itemCategory__prtCatName',
                       'supplierId__supCompanyName',
                        price=F('discountPrice'),
                       relId_id=F('supplierId'),
                       id=F(
                           'supplierCatId'),
                       priceUnit__type=F(
                           'purchaseCurrency__currencyTypeCode'),
                       uOm__type=F(
                           'purchaseUom__quantityTypeCode'))
               else:
                   itemList = SupplierProductCatalog.objects.filter(Q(supplierId__in=supplier),
                                                                    status=constants.Active).values(
                       'itemCode',
                       'itemName', 'itemCategory',
                       'itemCategory__prtCatName',
                       'supplierId__supCompanyName',
                       price=F('discountPrice'),
                       relId_id=F('supplierId'),
                       id=F(
                           'supplierCatId'),
                       priceUnit__type=F(
                           'purchaseCurrency__currencyTypeCode'),
                       uOm__type=F(
                           'purchaseUom__quantityTypeCode'))
           else:
               if filterBy == constants.Customer:
                   itemList = ItemMaster.objects.all().values()
               else:
                   customerList = Customer.objects.filter(status=constants.Active)
                   item["totalCustomer"] = list(customerList)

       if itemList:
           item["totalItem"] = list(itemList)
           totalItems.append(item)
           return JsonResponse(
               {'status': 'success', 'totalItems': totalItems})
       else:
           return JsonResponse(
               {'status': 'error', 'error_msg': 'No products found'})
   # user not in the session it will redirect to login page
   return JsonResponse(
       {'status': 'error', 'error_msg': 'sessionexpired',
        'redirect_url': settings.HTTP + request.get_host() + '/login'})

"""Method is for access removing functionalities,Parameter itemtable = Supplier/Customer/Catalog model"""
def accessRemoving(itemtable):
    itemtable.delete()
    #itemtable.status = constants.Inactive
    #itemtable.linked = False
    #itemtable.save()


"""Multiple items status changed to inactive"""
def itemRemoving(itemtable):
    for item in itemtable:
        item.status = constants.Inactive
        item.save()


"""Method is used to remove the customer and sent the notification to respective customer"""
@csrf_exempt
def removeCustomer(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                mail = body['email']
                customer = utilitySD.getCustomerByEmail(mail)
                ordCount = OrderPlacementfromCustomer.objects.filter(customerId=customer)
                ordStatus = OrderPlacementfromCustomer.objects.filter(customerId=customer,
                                                                      ordstatus=constants.Pending).values()
                if ordCount.count() == 0 or ordStatus:
                    itemforCus = CustomerProductCatalog.objects.filter(customerId=customer)
                    itemRemoving(itemforCus)
                    siteDetails = CustomerSiteDetails.objects.filter(userCustSitesCompany=customer)
                    itemRemoving(siteDetails)
                    customer.cusCommunicationEmail = customer.cusEmail
                    customer.cusEmail = None
                    if customer.relationshipStatus:
                        currentSchema = userCompany.schemaName
                        userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                        connection.set_schema(schema_name=userCustomerSchema)
                        supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                        supplier.relationshipStatus = False
                        supplier.invitationStatus = 1
                        supplier.connectionCode = None
                        supplier.save()
                        desc = userCompany.companyName + " deleted from their Customer list"
                        mainView.notificationView(constants.Supplier, supplier.supplierId, desc, "DeleteCustomer",None,1)
                        connection.set_schema(schema_name=currentSchema)
                    customer.relationshipStatus = False
                    accessRemoving(customer)
                    return JsonResponse({'status': 'success', 'success_msg': 'Customer removed successfully'})
                else:
                    return JsonResponse({'status': 'success', 'success_msg': 'Cannot remove this customer'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to remove the supplier and sent the notification to respective supplier"""
@csrf_exempt
def removeSupplier(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                mail = body['email']
                supplier = utilitySD.getSupplierByEmail(mail)
                ordCount = OrderPlacementtoSupplier.objects.filter(productId__supplierId=supplier)
                ordStatus = OrderPlacementtoSupplier.objects.filter(productId__supplierId=supplier,
                                                                      ordstatus=constants.Pending).values()
                if ordCount.count() == 0 or ordStatus:
                    itemfromSup = SupplierProductCatalog.objects.filter(supplierId=supplier)
                    itemRemoving(itemfromSup)
                    siteDetails = SupplierSlaForSites.objects.filter(userSupSitesCompany=supplier)
                    itemRemoving(siteDetails)
                    supplier.supAlterNateEmail = supplier.supEmail
                    supplier.supEmail = None
                    if supplier.relationshipStatus:
                        currentSchema = userCompany.schemaName
                        userCustomerSchema = utility.getCompanyByCompanyCode(supplier.supCompanyCode).schemaName
                        connection.set_schema(schema_name=userCustomerSchema)
                        customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                        customer.relationshipStatus = False
                        customer.invitationStatus = 1
                        customer.connectionCode = None
                        customer.save()
                        desc = userCompany.companyName + " deleted from their Vendor list"
                        mainView.notificationView(constants.Customer,  customer.customerId,desc, "DeleteVendor",None,1)
                        connection.set_schema(schema_name=currentSchema)
                    supplier.relationshipStatus = False
                    accessRemoving(supplier)
                    return JsonResponse({'status': 'success', 'success_msg': 'Vendor removed successfully'})
                else:
                    return JsonResponse({'status': 'success', 'success_msg': 'Cannot remove this vendor'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to remove the product from both end if the users are connected and sent the notification to 
assigned customers"""
@csrf_exempt
def removeProduct(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                itemCode = body['itemCode']
                prod = OrderDetails.objects.filter(itemCode=itemCode, ordstatus=constants.Pending).values(
                    'itemName')
                ordCount = OrderDetails.objects.filter(itemCode=itemCode)
                itemProdrelid = CustomerProductCatalog.objects.filter(itemCode=itemCode).values('customerId','itemName')
                currentSchema = userCompany.schemaName
                if ordCount.count() == 0 or prod:
                    itemMstr = utilitySD.getProductByItemCode(itemCode)
                    itemMstr.status = constants.Inactive
                    itemMstr.itemCode = None
                    itemMstr.itemName = None
                    itemMstr.save()
                    try:
                        assignProductsaleDetailsRemove = ProductCatalogForSaleDetails.objects.filter(
                            itemCode=itemCode)
                        itemRemoving(assignProductsaleDetailsRemove)
                    except:
                        pass
                    try:
                        assignProductPurchaseDetailsRemove = ProductCatalogForPurchaseDetails.objects.filter(
                            itemCode=itemCode)
                        itemRemoving(assignProductPurchaseDetailsRemove)
                    except:
                        pass
                    for singleCustomerId in itemProdrelid:
                        AssignProduct = CustomerProductCatalog.objects.get(itemName=singleCustomerId['itemName'],customerId=singleCustomerId['customerId'])
                        AssignProduct.status = constants.Inactive
                        AssignProduct.save()
                        customerId = singleCustomerId["customerId"]
                        customer = utilitySD.getCustomerById(customerId)
                        if customer.relationshipStatus:
                            userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                            connection.set_schema(schema_name=userCustomerSchema)
                            itemfromsup = SupplierProductCatalog.objects.get(supplierItemCode=itemCode)
                            itemfromsup.defaultSupplier = False
                            accessRemoving(itemfromsup)
                            desc = str(itemfromsup.supplierId.supCompanyName) \
                                   + " removed this product "+ str(itemfromsup.itemName)
                            types = constants.RemoveCustomerOrSupplierOrProduct
                            mainView.notificationView(constants.Customer,customer.customerId, desc, types,None,1)
                            connection.set_schema(schema_name=currentSchema)
                    return JsonResponse({'status': 'success', 'success_msg': 'Product removed successfully'})
                else:
                    return JsonResponse({'status': 'success', 'success_msg': 'Cannot remove this product'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get customer/supplier products informations and also get the own product information 
by passing the itemcode"""
@csrf_exempt
def viewCustomerOrSupplierProducts(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        category = body['type']
        item = {}
        unit = {}
        currency = {}
        totalItems = []
        totalUnits = []
        totalcurrency = []
        detailList = []
        unitList = []
        currencyList = []
        if category == constants.Customer:
            relId = body['relId']
            detailList = CustomerProductCatalog.objects.filter(customerId=relId,status=constants.Active).values(
                 'itemCode',
                 'itemName','discountPercentage',
                 'discountAbsolute',
                 'salesUom__quantityTypeCode','salesPrice',
                        'salesCurrency__currencyTypeCode','discountPrice',
                        'linked')
        elif category == constants.Supplier:
            relId = body['relId']
            detailList = SupplierProductCatalog.objects.filter(supplierId=relId,status=constants.Active).values(
                 'itemCode',
                 'itemName',
                 'discountPrice',
                 'purchaseUom__quantityTypeCode','purchasePrice',
                        'purchaseCurrency__currencyTypeCode','discountPrice',
                        'linked')
        elif category == constants.Product:
            itemCode = body['itemCode']
            detailList = ItemMaster.objects.filter(itemCode=itemCode, status=constants.Active).values(
                'itemCode','itemName','alterItemCode','alterItemName','alterItemName','brandName','itemDesc',
                'articleType__articleId','itemCategory','itemMerchantCategory','itemMerchantCategoryOne',
                'itemMerchantCategoryTwo','itemStorageCondition','baseUom','packingUnit','selfManufacturing',
                'manufacturingLeadTime','productDetail','attributeItem__attributeColor',
                'attributeItem__attributeDesign','attributeItem__attributeStyle','attributeItem__attributeOther',
                'attributeItem__attributeSize','purchasingItem__purchasingUom','purchasingItem__purchasingTax',
                'purchasingItem__purchasingPrice','purchasingItem__purchasingCurrency',
                'purchasingItem__purchasingCurrency','purchasingItem__purchasingPriceUnit',
                'purchasingItem__purchasingUomForKg','purchasingItem__purchasingOrderText','salesItem__salesUom',
                'salesItem__salesTax','salesItem__salesCategoryGrp','salesItem__salesPrice','salesItem__salesCurrency',
                'salesItem__salesPriceUnit','salesItem__salesUomForKg','salesItem__salesOrderText',
                'measurementItem__measurementDimension','measurementItem__measurementDimensionUnit',
                'measurementItem__measurementLength','measurementItem__measurementWidth',
                'measurementItem__measurementHeight','measurementItem__measurementWeight',
                'measurementItem__measurementWeightUnit','storageItem__storageShelfLife','storageItem__storageCase',
                'storageItem__storageTier','storageItem__storagePallet','storageItem__storageDept',
                'storageItem__storageRack','parameterItem__alterNateParamOne','parameterItem__alterNateParamTwo',
                'parameterItem__alterNateParamThree','parameterItem__alterNateParamFour')

        if detailList:
            item['totalItem'] = list(detailList)
            unit['totalUnit'] = list(unitList)
            currency['totalCurrency'] = list(currencyList)
            totalItems.append(item)
            totalUnits.append(unit)
            totalcurrency.append(currency)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems, 'totalUnits': totalUnits,
                 'totalcurrency': totalcurrency})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No products found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Particular item is removed for the customer by passing customerId and itemCode."""
@csrf_exempt
def itemRemoveForCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                customerId = body['relId']
                itmCode = body['itemCode']
                ordCount = OrderPlacementfromCustomer.objects.filter(orderdetail__itemCode=itmCode,
                                                                     customerId=customerId)
                ordStatus = OrderPlacementfromCustomer.objects.filter(orderdetail__itemCode=itmCode,
                                                                      customerId=customerId,
                                                                      ordstatus=constants.Pending).values()
                customer = utilitySD.getCustomerById(customerId)
                if ordCount.count() == 0 or ordStatus:
                    itemforcus = CustomerProductCatalog.objects.get(itemCode__iexact=itmCode, customerId=customer,
                                                                    status=constants.Active)
                    accessRemoving(itemforcus)
                    currentSchema = connection.schema_name
                    if customer.relationshipStatus:
                        userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                        connection.set_schema(schema_name=userCustomerSchema)
                        supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                        itemfromSup = SupplierProductCatalog.objects.get(supplierItemCode__iexact=itmCode,
                                                                         supplierId=supplier)
                        itemfromSup.defaultSupplier = False
                        accessRemoving(itemfromSup)
                        defaultProduct = SupplierProductCatalog.objects.filter(itemCode__iexact=itemfromSup.itemCode,
                                                              status=constants.Active).order_by('supplierCatId').values(
                            'supplierCatId'
                        )
                        for oneSupplier in defaultProduct:
                            SupplierProductCatalog.objects.filter(supplierCatId=oneSupplier['supplierCatId']).update(
                                defaultSupplier=True)
                            break
                        desc = str(supplier.supCompanyName)+" vendor removed the access of "+str(itemfromSup.supplierItemName)
                        types = constants.ItemRemoveForCustomer
                        mainView.notificationView(constants.Customer,customer.customerId, desc, types,None,1)
                        connection.set_schema(schema_name=currentSchema)
                    return JsonResponse({'status': 'success', 'success_msg': 'Product removed successfully'})
                elif customer.relationshipStatus:
                    currentSchema = connection.schema_name
                    userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                    connection.set_schema(schema_name=userCustomerSchema)
                    supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                    itemfromSup = SupplierProductCatalog.objects.get(supplierItemCode=itmCode, supplierId=supplier)
                    desc = itemfromSup.itemName + " want to delete their supplier"
                    types = constants.ItemRemoveForCustomer
                    mainView.notificationView(constants.Customer,customer.customerId, desc, types,None,1)
                    connection.set_schema(schema_name=currentSchema)
                    return JsonResponse({'status': 'success',
                                         'success_msg': 'Notification for delete product sent successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get all the supplier list from the current schema"""
def getSupplier(request):
    if 'user' in request.session or 'subUser' in request.session:
        item = {}
        totalItems = []
        detailList = Supplier.objects.filter(status=constants.Active).values(
            'supCompanyName','connectionCode','supplierId')
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No Vendors found'})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Product save by Excel uploding. Check all the user defined valdations for product adding functionalities """
# product adding method using csv
def saveMasterProductUsingCsv(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        resultSet = []
        resultSuccessfulSet = []
        try:
            if 'user' in request.session:
                currentUser = utility.getObjectFromSession(request, 'user')
                userCompany = currentUser.userCompanyId
                check = True
            else:
                currentUser = utility.getObjectFromSession(request, 'subUser')
                userCompany = utility.getCompanyBySchemaName(connection.schema_name)
                check = utility.checkRequesURLisPresentForSubUser(currentUser, "saveMasterProduct")
            account = utility.getoTAccountByCompany(userCompany)
            if not account.planSuspended:
                if check:
                    # get the email from the session
                    inputCsv = request.FILES.get('myfile', False)
                    book = xlrd.open_workbook(file_contents=inputCsv.read())
                    # takes an object and produces a string
                    sheet = book.sheet_by_name('Main Product Table 1')
                    keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]
                    dict_list = []
                    for row_index in range(1, sheet.nrows):
                        d = {}
                        if sheet.cell(row_index, 0).value == 0.0 or sheet.cell(row_index, 0).value == '':
                            break
                        else:
                            for col_index in range(sheet.ncols):
                                if sheet.cell(row_index, col_index).value != 0.0:
                                    d.update({keys[col_index]:sheet.cell(row_index, col_index).value})
                                else:
                                    d.update({keys[col_index]:''})
                        dict_list.append(d)
                    type = request.POST['type'].lower()
                    if len(dict_list) > 0:
                        productCount = utilitySD.getCountOftheModelByModelName("ItemMaster")
                        if utility.checkEntryCountBasedOnPlanAndFeatures(userCompany,'ItemMaster',
                                                                         productCount+len(dict_list)):
                            # get individual products from csv
                            for singleProduct in dict_list:
                                a = {}
                                b = {}
                                try:
                                    itemCode = singleProduct['PRODUCT_CODE'].replace(" ","")
                                    itemName = singleProduct['PRODUCT_NAME']
                                    brandName = singleProduct['BRAND_NAME']
                                    prodDesc = singleProduct['PRODUCT_DESCRIPTION']
                                    articleType = singleProduct['ARTICLE_TYPE']
                                    prodCategory = singleProduct['PRODUCT_CATEGORY']
                                    storageCondition = singleProduct['STORAGE_CONDITIONS']
                                    baseUom = singleProduct['BASE_UOM']
                                    orderUnitPur = singleProduct['ORDER_UNIT_PURCHASE']
                                    taxCodePur = singleProduct['TAX_CODE_PURCHASE']
                                    purchasePrice = singleProduct['PURCHASE_PRICE']
                                    currencyKeyPur = singleProduct['CURRENCY_KEY_PURCHASE']
                                    priceUnitPur = singleProduct['PRICE_UNIT_PURCHASE']
                                    priceUnitKgPur = singleProduct['PURCHASE_ORDER_UNIT_KG']
                                    purchaseText = singleProduct['PURCHASE_ORDER_TEXT']
                                    salesUnitSale = singleProduct['SALES_UNIT_SALES']
                                    texCodeSale = singleProduct['TAX_CODE_SALES']
                                    sellingPriceSale = singleProduct['SELLING_PRICE_SALES']
                                    currencyKeySale = singleProduct['CURRENCY_KEY_SALES']
                                    productFor = singleProduct['PRODUCT_FOR']
                                    a["currentData"] = {'itemCode': itemCode, 'itemName': itemName}
                                # mandatory fields are not present it will show the error messsage
                                except:
                                    return JsonResponse(
                                        {'status': 'showerror',
                                         'error_msg': 'Please upload the xlsx with proper headers/mandatory fields'})

                                masterItemCode = utilitySD.getProductByItemCode(itemCode)
                                masterItemName = utilitySD.getProductByItemName(itemName)
                                # product code or name already exists in the system it will the error message
                                if (not masterItemCode and not masterItemName) or (
                                        masterItemCode and masterItemCode.status == constants.Inactive) \
                                        or (masterItemName and masterItemName.status == constants.Inactive):
                                    Product = ItemMaster()
                                    if masterItemCode:
                                        Product = masterItemCode
                                        deleteProductSubModels(Product)
                                        Product.status = constants.Active
                                    elif masterItemName:
                                        Product = masterItemName
                                        deleteProductSubModels(Product)
                                        Product.status = constants.Active
                                    selfManufacturing = False
                                    try:
                                        if 'SELF_MANUFACTURING_PRODUCT' in singleProduct \
                                                and singleProduct['SELF_MANUFACTURING_PRODUCT'].lower() == "yes":
                                            selfManufacturing = True
                                    except:
                                        selfManufacturing = False
                                    itemMerchantCategory = None
                                    itemMerchantCategoryOne = None
                                    itemMerchantCategoryTwo = None
                                    if singleProduct['MERCHANDISE_CATEGORY'] != '' and \
                                            singleProduct['MERCHANDISE_CATEGORY'] != 0.0:
                                        itemMerchantCategory = singleProduct['MERCHANDISE_CATEGORY']
                                    if singleProduct['MERCHANDISE_SUB_CATEGORY_L1'] != '' \
                                            and singleProduct['MERCHANDISE_SUB_CATEGORY_L1'] != 0.0:
                                        itemMerchantCategoryOne = singleProduct['MERCHANDISE_SUB_CATEGORY_L1']
                                    if singleProduct['MERCHANDISE_SUB_CATEGORY_L2'] != '' \
                                            and singleProduct['MERCHANDISE_SUB_CATEGORY_L2'] != 0.0:
                                        itemMerchantCategoryTwo = singleProduct['MERCHANDISE_SUB_CATEGORY_L2']
                                    validations = csvFieldValidationProduct(articleType, prodCategory,
                                                                            itemMerchantCategory,
                                                              itemMerchantCategoryOne, itemMerchantCategoryTwo,
                                                              storageCondition, baseUom, b)
                                    testPrdctFor = True
                                    if validations is True:
                                        if productFor.lower() == constants.Purchase.lower():
                                            productFor = constants.Purchase
                                            validationProduct = csvFieldValidationProductPurchase(orderUnitPur,
                                                                                                  taxCodePur,
                                                                                                  currencyKeyPur,
                                                                                                  purchasePrice,
                                                                                                  priceUnitKgPur,
                                                                                                  priceUnitPur, b)
                                            validationSale = True
                                        elif productFor.lower() == constants.Sale.lower():
                                            productFor = constants.Sale
                                            validationProduct = True
                                            validationSale = csvFieldValidationProductSale(salesUnitSale, texCodeSale,
                                                                                   sellingPriceSale,
                                                                                   currencyKeySale,
                                                                                   singleProduct['PRICE_UNIT_SALES'],
                                                                                   singleProduct[
                                                                                       'SELLING_PRICE_UNIT_SALES'], b)
                                        elif productFor.lower() == constants.Both.lower():
                                            productFor = constants.Both
                                            validationProduct = csvFieldValidationProductPurchase(orderUnitPur,
                                                                                                  taxCodePur,
                                                                                                  currencyKeyPur,
                                                                                                  purchasePrice,
                                                                                                  priceUnitKgPur,
                                                                                                  priceUnitPur, b)
                                            validationSale = csvFieldValidationProductSale(salesUnitSale, texCodeSale,
                                                                                   sellingPriceSale,
                                                                                   currencyKeySale,
                                                                                   singleProduct['PRICE_UNIT_SALES'],
                                                                                   singleProduct[
                                                                                       'SELLING_PRICE_UNIT_SALES'], b)
                                        else:
                                            testPrdctFor = False
                                            validationProduct = False
                                            validationSale = False
                                        if testPrdctFor is True:
                                            if validationProduct is True:
                                                if validationSale is True:
                                                    articleType= utilitySD.getArticleTypeByName(articleType)
                                                    prodCategory = utilitySD.getProductCategoryByName(prodCategory)
                                                    merchantCat = ''
                                                    merchantCatOne = ''
                                                    merchantCatTwo = ''
                                                    if itemMerchantCategory:
                                                        merchantCat = utilitySD.getMerchantCategoryByName(
                                                            singleProduct['MERCHANDISE_CATEGORY']).pk
                                                    if itemMerchantCategoryOne:
                                                        merchantCatOne = utilitySD.getMerchantCategoryOneByName(
                                                            singleProduct['MERCHANDISE_SUB_CATEGORY_L1']).pk
                                                    if itemMerchantCategoryTwo:
                                                        merchantCatTwo = utilitySD.getMerchantCategoryTwoByName(
                                                            singleProduct['MERCHANDISE_SUB_CATEGORY_L2']).pk

                                                    saveItemMaster(Product, itemCode, itemName,
                                                                   singleProduct['ALTERNATE_PRODUCT_CODE'],
                                                                   singleProduct['ALTERNATE_PRODUCT_NAME'],
                                                                   brandName, prodDesc, articleType.pk
                                                                   , prodCategory.pk, merchantCat,
                                                                   merchantCatOne, merchantCatTwo,
                                                                   utilitySD.getStorageConditionByName(
                                                                       storageCondition).pk,
                                                                   utility.getQuantityTypeByName(baseUom).pk
                                                                   , singleProduct['PACKING_UNIT'], selfManufacturing,
                                                                   singleProduct['MANUFACTURING_LEAD_TIME'], productFor)
                                                    if singleProduct['COLOR_ATTRIBUTE'] !='' or \
                                                            singleProduct['SIZE_ATTRIBUTE']!='' or \
                                                            singleProduct['DESIGN_ATTRIBUTE']!='' or \
                                                            singleProduct['STYLE_OR_PATTERN']!='' \
                                                            or singleProduct['OTHER_ATTRIBUTE']!='':
                                                        Attribute = productAttribute()
                                                        Attribute.attributeItem = Product
                                                        saveproductAttribute(Attribute,singleProduct['COLOR_ATTRIBUTE'],
                                                                             singleProduct['SIZE_ATTRIBUTE'],
                                                                             singleProduct['DESIGN_ATTRIBUTE'],
                                                                             singleProduct['STYLE_OR_PATTERN'],
                                                                             singleProduct['OTHER_ATTRIBUTE'])
                                                    if productFor != constants.Sale:
                                                        Purchase = purchasingItems()
                                                        Purchase.purchasingItem = Product
                                                        savepurchasingItems(Purchase,
                                                                            utility.getQuantityTypeByName(
                                                                                orderUnitPur).pk,
                                                                            utilitySD.getTaxCodeByName(taxCodePur).pk,
                                                                            purchasePrice,
                                                                            utility.getCurrencyTypeByCode(
                                                                                currencyKeyPur).pk,
                                                                            priceUnitPur,
                                                                            utility.getQuantityTypeByName(
                                                                                priceUnitKgPur).pk,purchaseText)
                                                    if productFor != constants.Purchase:
                                                        Sales = salesItems()
                                                        Sales.salesItem = Product
                                                        saleUomKg = None
                                                        if singleProduct['SELLING_PRICE_UNIT_SALES'] != '':
                                                            saleUomKg = utility.getQuantityTypeByName(
                                                                singleProduct['SELLING_PRICE_UNIT_SALES']).pk
                                                        savesalesItems(Sales, utility.getQuantityTypeByName(
                                                                        salesUnitSale).pk,
                                                                       utilitySD.getTaxCodeByName(texCodeSale).pk,
                                                                       singleProduct['ITEM_CATEGORY_GROUP_SALES'],
                                                                       sellingPriceSale, utility.getCurrencyTypeByCode(
                                                                        currencyKeySale).pk,
                                                                       singleProduct['PRICE_UNIT_SALES'],
                                                                       saleUomKg, singleProduct['SALES_TEXT_SALES'])
                                                    if singleProduct['DIMENSION_MEASUREMENT'] != ''or \
                                                            singleProduct['DIMENSION_UNIT_MEASUREMENT'] != ''or \
                                                            singleProduct['LENGTH_MEASUREMENT'] != ''or \
                                                            singleProduct['HEIGHT_MEASUREMENT']!= '' or \
                                                            singleProduct['WIDTH_MEASUREMENT'] != ''or \
                                                            singleProduct['WEIGHT_MEASUREMENT'] != ''or singleProduct[
                                                        'WEIGHT_UNIT_MEASUREMENT'] != '':
                                                        Measurement = itemMeasurement()
                                                        Measurement.measurementItem = Product
                                                        saveitemMeasurement(Measurement,
                                                                            singleProduct['DIMENSION_MEASUREMENT'],
                                                                            singleProduct['DIMENSION_UNIT_MEASUREMENT'],
                                                                            singleProduct['LENGTH_MEASUREMENT'],
                                                                            singleProduct['WIDTH_MEASUREMENT'],
                                                                            singleProduct['HEIGHT_MEASUREMENT'],
                                                                            singleProduct['WEIGHT_MEASUREMENT'],
                                                                            singleProduct['WEIGHT_UNIT_MEASUREMENT'])
                                                    if singleProduct['SHELF_LIFE_DAYS_STORAGE'] != ''or \
                                                            singleProduct['CASE_OR_TIER_STORAGE'] != ''or \
                                                            singleProduct['TIER_OR_PALLET_STORAGE']!= '' or \
                                                            singleProduct['CASE_OR_PALLET_STORAGE'] != ''or \
                                                            singleProduct['DEPARTMENT_STORAGE']!= '' or\
                                                            singleProduct['RACK_STORAGE']!= '':
                                                        Storage = itemStorage()
                                                        Storage.storageItem = Product
                                                        saveitemStorage(Storage,
                                                                        singleProduct['SHELF_LIFE_DAYS_STORAGE'],
                                                                        singleProduct['CASE_OR_TIER_STORAGE'],
                                                                        singleProduct['TIER_OR_PALLET_STORAGE'],
                                                                        singleProduct['CASE_OR_PALLET_STORAGE'],
                                                                        singleProduct['DEPARTMENT_STORAGE'],
                                                                        singleProduct['RACK_STORAGE'])
                                                    if singleProduct['ALTERNATE_PARAMETER_ONE']!= '' or\
                                                            singleProduct['ALTERNATE_PARAMETER_TWO']!= '' or \
                                                            singleProduct['ALTERNATE_PARAMETER_THREE']!= '' or \
                                                            singleProduct['ALTERNATE_PARAMETER_FOUR']!= '':
                                                        Parameter = itemParameter()
                                                        Parameter.parameterItem = Product
                                                        saveitemParameter(Parameter,
                                                                          singleProduct['ALTERNATE_PARAMETER_ONE'],
                                                                          singleProduct['ALTERNATE_PARAMETER_TWO'],
                                                                          singleProduct['ALTERNATE_PARAMETER_THREE'],
                                                                          request.POST['ALTERNATE_PARAMETER_FOUR'])
                                                    b["error"] = 'The below product is added successfully'
                                                    a.update(b)
                                                    resultSuccessfulSet.append(a)
                                                else:
                                                    a.update(validationSale)
                                                    resultSet.append(a)
                                            else:
                                                a.update(validationProduct)
                                                resultSet.append(a)
                                        else:
                                            b["error"] = "Please enter valid Product For"
                                            a.update(b)
                                            resultSet.append(a)
                                    else:
                                        a.update(validations)
                                        resultSet.append(a)
                                else:
                                    if masterItemCode:
                                        b["error"] = 'This Product Code  already exists'
                                    elif masterItemName:
                                        b["error"] = 'This Product Name  already exists'
                                    a.update(b)
                                    resultSet.append(a)

                            # matched data or validation failure data present then it will show the data details
                            if resultSet:
                                errormessages = errormessage(type, [], resultSet + resultSuccessfulSet, "")
                                return JsonResponse(
                                    {'status': 'error', 'error_msg': 'matchedData','matchedDataContent': errormessages})
                            # no matched data or validation failures it will show success message
                            else:
                                return JsonResponse({'status': 'success',
                                                     'success_msg': 'product(s) were added successfully'})
                        else:
                            planFeatureCount = utility.planFeaturesCountByCompanyAndModelName(userCompany, "ItemMaster")
                            remainingCount = str(int(planFeatureCount) - int(productCount))
                            return JsonResponse(
                                {'status': 'error','error_msg':"Plan has only " + remainingCount + " quantities left"})
                    # csv is empty
                    else:
                        return JsonResponse(
                            {'status': 'showerror', 'error_msg': 'Please upload xlsx with data'})
                else:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': "Your don't have access for this action"})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your plan has suspended"})
        # exception is product save it will give the saved and matched details with error messsage
        except:
            if resultSet or resultSuccessfulSet:
                errormessages = errormessage("product", [], resultSet + resultSuccessfulSet,
                                    "Some of the product(s) were not added, please check and update the valid file")
                return JsonResponse(
                    {'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
            return JsonResponse(
                {'status': 'showerror', 'error_msg': 'Please upload valid file format'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used for Product Merchant Category field validations."""
def csvFieldValidationProduct(articleType, itemCategory, itemMerchantCategory, itemMerchantCategoryOne,
                              itemMerchantCategoryTwo,itemStorageCondition,baseUom,errorArray):
    articleType = utilitySD.getArticleTypeByName(articleType)
    prodCategory = utilitySD.getProductCategoryByName(itemCategory)
    merchantCat = not None
    merchantCatOne = not None
    merchantCatTwo = not None
    storageCondition = not None
    testBaseUom = not None
    if itemMerchantCategory is not None and itemMerchantCategory != '' :
        merchantCat = utilitySD.getMerchantCategoryByName(itemMerchantCategory)
    if itemMerchantCategoryOne is not None and itemMerchantCategoryOne != '':
        merchantCatOne = utilitySD.getMerchantCategoryOneByName(itemMerchantCategoryOne)
    if itemMerchantCategoryTwo is not None and itemMerchantCategoryTwo != '':
        merchantCatTwo = utilitySD.getMerchantCategoryTwoByName(itemMerchantCategoryTwo)
    if itemStorageCondition is not None and itemStorageCondition !='':
        storageCondition = utilitySD.getStorageConditionByName(itemStorageCondition)
    if baseUom is not None and baseUom != '':
        testBaseUom = utility.getQuantityTypeByName(baseUom)
    if articleType:
        if prodCategory:
            if merchantCat:
                if merchantCatOne:
                    if merchantCatTwo:
                        if storageCondition:
                            if testBaseUom:
                                return  True
                            else:
                                errorArray['error'] = 'Please enter valid Base UOM'
                                return errorArray
                        else:
                            errorArray['error'] = 'Please enter valid Storage Condition'
                            return errorArray
                    else:
                        errorArray['error'] = 'Please enter valid Merchant Category One'
                        return errorArray
                else:
                    errorArray['error'] = 'Please enter valid Merchant Category Two'
                    return errorArray
            else:
                errorArray['error'] = 'Please enter valid Merchant Category'
                return errorArray
        else:
            errorArray['error'] = 'Please enter valid Product Category'
            return errorArray
    errorArray['error'] = 'Please enter valid Article Type'
    return errorArray


"""Method is used for Product purchase field validations."""
def csvFieldValidationProductPurchase( purchasingUom, purchasingTax, purchasingCurrency, purchasingPrice,
                                      purchasingUomForKg,purchasingPriceUnit,errorArray):
    try:
        float(purchasingPrice)
        purchasingPriceTest = True
    except:
        purchasingPriceTest = None
    try:
        float(purchasingPriceUnit)
        purchasingPriceUnitTest = True
    except:
        purchasingPriceUnitTest = None
    if utility.getQuantityTypeByName(purchasingUom):
        if utilitySD.getTaxCodeByName(purchasingTax):
            if purchasingPriceTest:
                if utility.getCurrencyTypeByCode(purchasingCurrency):
                    if purchasingPriceUnitTest:
                        if utility.getQuantityTypeByName(purchasingUomForKg):
                            return  True
                        else:
                            errorArray['error'] = 'Please enter valid Purchasing Uom For Kg '
                            return errorArray
                    else:
                        errorArray['error'] = 'Please enter valid Price Unit'
                        return errorArray
                else:
                    errorArray['error'] = 'Please enter valid CurrencyType'
                    return errorArray
            else:
                errorArray['error'] = 'Please enter valid Purchasing Price'
                return errorArray
        else:
            errorArray['error'] = 'Please enter valid purchasing Tax'
            return errorArray
    errorArray['error'] = 'Please enter valid purchasing UOM'
    return errorArray


"""Method is used for Product sales field validations."""
def csvFieldValidationProductSale(salesUom,salesTax,salesPrice,salesCurrency,salesPriceUnit,salesUomForKg,errorArray):
    salesPriceUnitTest = True
    salesUomForKgTest = not None
    if salesPriceUnit is not None and salesPriceUnit !='' and salesPriceUnit != 0.0:
        try:
            float(salesPriceUnit)
            salesPriceUnitTest = True
        except:
            salesPriceUnitTest = None
    if salesUomForKg is not None and salesUomForKg != '' and salesUomForKg != 0.0:
        salesUomForKgTest = utility.getQuantityTypeByName(salesUomForKg)
    try:
        float(salesPrice)
        salesPriceTest = True
    except:
        salesPriceTest = None
    if utility.getQuantityTypeByName(salesUom):
        if utilitySD.getTaxCodeByName(salesTax):
            if salesPriceTest:
                if utility.getCurrencyTypeByCode(salesCurrency):
                    if salesPriceUnitTest:
                        if salesUomForKgTest:
                            return  True
                        else:
                            errorArray['error'] = 'Please enter sales Uom For Kg'
                            return errorArray
                    else:
                        errorArray['error'] = 'Please enter valid Sales Price Unit'
                        return errorArray
                else:
                    errorArray['error'] = 'Please enter valid Sales Currency'
                    return errorArray
            else:
                errorArray['error'] = 'Please enter valid Sales Price'
                return errorArray
        else:
            errorArray['error'] = 'Please enter valid Sales Tax'
            return errorArray
    errorArray['error'] = 'Please enter valid Sales UOM'
    return errorArray


"""Method is used to return all the sales products and also passing category method return all the sales products 
belongs to the mentioned category"""
@csrf_exempt
def productCatalogSales(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        category = body['category']
        item = {}
        totalItems = []
        if category != 'none':
            detailList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),
                                               itemCategory=category, status=constants.Active
                                               ).values('itemName','itemCode','itemCategory__prtCatName',
                                               'salesItem__salesPrice','salesItem__salesCurrency__currencyTypeCode',)
        else:
            detailList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase), status=constants.Active
                                                   ).values('itemName', 'itemCode', 'itemCategory__prtCatName',
                                                            'salesItem__salesPrice',
                                                            'salesItem__salesCurrency__currencyTypeCode', )
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No products found'})
        # user not in the session it will redirect to login page

    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to create sales catalog with list of products"""
@csrf_exempt
def saveProductCatalogSales(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                objectList = body['data']
                catalogName = body['catalogName']
                alreadyExistName = utilitySD.getSaleProductCatelogByName(catalogName)
                if alreadyExistName:
                    if alreadyExistName is None or (alreadyExistName and alreadyExistName.status != constants.Active):
                        if alreadyExistName and alreadyExistName.status != constants.Active:
                            alreadyExistName.status = constants.Active
                            alreadyExistName.save()
                            for dictionaries in objectList:
                                try:
                                    masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                                    productCatalogSaleDet = ProductCatalogForSaleDetails.objects.get(productCatelogId=alreadyExistName,itemCode=masterItem.itemCode)
                                    productCatalogSaleDet.status = constants.Active
                                    productCatalogSaleDet.save()
                                except:
                                    masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                                    salesDetails = utilitySD.getSalesDetailsByProduct(masterItem)
                                    productCatalogSaleDet = ProductCatalogForSaleDetails()
                                    productCatalogSaleDet.productCatelogId = alreadyExistName
                                    productCatalogSaleDet.productId = masterItem
                                    productCatalogSaleDet.itemCode = masterItem.itemCode
                                    productCatalogSaleDet.itemName = masterItem.itemName
                                    productCatalogSaleDet.itemCategory = masterItem.itemCategory
                                    productCatalogSaleDet.alterItemCode = masterItem.alterItemCode
                                    productCatalogSaleDet.alterItemName = masterItem.alterItemName
                                    productCatalogSaleDet.salesUom = salesDetails.salesUom
                                    productCatalogSaleDet.salesTax = salesDetails.salesTax
                                    productCatalogSaleDet.salesPrice = salesDetails.salesPrice
                                    productCatalogSaleDet.salesCurrency = salesDetails.salesCurrency
                                    productCatalogSaleDet.salesUomForKg = salesDetails.salesUomForKg
                                    productCatalogSaleDet.discountPercentage = dictionaries['discountPercentage']
                                    productCatalogSaleDet.discountAbsolute = dictionaries['discountAbsolute']
                                    productCatalogSaleDet.discountPrice = dictionaries['discountPrice']
                                    productCatalogSaleDet.save()
                        return JsonResponse({'status': 'success', 'success_msg': 'Product(s) added successlly to the sales catalog'})
                    return JsonResponse({'status': 'error', 'error_msg': 'Product Catalog Name already exists!!!.'})
                else:
                    productCatalogSale = ProductCatalogForSale()
                    productCatalogSale.catalogName = catalogName
                    productCatalogSale.save()
                    for dictionaries in objectList:
                        masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                        salesDetails = utilitySD.getSalesDetailsByProduct(masterItem)
                        productCatalogSaleDet = ProductCatalogForSaleDetails()
                        productCatalogSaleDet.productCatelogId = productCatalogSale
                        productCatalogSaleDet.productId = masterItem
                        productCatalogSaleDet.itemCode = masterItem.itemCode
                        productCatalogSaleDet.itemName = masterItem.itemName
                        productCatalogSaleDet.itemCategory = masterItem.itemCategory
                        productCatalogSaleDet.alterItemCode = masterItem.alterItemCode
                        productCatalogSaleDet.alterItemName =masterItem.alterItemName
                        productCatalogSaleDet.salesUom = salesDetails.salesUom
                        productCatalogSaleDet.salesTax = salesDetails.salesTax
                        productCatalogSaleDet.salesPrice = salesDetails.salesPrice
                        productCatalogSaleDet.salesCurrency =salesDetails.salesCurrency
                        productCatalogSaleDet.salesUomForKg =salesDetails.salesUomForKg
                        productCatalogSaleDet.discountPercentage =dictionaries['discountPercentage']
                        productCatalogSaleDet.discountAbsolute = dictionaries['discountAbsolute']
                        productCatalogSaleDet.discountPrice = dictionaries['discountPrice']
                        productCatalogSaleDet.save()
                    return JsonResponse({'status': 'success',
                                         'success_msg': 'Product(s) added successfully to the sales catalog'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to return all the purchase products and also passing category method return all the purchase products 
belongs to the mentioned category"""
@csrf_exempt
def productCatalogPurchase(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        category = body['category']
        item = {}
        totalItems = []
        if category != 'none':
            detailList = ItemMaster.objects.filter(~Q(productDetail=constants.Sale),
                                               itemCategory=category, status=constants.Active
                                               ).values('itemName', 'itemCode', 'itemCategory__prtCatName',
                                                            'purchasingItem__purchasingPrice',
                                                            'purchasingItem__purchasingCurrency__currencyTypeCode')
        else:
            detailList = ItemMaster.objects.filter(~Q(productDetail=constants.Sale),
                                                   status=constants.Active
                                                   ).values('itemName', 'itemCode', 'itemCategory__prtCatName',
                                                            'purchasingItem__purchasingPrice',
                                                            'purchasingItem__purchasingCurrency__currencyTypeCode')
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No products found'})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to create purchase catalog with list of products"""
@csrf_exempt
def saveProductCatalogPurchase(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                objectList = body['data']
                catalogName = body['catalogName']
                alreadyExistName = utilitySD.getPurchaseProductCatelogByName(catalogName)
                if alreadyExistName:
                    if alreadyExistName is None or (alreadyExistName and alreadyExistName.status != constants.Active):
                        if alreadyExistName and alreadyExistName.status != constants.Active:
                            alreadyExistName.status = constants.Active
                            alreadyExistName.save()
                            for dictionaries in objectList:
                                try:
                                    masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                                    productCatalogPurchaseDet = ProductCatalogForPurchaseDetails.objects.get(productCatelogId=alreadyExistName,itemCode=masterItem.itemCode)
                                    productCatalogPurchaseDet.status = constants.Active
                                    productCatalogPurchaseDet.save()
                                except:
                                    masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                                    purchaseDetails = utilitySD.getPurchaseDetailsByProduct(masterItem)
                                    productCatalogPurchaseDet = ProductCatalogForPurchaseDetails()
                                    productCatalogPurchaseDet.productCatelogId = productCatalogPurchase
                                    productCatalogPurchaseDet.productId = masterItem
                                    productCatalogPurchaseDet.itemCode = masterItem.itemCode
                                    productCatalogPurchaseDet.itemName = masterItem.itemName
                                    productCatalogPurchaseDet.itemCategory = masterItem.itemCategory
                                    productCatalogPurchaseDet.alterItemCode = masterItem.alterItemCode
                                    productCatalogPurchaseDet.alterItemName =masterItem.alterItemName
                                    productCatalogPurchaseDet.purchaseUom = purchaseDetails.purchasingUom
                                    productCatalogPurchaseDet.purchaseTax = purchaseDetails.purchasingTax
                                    productCatalogPurchaseDet.purchasePrice = purchaseDetails.purchasingPrice
                                    productCatalogPurchaseDet.purchaseCurrency =purchaseDetails.purchasingCurrency
                                    productCatalogPurchaseDet.purchaseUomForKg =purchaseDetails.purchasingUomForKg
                                    productCatalogPurchaseDet.save()
                        return JsonResponse({'status': 'success', 'success_msg': 'Product(s) added successlly to the product catalog'})
                    return JsonResponse({'status': 'error', 'error_msg': 'Product Catalog Name already exists!!!.'})
                else:
                    productCatalogPurchase = ProductCatalogForPurchase()
                    productCatalogPurchase.catalogName = catalogName
                    productCatalogPurchase.save()
                    for dictionaries in objectList:
                        masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                        purchaseDetails = utilitySD.getPurchaseDetailsByProduct(masterItem)
                        productCatalogPurchaseDet = ProductCatalogForPurchaseDetails()
                        productCatalogPurchaseDet.productCatelogId = productCatalogPurchase
                        productCatalogPurchaseDet.productId = masterItem
                        productCatalogPurchaseDet.itemCode = masterItem.itemCode
                        productCatalogPurchaseDet.itemName = masterItem.itemName
                        productCatalogPurchaseDet.itemCategory = masterItem.itemCategory
                        productCatalogPurchaseDet.alterItemCode = masterItem.alterItemCode
                        productCatalogPurchaseDet.alterItemName =masterItem.alterItemName
                        productCatalogPurchaseDet.purchaseUom = purchaseDetails.purchasingUom
                        productCatalogPurchaseDet.purchaseTax = purchaseDetails.purchasingTax
                        productCatalogPurchaseDet.purchasePrice = purchaseDetails.purchasingPrice
                        productCatalogPurchaseDet.purchaseCurrency =purchaseDetails.purchasingCurrency
                        productCatalogPurchaseDet.purchaseUomForKg =purchaseDetails.purchasingUomForKg
                        productCatalogPurchaseDet.save()
                    return JsonResponse({'status': 'success',
                                         'success_msg': 'Product(s) added successfully to the purchase catalog'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def updateMasterProduct(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                itemCode = request.POST['itemCode']
                selfManufacturing = False
                if 'selfManufacturing' in request.POST:
                    selfManufacturing = True
                Product = ItemMaster.objects.get(itemCode=itemCode)
                typeOfProd = ItemMaster.objects.get(itemCode=itemCode).productDetail
                try:
                    SupCatalog = SupplierProductCatalog.objects.get(productId=Product, status=constants.Active)
                except:
                    SupCatalog = None
                try:
                    CusCatalog = CustomerProductCatalog.objects.get(productId=Product, status=constants.Active)
                except:
                    CusCatalog = None
                if (SupCatalog or CusCatalog):
                    customerCatolog = utilitySD.getCustomerCatalogByProductCode(itemCode)
                    customerCatolog.salesPrice = request.POST['salesPrice']
                    customerCatolog.discountPrice = request.POST['salesPrice']
                    customerCatolog.save()
                    if typeOfProd == request.POST['productDetail'] or request.POST['productDetail'] == constants.Both:
                        UpdateProductMasterSave(request, Product, itemCode, selfManufacturing)
                        if request.POST['attributeColor'] or request.POST['attributeSize'] or \
                                request.POST['attributeDesign'] or \
                                request.POST['attributeStyle'] or request.POST['attributeOther']:
                            try:
                                Attribute =productAttribute.objects.get(attributeItem=Product)
                            except:
                                Attribute = productAttribute()
                            Attribute.attributeItem = Product
                            ProdAttributeSave(request, Attribute)
                        if request.POST['purchasingUom'] and request.POST['salesUom']:
                            try:
                                Purchase = purchasingItems.objects.get(purchasingItem=Product)
                            except:
                                Purchase = purchasingItems()
                            Purchase.purchasingItem = Product
                            PurchaseItemsSave(request, Purchase)
                            try:
                                Sales = salesItems.objects.get(salesItem=Product)
                            except:
                                Sales = salesItems()
                            Sales.salesItem = Product
                            SalesItemsSave(request, Sales)
                        elif request.POST['purchasingUom']:

                            try:
                                salesItems.objects.get(salesItem=Product).delete()
                            except:
                                pass
                            try:
                                Purchase = purchasingItems.objects.get(purchasingItem=Product)
                            except:
                                Purchase = purchasingItems()
                            Purchase.purchasingItem = Product
                            PurchaseItemsSave(request, Purchase)
                        elif request.POST['salesUom']:
                            try:
                                purchasingItems.objects.get(purchasingItem=Product).delete()
                            except:
                                pass
                            try:
                                Sales = salesItems.objects.get(salesItem=Product)
                            except:
                                Sales = salesItems()
                            Sales.salesItem = Product
                            SalesItemsSave(request, Sales)
                        if request.POST['measurementDimension'] or request.POST['measurementDimensionUnit'] or \
                                request.POST['measurementLength'] or request.POST['measurementHeight'] or \
                                request.POST['measurementWidth'] or request.POST['measurementWeight'] or \
                                request.POST['measurementWeightUnit']:
                            try:
                                  Measurement =itemMeasurement.objects.get(measurementItem=Product)
                            except:
                                Measurement = itemMeasurement()
                            Measurement.measurementItem = Product
                            ItemMeasurementSave(request, Measurement)
                        if request.POST['storageShelfLife'] or request.POST['storageCase'] or \
                                request.POST['storageTier'] or request.POST['storagePallet'] or \
                                request.POST['storageDept'] or request.POST['storageRack']:
                            try:
                                Storage = itemStorage.objects.get(storageItem=Product)
                            except:
                                Storage = itemStorage()
                            Storage.storageItem = Product
                            ItemStorageSave(request, Storage)
                        if request.POST['alterNateParamOne'] or request.POST['alterNateParamTwo'] or \
                                request.POST['alterNateParamThree'] or request.POST['alterNateParamFour']:
                            try:
                                Parameter = itemParameter.objects.get(parameterItem=Product)
                            except:
                                Parameter = itemParameter()
                            Parameter.parameterItem = Product
                            ItemParameterSave(request, Parameter)
                        currentSchema = connection.schema_name
                        Pro = CustomerProductCatalog.objects.filter(itemCode=itemCode).values('customerId')
                        customers = Customer.objects.filter(customerId__in=Pro).values('cusCompanyCode')
                        for customer in customers:
                            userSchema = utility.getCompanyByCompanyCode(customer['cusCompanyCode']).schemaName
                            connection.set_schema(schema_name=userSchema)
                            if request.POST['salesUom']:
                                supplierCatalog = utilitySD.getSupplierCatalogByProductCode(itemCode)
                                supplierCatalog.purchaseUom = QuantityType.objects.get(quantityTypeId =
                                                                                       request.POST['salesUom'])
                                supplierCatalog.purchaseTax = taxCode.objects.get(taxCodeId=request.POST['salesTax'])
                                supplierCatalog.purchaseCurrency =  CurrencyType.objects.get(currencyTypeId=
                                                                                         request.POST['salesCurrency'])
                                supplierCatalog.purchasePrice = request.POST['salesPrice']
                             #   supplierCatalog.purchaseUomForKg = QuantityType.objects.get(quantityTypeId=
                                # request.POST['salesUomForKg'])
                                supplierCatalog.discountPrice = request.POST['salesPrice']
                                supplierCatalog.save()
                        connection.set_schema(schema_name=currentSchema)
                        return JsonResponse({'status': 'success', 'success_msg': 'Product updated successfully'})
                    else:
                        return JsonResponse({'status': 'success', 'success_msg': 'Cant able to edit this product'})
                else:
                    UpdateProductMasterSave(request, Product, itemCode, selfManufacturing)
                    if request.POST['attributeColor'] or request.POST['attributeSize'] or \
                            request.POST['attributeDesign'] or \
                            request.POST['attributeStyle'] or request.POST['attributeOther']:
                        try:
                            Attribute = productAttribute.objects.get(attributeItem=Product)
                        except:
                            Attribute = productAttribute()
                        Attribute.attributeItem = Product
                        ProdAttributeSave(request, Attribute)
                    if request.POST['purchasingUom'] and request.POST['salesUom']:
                        try:
                            Purchase = purchasingItems.objects.get(purchasingItem=Product)
                        except:
                            Purchase = purchasingItems()
                        Purchase.purchasingItem = Product
                        PurchaseItemsSave(request, Purchase)
                        try:
                            Sales = salesItems.objects.get(salesItem=Product)
                        except:
                            Sales = salesItems()
                        Sales.salesItem = Product
                        SalesItemsSave(request, Sales)
                    elif request.POST['purchasingUom']:
                            try:
                                salesItems.objects.get(salesItem=Product).delete()
                            except:
                                pass
                            try:
                                Purchase = purchasingItems.objects.get(purchasingItem=Product)
                            except:
                                Purchase = purchasingItems()
                            Purchase.purchasingItem = Product
                            PurchaseItemsSave(request, Purchase)
                    elif request.POST['salesUom']:
                        try:
                            purchasingItems.objects.get(purchasingItem=Product).delete()
                        except:
                            pass
                        try:
                            Sales = salesItems.objects.get(salesItem=Product)
                        except:
                            Sales = salesItems()
                        Sales.salesItem = Product
                        SalesItemsSave(request, Sales)
                    if request.POST['measurementDimension'] or request.POST['measurementDimensionUnit'] or \
                            request.POST['measurementLength'] or request.POST['measurementHeight'] or \
                            request.POST['measurementWidth'] or request.POST['measurementWeight'] or request.POST[
                        'measurementWeightUnit']:
                        try:
                            Measurement = itemMeasurement.objects.get(measurementItem=Product)
                        except:
                            Measurement = itemMeasurement()
                        Measurement.measurementItem = Product
                        ItemMeasurementSave(request, Measurement)
                    if request.POST['storageShelfLife'] or request.POST['storageCase'] or \
                            request.POST['storageTier'] or request.POST['storagePallet'] or \
                            request.POST['storageDept'] or request.POST['storageRack']:
                        try:
                            Storage = itemStorage.objects.get(storageItem=Product)
                        except:
                            Storage = itemStorage()
                        Storage.storageItem = Product
                        ItemStorageSave(request, Storage)
                    if request.POST['alterNateParamOne'] or request.POST['alterNateParamTwo'] or \
                            request.POST['alterNateParamThree'] or request.POST['alterNateParamFour']:
                        try:
                            Parameter = itemParameter.objects.get(parameterItem=Product)
                        except:
                            Parameter = itemParameter()
                        Parameter.parameterItem = Product
                        ItemParameterSave(request, Parameter)
                    return JsonResponse({'status': 'success', 'success_msg': 'Product updated successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})

    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def UpdateProductMasterSave(request,Product,itemCode,selfManufacturing):
    saveItemMaster(Product, itemCode, request.POST['itemName'], request.POST['alterItemCode'],
                   request.POST['alterItemName'],
                   request.POST['brandName'], request.POST['itemDesc'], request.POST['articleType']
                   , request.POST['itemCategory'], request.POST['itemMerchantCategory'],
                   request.POST['itemMerchantCategoryOne'], request.POST['itemMerchantCategoryTwo'],
                   request.POST['itemStorageCondition'], request.POST['baseUom']
                   , request.POST['packingUnit'], selfManufacturing,
                   request.POST['manufacturingLeadTime'], request.POST['productDetail'])


def ProdAttributeSave(request,Attribute):
    saveproductAttribute(Attribute, request.POST['attributeColor'], request.POST['attributeSize'],
                                             request.POST['attributeDesign'], request.POST['attributeStyle'],
                                             request.POST['attributeOther'])


def PurchaseItemsSave(request,Purchase):
    savepurchasingItems(Purchase, request.POST['purchasingUom'], request.POST['purchasingTax'],
                                        request.POST['purchasingPrice'], request.POST['purchasingCurrency'],
                                        request.POST['purchasingPriceUnit'], request.POST['purchasingUomForKg'],
                                        request.POST['purchasingOrderText'])


def SalesItemsSave(request,Sales):
    savesalesItems(Sales, request.POST['salesUom'], request.POST['salesTax'], request.POST['salesCategoryGrp'],
                                       request.POST['salesPrice'], request.POST['salesCurrency'], request.POST['salesPriceUnit'],
                                       request.POST['salesUomForKg'], request.POST['salesOrderText'])


def ItemMeasurementSave(request,Measurement):
    saveitemMeasurement(Measurement, request.POST['measurementDimension'], request.POST['measurementDimensionUnit'],
                        request.POST['measurementLength'], request.POST['measurementWidth'],
                        request.POST['measurementHeight'], request.POST['measurementWeight'],
                        request.POST['measurementWeightUnit'])


def ItemStorageSave(request,Storage):
    saveitemStorage(Storage, request.POST['storageShelfLife'], request.POST['storageCase'],
                    request.POST['storageTier'], request.POST['storagePallet'], request.POST['storageDept'],
                    request.POST['storageRack'])


def ItemParameterSave(request,Parameter):
    saveitemParameter(Parameter, request.POST['alterNateParamOne'], request.POST['alterNateParamTwo'],
                      request.POST['alterNateParamThree'], request.POST['alterNateParamFour'])


@csrf_exempt
def fetchSupplierProductMerging(request):
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
            notifiCation = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            notiFy = notifiCation[:10]
            lengTh = len(notifiCation)
            subscribedModules = {}
            subscribed = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
            for sub in subscribed:
                module = Module.objects.get(moduleId=sub['modulesAccess'])
                subscribedModules[module.moduleName] = module.moduleId
            noti = utilitySD.getNotificationById(request.GET['notificationId'])
            usrId = request.GET['id']
            supplier = utilitySD.getSupplierById(usrId)
            if supplier is None or noti is None:
                return HttpResponseRedirect('/dashboard/')
            assignItems = SupplierProductCatalog.objects.filter(supplierId=supplier,
                                                                linked=False,status=constants.Pending).values()
            ownItems = ItemMaster.objects.filter(status=constants.Active).values()
            return render(request, 'supplierproductmerging.html',
                          {'assignItems': list(assignItems), 'ownItems': list(ownItems), 'company': company,
                           'user': currentUser,'urls':list(urls),'notificationId':request.GET['notificationId'],
                           'ProfileForm': ProfileForm, 'companyProfileForm': companyProfileForm,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh, 'usrId': usrId,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


@csrf_exempt
def addOrMergingOrRejectProducts(request):
    if ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                datas = body['data']
                noti = utilitySD.getNotificationById(body['notiId'])
                # noti.viewed = constants.Yes
                # noti.save()
                resultSuccessfulSet = []
                resultSet = []
                supplier = utilitySD.getSupplierById(body['supplierId'])
                currentSchema = connection.schema_name
                userCustomerSchema = utility.getCompanyByCompanyCode(supplier.supCompanyCode).schemaName
                for data in datas:
                    a = {}
                    b = {}
                    if data['type'] == "merge":
                        ownProduct = utilitySD.getProductById(data['productId'])
                        try:
                            sameProduct = SupplierProductCatalog.objects.get(productId=ownProduct,supplierId=supplier,linked=True)
                        except:
                            sameProduct = None
                        suplierProCat = SupplierProductCatalog.objects.get(supplierItemName__iexact=data['productName'],
                                                                           supplierId=supplier)
                        try:
                            suplierProCatActiveCheck = SupplierProductCatalog.objects.filter(itemName__iexact=ownProduct.itemName,
                                                                              status=constants.Active)
                        except:
                            suplierProCatActiveCheck = None

                        if not sameProduct:
                            if not suplierProCatActiveCheck:
                                suplierProCat.productId = ownProduct
                                suplierProCat.itemCode = ownProduct.itemCode
                                suplierProCat.itemName = ownProduct.itemName
                                suplierProCat.linked = True
                                suplierProCat.status = constants.Active
                                suplierProCat.defaultSupplier = True
                                suplierProCat.save()
                                connection.set_schema(schema_name=userCustomerSchema)
                                customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                                customerProCat = CustomerProductCatalog.objects.get(itemCode__iexact=data['productCode'],
                                                                            customerId=customer)
                                customerProCat.linked = True
                                customerProCat.customerItemCode = ownProduct.itemCode
                                customerProCat.customerItemName = ownProduct.itemName
                                customerProCat.save()
                                connection.set_schema(schema_name=currentSchema)
                                a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                                                    'itemName': suplierProCat.supplierItemName}
                                b["error"] = 'The below product is merged successfully'
                                a.update(b)
                                resultSuccessfulSet.append(a)
                            else:
                                setAsDefaultProduct = False
                                if data['setAsDefault'] == "True":
                                    setAsDefaultProduct = True
                                    try:
                                        changeDefault = SupplierProductCatalog.objects.get(
                                            itemName__iexact=ownProduct.itemName, defaultSupplier=True)
                                        changeDefault.defaultSupplier = False
                                        changeDefault.save()
                                    except:
                                        pass
                                suplierProCat.productId = ownProduct
                                suplierProCat.itemCode = ownProduct.itemCode
                                suplierProCat.itemName = ownProduct.itemName
                                suplierProCat.linked = True
                                suplierProCat.status = constants.Active
                                suplierProCat.defaultSupplier = setAsDefaultProduct
                                suplierProCat.save()
                                connection.set_schema(schema_name=userCustomerSchema)
                                customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                                customerProCat = CustomerProductCatalog.objects.get(
                                    itemCode__iexact=data['productCode'],
                                    customerId=customer)
                                customerProCat.linked = True
                                customerProCat.customerItemCode = ownProduct.itemCode
                                customerProCat.customerItemName = ownProduct.itemName
                                customerProCat.save()
                                connection.set_schema(schema_name=currentSchema)
                                a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                                                    'itemName': suplierProCat.supplierItemName}
                                b["error"] = 'The below product is merged successfully'
                                a.update(b)
                                resultSuccessfulSet.append(a)
                        else:
                            b["error"] = 'Your Product is already merged with '+str(sameProduct.supplierItemCode)
                            a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                                                'itemName': suplierProCat.supplierItemName}
                            a.update(b)
                            resultSet.append(a)
                    elif data['type'] == "add":
                        # suplierProCat = SupplierProductCatalog.objects.get(supplierItemCode__iexact=data['productCode'],
                        #                                                    supplierId=supplier)
                        suplierProCat = SupplierProductCatalog.objects.get(supplierItemCode__iexact=data['productCode'],
                                                                           supplierId=supplier)
                        masterItemCode = utilitySD.getProductByItemCode(data['productCode'])
                        masterItemName = utilitySD.getProductByItemName(suplierProCat.supplierItemName)
                        try:
                            defaultSupplier = SupplierProductCatalog.objects.get(productId=masterItemCode,
                                                                                 defaultSupplier=True)
                        except:
                            defaultSupplier = None
                        try:
                            suplierProCatActiveCheckbyName = SupplierProductCatalog.objects.filter(itemName__iexact=data['productName'],
                                                                              status=constants.Active)
                        except:
                            suplierProCatActiveCheckbyName = None
                        # try:
                        #     suplierProCatActiveCheckbyCode = SupplierProductCatalog.objects.filter(itemCode__iexact=data['productCode'],
                        #                                                       status=constants.Active)
                        # except:
                        #     suplierProCatActiveCheckbyCode = None
                        # +++++++ this if will used if product valid by itemcode also+++++++++
                        # if not suplierProCatActiveCheckbyName or not suplierProCatActiveCheckbyCode:
                        #     if (not masterItemCode and not masterItemName) or (
                        #             masterItemCode and masterItemCode.status == constants.Inactive) \
                        #             or (masterItemName and masterItemName.status == constants.Inactive)
                                # ++++++++++++++++++++++++++above-if-end-here+++++++++++++++++++++++++++++++
                        if not suplierProCatActiveCheckbyName:
                            if (not masterItemName) or  (masterItemName and masterItemName.status == constants.Inactive):
                                addProduct = ItemMaster()
                                # if masterItemCode:
                                #     addProduct = masterItemCode
                                #     deleteProductSubModels(addProduct)
                                #     addProduct.status = constants.Active
                                if masterItemName:
                                    addProduct = masterItemName
                                    deleteProductSubModels(addProduct)
                                    addProduct.status = constants.Active
                                setAsDefaultProduct = False
                                if data['setAsDefault'] == "True":
                                    setAsDefaultProduct = True
                                setAsViewProduct = False
                                if data['setAsView'] == "True":
                                    setAsViewProduct = True
                                addProduct.itemCode = suplierProCat.supplierItemCode
                                addProduct.itemName = suplierProCat.supplierItemName
                                addProduct.itemCategory = suplierProCat.itemCategory
                                addProduct.productDetail = constants.Purchase
                                addProduct.baseUom = suplierProCat.purchaseUom
                                addProduct.setAsDefault = setAsDefaultProduct
                                addProduct.setAsView = setAsViewProduct
                                addProduct.save()
                                purchasingItem = purchasingItems()
                                purchasingItem.purchasingItem = addProduct
                                purchasingItem.purchasingUom = suplierProCat.purchaseUom
                                purchasingItem.purchasingPrice = suplierProCat.purchasePrice
                                purchasingItem.purchasingCurrency = suplierProCat.purchaseCurrency
                                purchasingItem.purchasingTax = suplierProCat.purchaseTax
                                purchasingItem.purchasingUomForKg = suplierProCat.purchaseUomForKg
                                purchasingItem.save()
                                suplierProCat.itemCode = addProduct.itemCode
                                suplierProCat.itemName = addProduct.itemName
                                suplierProCat.productId = addProduct
                                suplierProCat.linked = True
                                suplierProCat.status = constants.Active
                                if defaultSupplier is None:
                                    suplierProCat.defaultSupplier = True
                                suplierProCat.save()
                                connection.set_schema(schema_name=userCustomerSchema)
                                customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                                customerProCat = CustomerProductCatalog.objects.get(itemCode__iexact=data['productCode'],
                                                                                    customerId=customer)
                                customerProCat.linked = True
                                customerProCat.customerItemCode = addProduct.itemCode
                                customerProCat.customerItemName = addProduct.itemName
                                customerProCat.save()
                                desc = str(customer.cusCompanyName) + " added " + str(
                                    data['productCode']) + " to assigned list"
                                mainView.notificationView(constants.Customer, customer.pk, desc, "ProductAdded", None, 1)
                                connection.set_schema(schema_name=currentSchema)
                            else:
                                # if masterItemCode:
                                #     b["error"] = 'This Product++ Code  already exists'
                                # elif masterItemName:
                                #     b["error"] = 'This Product Name  already exists'
                                # a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                                #                     'itemName': suplierProCat.supplierItemName}
                                # a.update(b)
                                # resultSet.append(a)
                                if masterItemName:
                                    b["error"] = 'This Product Name already exists'
                                # elif masterItemCode:
                                #     b["error"] = 'This Product Code already exists'
                                a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                                                    'itemName': suplierProCat.supplierItemName}
                                a.update(b)
                                resultSet.append(a)
                        else:
                            # if suplierProCatActiveCheckbyCode:
                            #     b["error"] = 'This Product Code--  already exists'
                            # elif suplierProCatActiveCheckbyName:
                            #     b["error"] = 'This Product Name  already exists'
                            # a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                            #                     'itemName': suplierProCat.supplierItemName}
                            # a.update(b)
                            # resultSet.append(a)
                            if suplierProCatActiveCheckbyName:
                                b["error"] = 'This Product Name already exists'
                            # elif suplierProCatActiveCheckbyCode:
                            #     b["error"] = 'This Product Code already exists'
                            a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                                                'itemName': suplierProCat.supplierItemName}
                            a.update(b)
                            resultSet.append(a)
                    else:
                        suplierProCat = SupplierProductCatalog.objects.get(supplierItemCode__iexact=data['productCode'],
                                                                           supplierId=supplier)
                        suplierProCat.status = constants.Reject
                        suplierProCat.save()
                        connection.set_schema(schema_name=userCustomerSchema)
                        customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                        customerProCat = CustomerProductCatalog.objects.get(itemCode__iexact=data['productCode'],
                                                                            customerId=customer)
                        customerProCat.status = constants.Reject
                        customerProCat.save()
                        desc = str(customer.cusCompanyName) + " rejected " + str(data['productCode'])+" from assigned list"
                        mainView.notificationView(constants.Customer, customer.pk, desc, "ProductRejected", None, 1)
                        connection.set_schema(schema_name=currentSchema)
                        a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                                            'itemName': suplierProCat.supplierItemName}
                        b["error"] = 'The below product is rejected successfully'
                        a.update(b)
                        resultSuccessfulSet.append(a)

                if resultSet:
                    errormessages = errormessage("product", [], resultSet + resultSuccessfulSet, "Status Report")
                    return JsonResponse(
                        {'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
                else:
                    connection.set_schema(schema_name=userCustomerSchema)
                    customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                    mainView.notificationView(constants.Customer, customer.customerId,
                                              str(customer.cusCompanyName) + " updated your catalog assignment ",
                                              "addOrMergingOrRejectProducts",None,1)
                    connection.set_schema(schema_name=currentSchema)
                    return JsonResponse({'status': 'success', 'success_msg': 'Product(s) were updated successfully'})
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
def updateProductAssigntoCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                customerId = body['cusId']
                itemCode = body['itemCode']
                customerProd = CustomerProductCatalog.objects.get(itemCode=itemCode, customerId=customerId)
                previousPrice = customerProd.discountPrice
                currency = customerProd.salesCurrency.currencyTypeCode
                customerProd.discountPercentage = body['discountPercentage']
                customerProd.discountAbsolute = body['discountAbsolute']
                customerProd.discountPrice = body['discountPrice']
                customerProd.save()
                if previousPrice != float(body['discountPrice']):
                    currentSchema = connection.schema_name
                    customer = utilitySD.getCustomerById(customerId)
                    userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                    connection.set_schema(schema_name=userCustomerSchema)
                    supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                    supplierProd = SupplierProductCatalog.objects.get(supplierItemCode=itemCode, supplierId=supplier)
                    supplierProd.discountPrice = body['discountPrice']
                    supplierProd.save()
                    desc = str(supplier.supCompanyName) + " updated price of product "+str(supplierProd.itemName)+" "\
                           +str(previousPrice) +""+currency+" to " + str(body['discountPrice'])+""+currency
                    mainView.notificationView(constants.Supplier, supplier.pk, desc, "UpdatedPrice", None, 1)
                    connection.set_schema(schema_name=currentSchema)
                return JsonResponse({'status': 'success', 'success_msg': 'Product updated successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Upload Holiday by CSV, Method is used to group the holidays with the user specified name"""
@csrf_exempt
def uploadHoliday(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                holidayFile = request.FILES['myfile']
                listCsv = list(csv.DictReader(io.TextIOWrapper(holidayFile)))
                dumps = json.dumps(listCsv)
                holidayFromCsv = json.loads(dumps)
                if len(holidayFromCsv) > 0:
                    holidayYear = request.POST['year']
                    holidayName = request.POST['name']
                    holiday = utilitySD.getHolidayByName(holidayName)
                    for holidayRow in holidayFromCsv:
                        try:
                            dateColumn = holidayRow["DATE"]
                            reasonColumn = holidayRow["REASON"]
                            datetime.datetime.strptime(dateColumn, "%d/%m/%Y")
                        except:
                            return JsonResponse(
                                {'status': 'showerror',
                                 'error_msg': 'Please upload the csv with proper format/headers/mandotary fields'})
                    if not holiday:
                       holiday = Holidays()
                       holiday.holidayYear = holidayYear
                       holiday.holidayName = holidayName
                       holiday.save()
                    for holidayRow in holidayFromCsv:
                        dateColumn = holidayRow["DATE"]
                        reasonColumn = holidayRow["REASON"]
                        HolidaysDetails(holidayDate=dateColumn,holidayReason=reasonColumn,holiday=holiday).save()
                    return JsonResponse(
                        {'status': 'success', 'error_msg': 'Holidays uploaded Successfully'})
                else:
                    return JsonResponse(
                        {'status': 'showerror', 'error_msg': 'Please upload csv with data'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to get the group of holidays for the specified holiday id"""
@csrf_exempt
def getHoliday(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        holiday = Holidays.objects.filter(status=constants.Active).values()
        if 'holidayId' in body:
            holiday = HolidaysDetails.objects.filter(holiday_id= body['holidayId']).values()
        return JsonResponse({'status': 'success', 'data': list(holiday)})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to return the supplier sites by using supplierId"""
@csrf_exempt
def fetchSupplierSites(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        supplierId = body['supId']
        supplier = utilitySD.getSupplierById(supplierId)
        usrSupSites = SupplierSlaForSites.objects.filter(userSupSitesCompany=supplier,
                                                         status=constants.Active).values('mappedSites')
        supplierSites = Sites.objects.all().exclude(siteId__in=usrSupSites).values('siteName','siteId')
        return JsonResponse({'status': 'success', 'userData': list(supplierSites)})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def saveSlaForSupplierFromCus(request):
    if ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                supId = body['supplierId']
                supplier = utilitySD.getSupplierById(supId)
                cusAndSupMapSites = body['data']
                for sites in cusAndSupMapSites:
                    siteDetail = utilitySD.getSiteBySiteId(sites)
                    try:
                        customerSite=SupplierSlaForSites.objects.get(userSupSitesCompany=supplier,mappedSites_id=sites)
                        customerSite.status = constants.Active
                    except:
                        customerSite = SupplierSlaForSites()
                        customerSite.mappedSites_id = sites
                        customerSite.userSupSitesCompany = supplier
                    slaJsonData = utilitySD.getSlaBySlaId(body['sla'])
                    customerSite.slaFromSupplier = slaJsonData.slaDetails
                    customerSite.supplier_country=Country.objects.get(countryName=siteDetail.siteAddress.usradd_country)
                    customerSite.supplier_address_Line1 = siteDetail.siteAddress.usradd_address_Line1
                    customerSite.supplier_address_Line2 = siteDetail.siteAddress.usradd_address_Line2
                    customerSite.supplier_unit1 = siteDetail.siteAddress.usradd_unit1
                    customerSite.supplier_unit2 = siteDetail.siteAddress.usradd_unit2
                    customerSite.supplier_state = siteDetail.siteAddress.usradd_state
                    customerSite.supplier_postalCode = siteDetail.siteAddress.usradd_postalCode
                    customerSite.selfCreation = True
                    customerSite.linkedStatus = False
                    customerSite.save()
                return JsonResponse({'status': 'success', 'success_msg': 'Assigned successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'success', 'success_msg': 'SLA Added successfully',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def sitesAddingForSla(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                usrId = body['sendFromId']
                notificationId = body['id']
                type = body['type']
                supplier = utilitySD.getSupplierById(usrId)
                supplierCompany = utility.getCompanyByCompanyCode(supplier.supCompanyCode)
                sitesid = Sites.objects.all().values('siteId')
                s = list(sitesid)
                utilitySD.notificationStatusChangeByID(notificationId)
                if type == "accept":
                    currentSchema = connection.schema_name
                    for siteid in s:
                        siteInfo = utilitySD.getSiteBySiteId(siteid['siteId'])
                        try:
                            usersupsite = SupplierSlaForSites.objects.get(userSupSitesCompany=
                                                                          supplier,mappedSites_id=siteid['siteId'])
                        except:
                            usersupsite = SupplierSlaForSites()
                        usersupsite.userSupSitesCompany = supplier
                        usersupsite.mappedSites_id = siteid['siteId']
                        usersupsite.slaFromSupplier = constants.SlaDetailsJson
                        usersupsite.status = constants.Active
                        usersupsite.selfCreation = False
                        usersupsite.save()
                        customer_country = siteInfo.siteAddress.usradd_country
                        customer_address_Line1 = siteInfo.siteAddress.usradd_address_Line1
                        customer_address_Line2 = siteInfo.siteAddress.usradd_address_Line2
                        customer_unit1 = siteInfo.siteAddress.usradd_unit1
                        customer_unit2 = siteInfo.siteAddress.usradd_unit2
                        customer_state = siteInfo.siteAddress.usradd_state
                        customer_postalCode = siteInfo.siteAddress.usradd_postalCode
                        userCustSiteName = siteInfo.siteName
                        connection.set_schema(schema_name=supplierCompany.schemaName)
                        customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                        try:
                            customerSite = CustomerSiteDetails.objects.get(userCustSitesCompany=customer,
                                                                           userCustSiteId=siteid['siteId'])
                            customerSite.status = constants.Active
                        except:
                            customerSite = CustomerSiteDetails()
                        customerSite.customer_country = customer_country
                        customerSite.customer_address_Line1 = customer_address_Line1
                        customerSite.customer_address_Line2 = customer_address_Line2
                        customerSite.customer_unit1 = customer_unit1
                        customerSite.customer_unit2 = customer_unit2
                        customerSite.customer_state = customer_state
                        customerSite.customer_postalCode = customer_postalCode
                        customerSite.userCustSiteId = siteid['siteId']
                        customerSite.userCustSiteName = userCustSiteName
                        customerSite.userCustSitesCompany = customer
                        customerSite.save()
                        connection.set_schema(schema_name=currentSchema)
                    connection.set_schema(schema_name=supplierCompany.schemaName)
                    mainView.notificationView(constants.Customer,customer.customerId,
                                              str(customer.cusCompanyName)+" gave access to assign SLA ",
                                              "customer",None,1)
                    connection.set_schema(schema_name=currentSchema)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': "SLA allowed successfully"})
                else:
                    return JsonResponse(
                        {'status': 'success', 'success_msg':"Rejected Successfully"})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'success', 'success_msg': 'SLA Added successfully',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get all the active sites from the current schema"""
@csrf_exempt
def getAllSites(request):
    if 'user' in request.session or 'subUser' in request.session:
        site = Sites.objects.filter(status=constants.Active).values('siteId', 'siteName', 'siteDesc',
                                                                        'siteType__siteTypeName',
                                                                        'siteArea__areaName',
                                                                        'siteAddress__usradd_address_Line1',
                                                                        'siteAddress__usradd_address_Line2',
                                                                        'siteAddress__usradd_unit1',
                                                                        'siteAddress__usradd_unit2',
                                                                        'siteAddress__usradd_country__countryName',
                                                                        'siteAddress__usradd_state__stateName',
                                                                        'siteAddress__usradd_postalCode',
                                                                        ).order_by('siteId')
        item = {}
        totalItems = []
        item['site'] = list(site)
        totalItems.append(item)
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to create site for the current schema"""
@csrf_exempt
def createSite(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                if utility.checkEntryCountBasedOnPlanAndFeatures(utility.getCompanyBySchemaName(connection.schema_name),
                                                                 'Sites',
                                                                 utilitySD.getCountOftheModelByModelName("Sites")):
                    a = request.body.decode('utf-8')
                    body = json.loads(a)
                    siteName = body['siteName']
                    alreadyExistSite = utilitySD.getSiteBySiteName(siteName)
                    if alreadyExistSite is None:
                        address = UserAddress()
                        address.usradd_country_id = body['country']
                        address.usradd_address_Line1 = body['address_Line1']
                        address.usradd_address_Line2 = body['address_Line2']
                        address.usradd_unit1 = body['unit1']
                        address.usradd_unit2 = body['unit2']
                        address.usradd_state_id = body['state']
                        address.usradd_postalCode = body['postalCode']
                        address.usradd_addressType = siteName
                        address.save()
                        site = Sites()
                        site.siteArea_id = body['siteArea']
                        site.siteType_id = body['siteType']
                        site.siteDesc = body['siteDesc']
                        site.siteName = siteName
                        site.siteAddress = address
                        site.save()
                        return JsonResponse({'status':'success','success_msg':'Site created successfully','id':site.pk})
                    else:
                        return JsonResponse({'status': 'error', 'error_msg': 'Site Name already exists!!.'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Your Purchased Site Limit Is Exceeded'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to update site by using site Id"""
@csrf_exempt
def updateSite(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                siteId = body['siteId']
                if body['type'] == 'edit':
                    site = Sites.objects.filter(siteId=siteId).values('siteId', 'siteName', 'siteDesc',
                                                                      'siteArea','siteType',
                                                                      'siteAddress__usradd_country',
                                                                      'siteAddress__usradd_address_Line2',
                                                                      'siteAddress__usradd_address_Line1',
                                                                      'siteAddress__usradd_unit1',
                                                                      'siteAddress__usradd_unit2',
                                                                      'siteAddress__usradd_state',
                                                                      'siteAddress__usradd_postalCode',
                                                                      ).order_by('siteId')
                    return JsonResponse({'status': 'success', 'site': list(site)})
                else:
                    siteName = body['siteName']
                    try:
                        alreadyExistSite = Sites.objects.filter(~Q(siteId=siteId), siteName=siteName).all()
                    except:
                        alreadyExistSite = None
                    if alreadyExistSite:
                        return JsonResponse({'status': 'error', 'error_msg': 'Site Name already exists!!.'})
                    else:
                        site = utilitySD.getSiteBySiteId(siteId)
                        site.siteArea_id = body['siteArea']
                        site.siteType_id = body['siteType']
                        site.siteDesc = body['siteDesc']
                        if site.pk !=1:
                            site.siteName = siteName
                        site.save()
                        address = UserAddress.objects.get(pk=site.siteAddress_id)
                        address.usradd_country_id = body['editcountry']
                        address.usradd_address_Line1 = body['editaddress_Line1']
                        address.usradd_address_Line2 = body['editaddress_Line2']
                        address.usradd_unit1 = body['editunit1']
                        address.usradd_unit2 = body['editunit2']
                        address.usradd_state_id = body['editstate']
                        address.usradd_postalCode = body['editpostalCode']
                        address.save()
                        supplierList = SupplierSlaForSites.objects.filter(mappedSites=siteId).values()
                        currentSchema = connection.schema_name
                        for sup in supplierList:
                            connection.set_schema(schema_name=currentSchema)
                            supplier = utilitySD.getSupplierById(sup['userSupSitesCompany_id'])
                            supplierCompany = utility.getCompanyByCompanyCode(supplier.supCompanyCode)
                            connection.set_schema(schema_name=supplierCompany.schemaName)
                            suppliersite = utilitySD.getCustomerSiteDetailsForUpdateSites(siteId)
                            if suppliersite:
                                suppliersite.userCustSiteName = siteName
                                suppliersite.customer_address_Line1 = body['editaddress_Line1']
                                suppliersite.customer_address_Line2 = body['editaddress_Line2']
                                suppliersite.customer_unit1 = body['editunit1']
                                suppliersite.customer_unit2 = body['editunit2']
                                suppliersite.customer_postalCode = body['editpostalCode']
                                suppliersite.customer_country_id = body['editcountry']
                                suppliersite.customer_state_id = body['editstate']
                                suppliersite.save()
                        connection.set_schema(schema_name=currentSchema)

                        return JsonResponse({'status': 'success', 'success_msg': 'Site Updated successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to delete site by using site Id"""
@csrf_exempt
def deleteSite(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                siteId = body['siteId']
                customerList = utilitySD.getCustomerListBasedonSite(siteId)
                if customerList:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': 'Cant able to delete the Site.This site has customers.!!!'})
                else:
                    site = utilitySD.getSiteBySiteId(siteId)
                    site.status = constants.Inactive
                    site.siteName = None
                    site.save()
                    return JsonResponse({'status': 'success', 'success_msg': 'Site deleted successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Get all the service level agreement details"""
@csrf_exempt
def fetchSLAData(request):
    if 'user' in request.session or 'subUser' in request.session:
        SLAData = serviceLevelAgreement.objects.filter(status=constants.Active).values('slaId', 'slaType',
                                                                                          'status',
                                                                                          ).order_by('slaId')
        return JsonResponse({'status': 'success', 'SLAData': list(SLAData)})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Get the particular service level agreement details by using sla id"""
@csrf_exempt
def slaDetailsByslaId(request):
    if 'user' in request.session or 'subUser' in request.session:
        body = json.loads(request.body.decode('utf-8'))
        slaId = body['slaId']
        SLAData = serviceLevelAgreement.objects.filter(pk=slaId, status=constants.Active).values('slaId',
                                                                                                 'slaType',
                                                                                                 'slaDetails',
                                                                                                 'status',
                                                                                                 ).order_by('slaId')
        return JsonResponse({'status': 'success', 'SLAData': list(SLAData)})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is used to update SLA and also the updated SLA is send to previous assigned customers for accept/reject"""
@csrf_exempt
def updateSlaForCustomer(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                body = json.loads(request.body.decode('utf-8'))
                slaId = body['slaId']
                slaType = body['slaType']
                alreadyExistsSla = serviceLevelAgreement.objects.filter(~Q(slaId=slaId), slaType=slaType).all()
                if alreadyExistsSla.count() == 0:
                    sla = utilitySD.getSlaBySlaId(slaId)
                    body['slaJson']['orderingSchedule'] = int(body['slaJson']['orderingSchedule'])
                    if sla.pk != 1:
                        sla.slaType = body['slaType']
                    sla.slaDetails = body['slaJson']
                    sla.save()
                    customeList = utilitySD.getCustomerListBasedonSla(slaId)
                    currentSchema = connection.schema_name
                    if customeList:
                        for individualCustomer in customeList:
                            customerSchema = utility.getCompanyByCompanyCode\
                                (individualCustomer['userCustSitesCompany__cusCompanyCode']).schemaName
                            connection.set_schema(schema_name=customerSchema)
                            supplier = utilitySD.getSupplierByConnectionCode(
                                individualCustomer['userCustSitesCompany__connectionCode'])
                            slaCustomer = SupplierSlaForSites.objects.get(
                                userSupSitesCompany=supplier,mappedSites_id=individualCustomer['userCustSiteId'])
                            slaCustomer.slaFromSupplier = body['slaJson']
                            slaCustomer.linkedStatus = False
                            slaCustomer.save()
                            mainView.notificationView(constants.Supplier, "/viewSupplierSLA?id="+str(supplier.pk),
                                                      userCompany.companyName + " updated the sla", "href",None,1)
                        connection.set_schema(schema_name=currentSchema)
                    return JsonResponse({'status': 'success', 'success_msg': 'SLA updated successfully'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'SLA Name already exists'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Get particular address information by using addressId"""
@csrf_exempt
def getAddressByAddressId(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        addressId = body['addressId']
        address = UserAddress.objects.filter(pk=addressId).values(
            'usradd_address_Line1',
            'usradd_address_Line2',
            'usradd_unit1',
            'usradd_unit2',
            'usradd_country__countryName',
            'usradd_state__stateName',
            'usradd_postalCode', )
        item = {}
        totalItems = []
        item['address'] = list(address)
        totalItems.append(item)
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Delete the service level agreement by using slaId"""
@csrf_exempt
def deleteSla(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                slaId = body['slaId']
                customerList = utilitySD.getCustomerListBasedonSla(slaId)
                if customerList:
                    return JsonResponse(
                        {'status': 'error',
                         'error_msg': 'Cant able to delete the SLA.This SLA has been assigned to customers.!!'})
                else:
                    sla = utilitySD.getSlaBySlaId(slaId)
                    sla.slaType = None
                    sla.status = constants.Inactive
                    sla.save()
                    return JsonResponse({'status': 'success', 'success_msg': 'SLA deleted successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get Roles permission details by using roleId"""
@csrf_exempt
def accessProvideByRole(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        role = body['role']
        roleAccess = utilitySD.getRoleById(role).roleArray
        return JsonResponse({'status': 'success', 'roleAccess': roleAccess})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Assign SLA to Customer HTML - Page has assign Existing/New SLA to the customer sites"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def fetchAllCustomerForSlaAssign(request):
    if ('user' in request.session or 'subUser' in request.session):
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        wsid = None
        if request.GET.get('wsid', None) is not None:
            wsid = request.GET.get('wsid', '')
        if request.GET.get('notificationId', None) is not None:
            noty = request.GET['notificationId']
            utilitySD.notificationStatusChangeByID(noty)
        areaAddForm = AreaAddForm()
        AddSiteFormdetails = EditSiteForm()
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
            customerDetails=[]
            if wsid:
                booleanValue = True
                customerDetails = Customer.objects.filter(customerId=wsid,status=constants.Active).values(
                    'cusCompanyName', 'customerId')
            if wsid is None or not customerDetails:
                customerDetails = Customer.objects.filter(status=constants.Active).values('cusCompanyName','customerId')
                booleanValue = False
            return render(request, 'assignSlaToCustomer.html',{'cus':customerDetails,'urls':list(urls),
                                                               'user': currentUser, 'ProfileForm': ProfileForm,
                                                                'companyProfileForm': companyProfileForm,
                                                               'subUserProfile': subUserProfile,
                                                               'status': company.urlchanged,'company':company,
                                                               'default':booleanValue,'AddSiteForm':AddSiteFormdetails,
                                                               'areaAddForm':areaAddForm,'noti': notiFy,'leng': lengTh,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Assign SLA to Customer HTML - Page has update customer sites SLA functionalities"""
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def fetchAllCustomerForSlaAssigned(request):
    if ('user' in request.session or 'subUser' in request.session):
        ProfileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        wsid = None
        if request.GET.get('wsid', None) is not None:
            wsid = request.GET.get('wsid', '')
        areaAddForm = AreaAddForm()
        AddSiteFormdetails = EditSiteForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, "fetchAllCustomerForSlaAssign")
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser, "fetchAllCustomerForSlaAssign")
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
            # customerDetails=[]
            booleanValue = False
            customerDetails = Customer.objects.filter(status=constants.Active).values('cusCompanyName','customerId')
            return render(request, 'assignedSlaToCustomer.html',{'cus':customerDetails,'user': currentUser,
                                                                 'ProfileForm': ProfileForm,
                                                                 'companyProfileForm': companyProfileForm,
                                                                 'urls':list(urls),'subUserProfile': subUserProfile,
                                                                 'status': company.urlchanged,'company':company,
                                                                 'default':booleanValue,'leng': lengTh,
                                                                 'AddSiteForm':AddSiteFormdetails,
                                                                 'areaAddForm':areaAddForm,'noti': notiFy,'subscribedModules':subscribedModules})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


"""Method is used to get the assigned/not assigned customer site details by using customerId"""
@csrf_exempt
def fetchCustomerSites(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        customerId = body['cusId']
        customer = utilitySD.getCustomerById(customerId)
        createSite= False
        if customer.relationshipStatus == False:
            createSite = True
        if 'assigned' in body:
            usrCusSites = CustomerSiteDetails.objects.filter(mappedSites__isnull=False,userCustSitesCompany=customer,
                                                             status=constants.Active).values(
                                                        'userCustSiteName','userCustSitesId',
                                                        'customer_country__countryName','customer_address_Line1',
                                                        'customer_address_Line2','customer_unit1','customer_unit2',
                                                        'customer_state__stateName','customer_postalCode',
                                                         'mappedSites__siteName')
        else:
            usrCusSites = CustomerSiteDetails.objects.filter(mappedSites__isnull=True, userCustSitesCompany=customer,
                                                             status=constants.Active).values(
                'userCustSiteName', 'userCustSitesId',
                'customer_country__countryName', 'customer_address_Line1',
                'customer_address_Line2', 'customer_unit1', 'customer_unit2',
                'customer_state__stateName', 'customer_postalCode'
            )
        return JsonResponse({'status': 'success', 'userData': list(usrCusSites),'createSite':createSite})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def saveSlaForCustomerFromSup(request):
    if ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                cusId = body['customerId']
                customer = utilitySD.getCustomerById(cusId)
                customerCompany = utility.getCompanyByCompanyCode(customer.cusCompanyCode)
                cusAndSupMapSites = body['data']
                currentSchema = connection.schema_name
                string = ""
                for sites in cusAndSupMapSites:
                    siteDetail = utilitySD.getSiteBySiteId(sites['supplier'])
                    siteAddress = siteDetail.siteAddress
                    customerSite = CustomerSiteDetails.objects.get(userCustSitesCompany=customer,
                                                                   userCustSitesId=sites['customer'])
                    customerSite.mappedSites = siteDetail
                    customerSite.status = constants.Active
                    customerSite.save()
                    string += customerSite.userCustSiteName + ","
                    slaJsonData = siteDetail.siteArea.areaSlaId.slaDetails
                    if customer.relationshipStatus:
                        connection.set_schema(schema_name=customerCompany.schemaName)
                        supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                        usersupsite = SupplierSlaForSites.objects.get(userSupSitesCompany=supplier,
                                                                      mappedSites_id=customerSite.userCustSiteId)
                        usersupsite.supplier_country = siteAddress.usradd_country
                        usersupsite.supplier_address_Line1 = siteAddress.usradd_address_Line1
                        usersupsite.supplier_address_Line2 = siteAddress.usradd_address_Line2
                        usersupsite.supplier_unit1 = siteAddress.usradd_unit1
                        usersupsite.supplier_unit2 = siteAddress.usradd_unit2
                        usersupsite.supplier_state = siteAddress.usradd_state
                        usersupsite.supplier_postalCode =siteAddress.usradd_postalCode
                        usersupsite.status = constants.Active
                        usersupsite.slaFromSupplier = slaJsonData
                        usersupsite.save()
                    connection.set_schema(schema_name=currentSchema)
                if customer.relationshipStatus:
                    connection.set_schema(schema_name=customerCompany.schemaName)
                    supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                    mainView.notificationView(constants.Supplier, "/viewSupplierSLA?id="+str(supplier.pk),
                                        str(supplier.supCompanyName) + " have assigned SLA to your sites ("+string+")",
                                              "href",None,1)
                connection.set_schema(schema_name=currentSchema)
                return JsonResponse({'status': 'success', 'success_msg': 'Assigned successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'success', 'success_msg': 'SLA Added successfully',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def fetchSupplierForSitePushing(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        excludeItems = SupplierSlaForSites.objects.filter(mappedSites_id=body['siteId'],selfCreation=False,
                                                          status=constants.Active).values('userSupSitesCompany')
        supplierList = Supplier.objects.filter(relationshipStatus=True,status=constants.Active).exclude(
            supplierId__in=excludeItems).values('supCompanyName','supplierId')
        return JsonResponse({'status': 'success', 'supplierList': list(supplierList)})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def pushingSitestoSupplier(request):
    if ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, "sitesAddingForSla")
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                supplierList = body['suppliers']
                siteId = body['siteId']
                currentSchema = connection.schema_name
                for sup in supplierList:
                    supplier = utilitySD.getSupplierById(sup)
                    siteInfo = utilitySD.getSiteBySiteId(siteId)
                    try:
                        usersupsite = SupplierSlaForSites.objects.get(userSupSitesCompany=supplier,mappedSites=siteInfo)
                        usersupsite.status = constants.Active
                        usersupsite.selfCreation = False
                    except:
                        usersupsite = SupplierSlaForSites()
                        usersupsite.userSupSitesCompany = supplier
                        usersupsite.mappedSites = siteInfo
                    usersupsite.slaFromSupplier = constants.SlaDetailsJson
                    usersupsite.supplier_country = siteInfo.siteAddress.usradd_country
                    usersupsite.supplier_address_Line1 = siteInfo.siteAddress.usradd_address_Line1
                    usersupsite.supplier_address_Line2 = siteInfo.siteAddress.usradd_address_Line2
                    usersupsite.supplier_unit1 = siteInfo.siteAddress.usradd_unit1
                    usersupsite.supplier_unit2 = siteInfo.siteAddress.usradd_unit2
                    usersupsite.supplier_state = siteInfo.siteAddress.usradd_state
                    usersupsite.supplier_postalCode = siteInfo.siteAddress.usradd_postalCode
                    usersupsite.linkedStatus = False
                    usersupsite.save()
                    supplierCompany = utility.getCompanyByCompanyCode(supplier.supCompanyCode)
                    connection.set_schema(schema_name=supplierCompany.schemaName)
                    customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                    try:
                        customerSite = CustomerSiteDetails.objects.get(userCustSiteId=siteId,
                                                                       userCustSitesCompany=customer)
                        customerSite.status = constants.Active
                        customerSite.linkedStatus= False
                    except:
                        customerSite = CustomerSiteDetails()
                    connection.set_schema(schema_name=currentSchema)
                    customerSite.customer_country = siteInfo.siteAddress.usradd_country
                    customerSite.customer_address_Line1 = siteInfo.siteAddress.usradd_address_Line1
                    customerSite.customer_address_Line2 = siteInfo.siteAddress.usradd_address_Line2
                    customerSite.customer_unit1 = siteInfo.siteAddress.usradd_unit1
                    customerSite.customer_unit2 = siteInfo.siteAddress.usradd_unit2
                    customerSite.customer_state = siteInfo.siteAddress.usradd_state
                    customerSite.customer_postalCode = siteInfo.siteAddress.usradd_postalCode
                    customerSite.userCustSiteId = siteId
                    customerSite.userCustSiteName = siteInfo.siteName
                    connection.set_schema(schema_name=supplierCompany.schemaName)
                    customerSite.userCustSitesCompany = customer
                    customerSite.save()
                    mainView.notificationView(constants.Customer, customer.customerId,
                                              str(customer.cusCompanyName) + " requesting to assign SLA for new site "+
                                              str(customerSite.userCustSiteName), "customer",None,1)
                    connection.set_schema(schema_name=currentSchema)
                return JsonResponse({'status': 'success','success_msg':'successfully pushed the sites to vendor(s)',
                                     'supplierList': list(supplierList)})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# Fetch the Area Data
@csrf_exempt
def fetchAreaData(request):
    if 'user' in request.session or 'subUser' in request.session:
        areaData = Area.objects.filter(status=constants.Active).values('areaId', 'areaName', 'areaDesc',
                                                                       'areaSlaId__slaType').order_by('areaId')
        return JsonResponse({'status': 'success', 'areaData': list(areaData)})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def createAreaDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                if utility.checkEntryCountBasedOnPlanAndFeatures(utility.getCompanyBySchemaName(connection.schema_name),
                                                                 'Area',
                                                                 utilitySD.getCountOftheModelByModelName("Area")):
                    a = request.body.decode('utf-8')
                    body = json.loads(a)
                    if body['type'] == constants.Create:
                        AreaDet = utilitySD.getAreaByAreaName(body['areaName'])
                        if AreaDet is None or (AreaDet and AreaDet.status != constants.Active):
                            if AreaDet and AreaDet.status != constants.Active:
                                AreaDet.areaName = None
                                AreaDet.save()
                            areaDetails = Area()
                            addNewArea(areaDetails, body)
                            return JsonResponse({'status': 'success', 'success_msg': 'Area added successfully'})
                        else:
                            return JsonResponse({'status': 'error', 'error_msg': 'Area Name is already exist'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Your Purchased Area Limit Is Exceeded'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def addNewArea(areaDetails, body):
    areaDetails.areaName = body['areaName']
    areaDetails.areaDesc = body['areaDesc']
    areaDetails.areaSlaId_id = body['areaSla']
    areaDetails.save()


@csrf_exempt
def fetchAreaDataViaId(request):
    if 'user' in request.session or 'subUser' in request.session:
        body = json.loads(request.body.decode('utf-8'))
        areaData = Area.objects.filter(pk=body['areaId']).values('areaId', 'areaName', 'areaDesc', 'areaSlaId')
        return JsonResponse({'status': 'success', 'areaData': list(areaData)})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def updateAreaDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
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
                        addNewArea(areaDetails, body)
                        return JsonResponse({'status': 'success', 'success_msg': 'Area updated successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def removeAreaDataViaId(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                try:
                    siteDet = Sites.objects.filter(siteArea=body['areaId'], status=constants.Active).values()
                except:
                    siteDet = None

                if siteDet:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': 'Area has active sites.So cannot able to delete the area'})
                else:
                    areaDetails = utilitySD.getAreaById(body['areaId'])
                    areaDetails.status = constants.Inactive
                    areaDetails.areaName = None
                    areaDetails.save()
                    return JsonResponse({'status': 'success', 'success_msg': 'Area removed successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get all delivery address for the current user"""
def getUserAddress(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'subUser' in request.session:
            loginUser = utility.getObjectFromSession(request, 'subUser')
            if loginUser.superAdmin:
                site = Sites.objects.filter(status=constants.Active)
            else:
                subSites = SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=loginUser).values(
                    'subuserSiteAssignSites__siteId')
                site = Sites.objects.filter(status=constants.Active,siteId__in=subSites)
        else:
            site = Sites.objects.filter(status=constants.Active)
        totalSites = site.values('siteId', 'siteName', 'siteDesc',
                                'siteType__siteTypeName',
                                'siteArea__areaName',
                                'siteAddress__usradd_address_Line1',
                                'siteAddress__usradd_address_Line2',
                                'siteAddress__usradd_unit1',
                                'siteAddress__usradd_unit2',
                                'siteAddress__usradd_country__countryName',
                                'siteAddress__usradd_state__stateName',
                                'siteAddress__usradd_postalCode',
                                ).order_by('siteId')
        totalItems = []
        item = {}
        item['site'] = list(totalSites)
        totalItems.append(item)
        return JsonResponse({'status': 'success', 'totalItems': totalItems})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def upload_pic(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            usr = utility.getObjectFromSession(request, 'user')
            userCompany = usr.userCompanyId
            currentSchemaName = userCompany.schemaName
            model = User
            sessionKey = 'user'
            pk = usr.pk
            check = True
        else:
            usr = utility.getObjectFromSession(request, 'subUser')
            currentSchemaName = connection.schema_name
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(usr, request.path)
            model = Subuser
            sessionKey = 'subUser'
            pk = usr.pk
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                type = request.POST['type'].lower()
                fs = FileSystemStorage(location=settings.MEDIA_ROOT + "/" + currentSchemaName)
                userimage = request.FILES['myfile']
                name = fs.save(userimage.name, userimage)
                if type == constants.Company:
                    cmpny = utility.getCompanyByCompanyId(usr.userCompanyId)
                    cmpny.companyImage = currentSchemaName + "/" + name
                    cmpny.save()
                elif type == constants.Profile:
                    usr.profilepic = currentSchemaName + "/" + name
                    usr.save()
                    utility.updateSessionforObject(request, sessionKey, model, pk)

                return JsonResponse({'status': 'success', 'success_msg': type})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to update user and company informations and also the changes is updated into their supplier/customer side"""
def profileUpdate(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            usr = utility.getObjectFromSession(request, 'user')
            cmpny = utility.getCompanyByCompanyId(usr.userCompanyId)
        else:
            cmpny = utility.getCompanyBySchemaName(connection.schema_name)
            usr = utility.getUserByCompanyId(cmpny)
        account = utility.getoTAccountByCompany(cmpny)
        if not account.planSuspended:
            contactNo = request.POST['contactNo']
            email = request.POST['email'].lower()
            companyName = request.POST['companyName']
            countryCode = utility.getCountryCodeById(request.POST['countryCode'])
            emailValidation = User.objects.filter(~Q(pk=usr.pk),email__iexact = email,status = constants.Active)
            contactValidation = User.objects.filter(~Q(pk=usr.pk),contactNo = contactNo,status = constants.Active)
            companyNameValidation = Company.objects.filter(~Q(pk=cmpny.pk),companyName__iexact =
                                    companyName,status = constants.Active)
            if contactValidation:
                return JsonResponse({'status': 'error', 'error_msg': 'Contact Number already exists. Contact Admin'})
            elif emailValidation:
                return JsonResponse({'status': 'error', 'error_msg': 'Email already exists. Contact Admin'})
            elif companyNameValidation:
                return JsonResponse({'status': 'error', 'error_msg': 'Company Name already exists. Contact Admin'})
            else:
                check = True
                usraddr = UserAddress.objects.get(usradd_addressType=constants.HeadQuarter)
                usr.firstName = request.POST['firstName']
                usr.lastName = request.POST['lastName']
                usr.contactNo = contactNo
                usr.countryCode = countryCode
                usr.email = email
                usr.sec_question_id = request.POST['sec_question']
                usr.sec_answer = request.POST['sec_answer']
                usr.save()
                cmpny.companyName = companyName
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
                if check:
                    connectedSuppliers = Supplier.objects.filter(relationshipStatus=True,status=constants.Active)
                    connectedCustomers = Customer.objects.filter(relationshipStatus=True,status=constants.Active)
                    currentSchema = connection.schema_name
                    if connectedSuppliers:
                        for singleSupplier in connectedSuppliers:
                            supplierCompany = utility.getCompanyByCompanyCode(singleSupplier.supCompanyCode)
                            connection.set_schema(schema_name=supplierCompany.schemaName)
                            customer = utilitySD.getCustomerByConnectionCode(singleSupplier.connectionCode)
                            customer.cusCompanyName = companyName
                            customer.cusEmail = email
                            customer.cusContactNo = contactNo
                            customer.cusCountryCode = countryCode
                            customer.save()
                            connection.set_schema(schema_name=currentSchema)
                    if connectedCustomers:
                        for singleCustomer in connectedCustomers:
                            customerCompany = utility.getCompanyByCompanyCode(singleCustomer.cusCompanyCode)
                            connection.set_schema(schema_name=customerCompany.schemaName)
                            supplier = utilitySD.getSupplierByConnectionCode(singleCustomer.connectionCode)
                            supplier.supCompanyName = companyName
                            supplier.supEmail = email
                            supplier.supContactNo = contactNo
                            supplier.supCountryCode = countryCode
                            supplier.save()
                    connection.set_schema(schema_name=currentSchema)
                connectedCustomers = Customer.objects.filter(relationshipStatus=True, status=constants.Active)
                connectedSuppliers = Supplier.objects.filter(relationshipStatus=True, status=constants.Active)
                currentSchema = connection.schema_name
                for singleCustomer in connectedCustomers:
                    customerCompany = utility.getCompanyByCompanyCode(singleCustomer.cusCompanyCode)
                    connection.set_schema(schema_name=customerCompany.schemaName)
                    sup = utilitySD.getSupplierByConnectionCode(singleCustomer.connectionCode)
                    sup.supCountry = Country.objects.get(countryId=request.POST['country'])
                    sup.supAddress_Line1 = request.POST['address_Line1']
                    sup.supAddress_Line2 = request.POST['address_Line2']
                    sup.supUnit1 = request.POST['unit1']
                    sup.supUnit2 = request.POST['unit2']
                    sup.supState = State.objects.get(stateId=request.POST['state'])
                    sup.supPostalCode = request.POST['postalCode']
                    sup.save()
                    types = "profileUpdate"
                    mainView.notificationView(constants.Supplier, "", "Your vendor " + (str(sup.supCompanyName))+" changed the profile info ",types, None, 1)
                    connection.set_schema(schema_name=currentSchema)
                for singleSupplier in connectedSuppliers:
                    supplierCompany = utility.getCompanyByCompanyCode(singleSupplier.supCompanyCode)
                    connection.set_schema(schema_name=supplierCompany.schemaName)
                    cus = utilitySD.getCustomerByConnectionCode(singleSupplier.connectionCode)
                    cus.cusCountry = Country.objects.get(countryId=request.POST['country'])
                    cus.cusAddress_Line1 = request.POST['address_Line1']
                    cus.cusAddress_Line2 = request.POST['address_Line2']
                    cus.cusUnit1 = request.POST['unit1']
                    cus.cusUnit2 = request.POST['unit2']
                    cus.cusState = State.objects.get(stateId=request.POST['state'])
                    cus.cusPostalCode = request.POST['postalCode']
                    cus.save()
                    types = "profileUpdate"
                    mainView.notificationView(constants.Customer, "", "Your customer " + (str(cus.cusCompanyName))+" changed the profile info ",types, None, 1)
                    connection.set_schema(schema_name=currentSchema)
                if 'user' in request.session:
                    utility.updateSessionforObject(request, 'user', User, usr.pk)
                return JsonResponse({'status': 'success', 'success_msg': 'Profile Updated successfully'})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Invitation/Connection link send to respective customer/supplier as per the user request"""
@csrf_exempt
def inviteSend(request):
    if 'user' in request.session or 'subUser' in request.session:
        a = request.body.decode('utf-8')
        body = json.loads(a)
        if body["type"] == "supplier":
            type = "vendor"
        else:
            type = body["type"]
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            company = mainUser.userCompanyId
            token = mainUser.token
            check = True
        else:
            usr = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
            mainUser = utility.getUserByCompanyId(company.companyId)
            check = utility.checkRequesURLisPresentForSubUser(usr, request.path)
            token = mainUser.token
        account = utility.getoTAccountByCompany(company)
        if not account.planSuspended:
            if check:
                userCompanyName = company.companyName
                mail = body['email']
                # type = body['type']
                status = body['status']
                if status == constants.Invite:
                    if type.lower() == constants.Customer:
                        userTrd = utilitySD.getCustomerByEmail(mail)
                        url = settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT + '/subscription/?wsid=' + \
                              token + constants.C
                    else:
                        userTrd = utilitySD.getSupplierByEmail(mail)
                        url = settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT + '/subscription/?wsid=' + \
                              token + constants.S
                    userTrd.invitationStatus = 1
                    userTrd.save()
                    mainView.sendingEmail(request, userTrd, mail, userCompanyName, 'traders_adding_email.html',
                                 '' + userCompanyName + ' invite you to join in OrderTango',
                                 url , None,None)
                    return JsonResponse({'status': 'success', 'success_msg': 'Invitation sent successfully'})
                else:
                    traderUser = utility.getUserByEmail(mail)
                    if traderUser:
                        wsid = uuid.uuid4().hex
                        uid = urlsafe_base64_encode(force_bytes(mainUser.pk)).decode()
                        token = account_activation_token.make_token(mainUser)
                        currentSchema = connection.schema_name
                        if type.lower() == constants.Customer:
                            userTrd = utilitySD.getCustomerByEmail(mail)
                            userTrd.connectionCode = wsid
                            userTrd.save()
                            traderCompany = traderUser.userCompanyId
                            connection.set_schema(schema_name=traderCompany.schemaName)
                            url = "/acceptSupplier/" + uid + "/" + token + "/?wsid=" + wsid
                            mainView.notificationView(constants.Supplier, url, userCompanyName + " added you as a " +
                                                      type, "href",None,1)
                            connection.set_schema(schema_name=currentSchema)
                        else:
                            userTrd = utilitySD.getSupplierByEmail(mail)
                            userTrd.connectionCode = wsid
                            userTrd.save()
                            traderCompany = traderUser.userCompanyId
                            connection.set_schema(schema_name=traderCompany.schemaName)
                            url = "/acceptCustomer/" + uid + "/" + token + "/?wsid=" + wsid
                            mainView.notificationView(constants.Customer, url, userCompanyName + " added you as a " +
                                                      type, "href",None,1)
                            connection.set_schema(schema_name=currentSchema)
                        userTrd.connectionCode = wsid
                        userTrd.invitationStatus = 2
                        userTrd.save()

                        mainView.sendingEmail(request, mainUser, mail, traderUser,
                                     "add_existing_traders_email.html",
                                     userCompanyName + " added you as a " + type, type, None, wsid)
                        return JsonResponse({'status': 'success', 'success_msg': 'Connection sent successfully'})
                    else:
                        return JsonResponse({'status': 'success',
                                             'success_msg': 'Requested '+type+' is not in the system'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to create Service level agreement information as JSON"""
@csrf_exempt
def createSla(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            userCompany = currentUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                if utility.checkEntryCountBasedOnPlanAndFeatures(
                        utility.getCompanyBySchemaName(connection.schema_name),'serviceLevelAgreement',
                                       utilitySD.getCountOftheModelByModelName("serviceLevelAgreement")):
                    body = json.loads(request.body.decode('utf-8'))
                    slaType = body['slaType']
                    slaJson = body['slaJson']
                    alreadyExistsSla = utilitySD.getSlaBySlaName(slaType)
                    if alreadyExistsSla is None :
                        slaJson['orderingSchedule'] = int(slaJson['orderingSchedule'])
                        sla = serviceLevelAgreement(slaType=slaType,
                                                    slaDetails=slaJson,
                                                    )
                        sla.save()
                        return JsonResponse({'status': 'success', 'success_msg': 'SLA Added successfully'})
                    else:
                        return JsonResponse({'status': 'error', 'error_msg': 'SLA Name already exists'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Your Purchased SLA Limit Is Exceeded'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})



@csrf_exempt
def createSubUser(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            mainUser = utility.getUserByCompanyId(userCompany.companyId)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                if utility.checkEntryCountBasedOnPlanAndFeatures(utility.getCompanyBySchemaName(connection.schema_name),
                                                                 'Subuser',
                                                                 utilitySD.getCountOftheModelByModelName(
                                                                     "Subuser")):
                    invalidChars = set(string.punctuation.replace("_", ""))
                    minLength = 8
                    existsUserName =Subuser.objects.filter( userName__iexact=request.POST['userName'],
                                                            status=constants.Active).all()
                    email = request.POST['email'].lower()
                    contactNo = request.POST['contactNo']
                    countryCodeId = CountryCode.objects.get(countryCodeId=request.POST['countryCode'])
                    if existsUserName or (request.POST['userName'].lower() == mainUser.email.lower()):
                        return JsonResponse({'status': 'error', 'error_msg': 'User Name already exists!!!'})
                    if email != '':
                        existsEmail = utilitySD.getSubUserByEmail(email)
                        if existsEmail or (email == mainUser.email.lower()):
                            return JsonResponse({'status': 'error', 'error_msg': 'Email already exists!!!'})
                    existsContactNo = Subuser.objects.filter(contactNo=contactNo,countryCode=countryCodeId).all()
                    if existsContactNo or (contactNo == mainUser.contactNo and countryCodeId==mainUser.countryCode):
                        return JsonResponse({'status': 'error', 'error_msg': 'Contact Number already exists!!!'})
                    passWord = request.POST['password']
                    if passWord.isdigit() or not any(x.isupper() for x in passWord) or not any(
                            x.islower() for x in passWord) or len(passWord) < minLength or not any(
                        x.isdigit() for x in passWord) or not any(
                        char in invalidChars for char in passWord):
                        return JsonResponse({'status': 'error',
                                             'error_msg':"Password should contain at least %d characters with a mix of "
                                                        "uppercase,lowercase,special character,numeric " % minLength})
                    if request.POST['confirm_password'] != passWord:
                        return JsonResponse({'status': 'error', 'error_msg': 'Password does not match!!!'})
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                    try:
                        subuser = Subuser.objects.get( userName__iexact=request.POST['userName'],
                                                       status= constants.Inactive)
                    except:
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
                    subuser.contactNo = contactNo
                    subuser.status = constants.Active
                    if 'areaId' in request.POST:
                        subuser.area_id = request.POST['areaId']
                    if 'accessRights' in request.POST:
                        subuser.superAdmin = True
                        subuser.accessRights = request.POST['accessRights']
                    if 'role' in request.POST:
                        subuser.role = utilitySD.getRoleById(request.POST['role'])
                    subuser.email = email
                    subuser.DOJ = request.POST['DOJ']
                    subuser.countryCode = countryCodeId
                    subuser.DOD = ""
                    subuser.save()
                    if 'siteId' in request.POST:
                        sites = request.POST["siteId"]
                        if sites == "All":
                            sitesAll = Sites.objects.filter(siteArea__areaId=request.POST['areaId']).values()
                            if sitesAll:
                                for i in sitesAll:
                                    subusersiteaassign = SubuserSiteAssign()
                                    subusersiteaassign.subuserSiteAssignSubUser = subuser
                                    subusersiteaassign.subuserSiteAssignSites_id = i['siteId']
                                    subusersiteaassign.save()
                        else:
                            subusersiteaassign = SubuserSiteAssign()
                            subusersiteaassign.subuserSiteAssignSubUser = subuser
                            subusersiteaassign.subuserSiteAssignSites_id =request.POST["siteId"]
                            subusersiteaassign.save()
                    return JsonResponse({'status': 'success', 'success_msg': 'User created successfully'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Your Purchased User Limit Is Exceeded'})
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
def updateSubUser(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            mainUser = utility.getUserByCompanyId(userCompany.companyId)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                existsUserName = Subuser.objects.filter(~Q(pk=request.POST['subUserId']),status=constants.Active,
                                                        userName__iexact=request.POST['userName']).all()
                if existsUserName or (request.POST['userName'].lower() == mainUser.email.lower()):
                    return JsonResponse({'status': 'error', 'error_msg': 'User Name is already exists!!!'})
                email = request.POST['email'].lower()
                contactNo = request.POST['contactNo']
                countryCodeId = CountryCode.objects.get(countryCodeId=request.POST['countryCode'])
                if email != '' :
                    existsEmail = Subuser.objects.filter(~Q(pk=request.POST['subUserId']), email__iexact=email).all()
                    if existsEmail or (email == mainUser.email.lower()):
                        return JsonResponse({'status': 'error', 'error_msg': 'Email already exists!!!'})
                existsContactNo = Subuser.objects.filter(~Q(pk=request.POST['subUserId']), contactNo=contactNo
                                                         , countryCode=countryCodeId).all()
                if existsContactNo or (contactNo == mainUser.contactNo and countryCodeId==mainUser.countryCode):
                    return JsonResponse({'status': 'error', 'error_msg': 'Contact Number already exists!!!'})
                subuser = utilitySD.getSubUserById(request.POST['subUserId'])
                fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                if 'myfile' in request.FILES:
                    subuserimage = request.FILES['myfile']
                    imagename = fs.save(subuserimage.name, subuserimage)
                    subuser.profilepic = imagename
                subuser.firstName = request.POST['firstName']
                subuser.lastName = request.POST['lastName']
                subuser.userName = request.POST['userName']
                subuser.designation = request.POST['designation']
                subuser.contactNo = contactNo
                subuser.countryCode = countryCodeId
                if 'areaId' in request.POST:
                    subuser.area_id = request.POST['areaId']
                if 'accessRights' in request.POST:
                    subuser.accessRights = request.POST['accessRights']
                if 'role' in request.POST:
                    subuser.role = utilitySD.getRoleById(request.POST['role'])
                    subuser.DOJ = request.POST['DOJ']
                    subuser.DOD = request.POST['DOD']
                subuser.email = email
                subuser.save()
                SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=subuser.subUserId).delete()
                if 'siteId' in request.POST:
                    sites = request.POST["siteId"]
                    if sites == "All":
                        sitesAll = Sites.objects.filter(siteArea__areaId=request.POST['areaId']).values()
                        if sitesAll:
                            for i in sitesAll:
                                subusersiteaassign = SubuserSiteAssign()
                                subusersiteaassign.subuserSiteAssignSubUser = subuser
                                subusersiteaassign.subuserSiteAssignSites_id = i['siteId']
                                subusersiteaassign.save()
                    else:
                        subusersiteaassign = SubuserSiteAssign()
                        subusersiteaassign.subuserSiteAssignSubUser = subuser
                        subusersiteaassign.subuserSiteAssignSites_id = request.POST["siteId"]
                        subusersiteaassign.save()
                return JsonResponse({'status': 'success', 'success_msg': 'User updated successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to Get all the Subuser details"""
@csrf_exempt
def fetchSubUserData(request):
    if 'user' in request.session or 'subUser' in request.session:
        try:
            userData = Subuser.objects.filter(status__in=[constants.Active,constants.Disable],role__isnull = False).values('subUserId',
                                                                          'userName', 'designation','status',
                                                                          'role__roleName',
                                                                          'contactNo','countryCode__countryCodeType')

        except:
            userData = None
        if userData is not None:
            return JsonResponse({'status': 'success', 'userData': list(userData)})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get particular subuser details by using subuser Id"""
@csrf_exempt
def fetchSubUserDataViaId(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        body = json.loads(request.body.decode('utf-8'))
        subUserId = body['subUserId']
        subUser = utilitySD.getSubUserById(subUserId)
        if subUser:
            item = {}
            totalItems = []
            assignesSites = list(Subuser.objects.filter(subUserId=subUserId,
                                                        Subuser__subuserSiteAssignSites_id__isnull = False).values(
                'Subuser__subuserSiteAssignSites_id'))
            item['assignesSites'] = assignesSites
            item['totalSites'] = None
            item['area'] = subUser.area_id
            if assignesSites:
                area = Area.objects.get(area_sites=assignesSites[0]['Subuser__subuserSiteAssignSites_id'])
                item['totalSites'] = list(area.area_sites
                                          .filter(status=constants.Active).values('siteId', 'siteName'))
            item['totalItem'] = list(Subuser.objects.filter(subUserId=subUserId).values())
            if  subUser.role:
                item['role'] = subUser.role.pk
            item['countryCode'] = subUser.countryCode.pk
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to delete the particular subuser by using subuserId"""
@csrf_exempt
def deleteSubUserData(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
            currentUser = None
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                body = json.loads(request.body.decode('utf-8'))
                subUserId = body['subUserId']
                if currentUser:
                    if currentUser.pk != int(subUserId):
                        subuser = Subuser.objects.get(pk=subUserId)
                        subuser.status=constants.Inactive
                        subuser.save()
                        return JsonResponse({'status': 'success','success_msg': 'Successfully Removed'})
                    else:
                        return JsonResponse({'status': 'error','error_msg':'You cannot delete yourself'})
                else:
                    subuser = Subuser.objects.get(pk=subUserId)
                    subuser.status = constants.Inactive
                    subuser.save()
                    return JsonResponse({'status': 'success','success_msg': 'Successfully Removed'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get product list belongs to particular Purchase Product Catalog information and also get the product 
list that not belongs to the particular catalog by passing catalogId"""
@csrf_exempt
def productCatalogPurchaseViewDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        catalog = body['catalog']
        item = {}
        totalItems = []
        if 'view' in body:
            detailList = ProductCatalogForPurchaseDetails.objects.filter(
                productCatelogId_id=catalog, status=constants.Active
                                               ).values('itemName', 'itemCode', 'itemCategory__prtCatName',
                                                            'purchasePrice',
                                                            'purchaseCurrency__currencyTypeCode')
        else:
            excludeItems = ProductCatalogForPurchaseDetails.objects.filter(productCatelogId_id=catalog,
                                                                           status=constants.Active).values('itemCode')
            detailList =ItemMaster.objects.filter(~Q(productDetail=constants.Sale),status=constants.Active).\
                exclude(itemCode__in=excludeItems).values('itemName', 'itemCode', 'itemCategory__prtCatName',
                                                            'purchasingItem__purchasingPrice',
                                                            'purchasingItem__purchasingCurrency__currencyTypeCode')

        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No products found'})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Add product list to particular purcahse catalog by using catalogId"""
@csrf_exempt
def addNewProductCatalogPurchase(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                objectList = body['data']
                catalogId = body['catalogId']
                productCatalogPurchase = utilitySD.getPurchaseProductCatelogById(catalogId)
                for dictionaries in objectList:
                    masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                    try:
                        productCatalogPurchaseDet = ProductCatalogForPurchaseDetails.objects.get(
                            productCatelogId_id=catalogId,productId=masterItem,status=constants.Inactive)
                        productCatalogPurchaseDet.status = constants.Active
                    except:
                        productCatalogPurchaseDet = ProductCatalogForPurchaseDetails()
                    purchaseDetails = utilitySD.getPurchaseDetailsByProduct(masterItem)
                    productCatalogPurchaseDet.productCatelogId = productCatalogPurchase
                    productCatalogPurchaseDet.productId = masterItem
                    productCatalogPurchaseDet.itemCode = masterItem.itemCode
                    productCatalogPurchaseDet.itemName = masterItem.itemName
                    productCatalogPurchaseDet.itemCategory = masterItem.itemCategory
                    productCatalogPurchaseDet.alterItemCode = masterItem.alterItemCode
                    productCatalogPurchaseDet.alterItemName = masterItem.alterItemName
                    productCatalogPurchaseDet.purchaseUom = purchaseDetails.purchasingUom
                    productCatalogPurchaseDet.purchaseTax = purchaseDetails.purchasingTax
                    productCatalogPurchaseDet.purchasePrice = purchaseDetails.purchasingPrice
                    productCatalogPurchaseDet.purchaseCurrency = purchaseDetails.purchasingCurrency
                    productCatalogPurchaseDet.purchaseUomForKg = purchaseDetails.purchasingUomForKg
                    productCatalogPurchaseDet.save()
                    list1 = SupplierProductCatalog.objects.filter(productCatId=productCatalogPurchase,
                                                                  status=constants.Active).values('supplierId')
                    unique_supplier = []
                    for x in list1:
                        if x['supplierId'] not in unique_supplier:
                            unique_supplier.append(x['supplierId'])
                    for dictionaries in unique_supplier:
                        singleSupplier = utilitySD.getSupplierById(dictionaries)
                        try:
                            defaultSupplier = SupplierProductCatalog.objects.get(
                                productId=productCatalogPurchaseDet.productId,defaultSupplier=True)
                        except:
                            defaultSupplier = None
                        try:
                            supplierCatalog = SupplierProductCatalog.objects.get(
                                itemCode__iexact=productCatalogPurchaseDet.itemCode,supplierId=singleSupplier)
                            supplierCatalog.status = constants.Active
                            supplierCatalog.linked = False
                        except:
                            supplierCatalog = SupplierProductCatalog()
                            supplierCatalog.supplierId = singleSupplier
                        if defaultSupplier is None:
                            supplierCatalog.defaultSupplier = True
                        supplierCatalog.productId = productCatalogPurchaseDet.productId
                        supplierCatalog.productCatId_id = productCatalogPurchaseDet
                        saveSupplierCatalog(supplierCatalog, productCatalogPurchaseDet,
                                            productCatalogPurchaseDet.purchaseUom,
                                            productCatalogPurchaseDet.purchaseTax,
                                            productCatalogPurchaseDet.purchaseCurrency,
                                            productCatalogPurchaseDet.purchasePrice,
                                            productCatalogPurchaseDet.purchaseUomForKg,
                                            productCatalogPurchaseDet.purchasePrice, False)
                return JsonResponse(
                    {'status': 'success', 'success_msg': 'Product(s) added successfully to the purchase catalog'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Delete the particular product from particular purchase catalog by passing itemCode and catalogId"""
@csrf_exempt
def delProductFromCatalogPurchase(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                catalogId = body['catalogId']
                if 'itemCode' in body:
                    itemCode = body['itemCode']
                    productCat=ProductCatalogForPurchaseDetails.objects.get(productCatelogId_id=catalogId,
                                                                            itemCode=itemCode)
                    productCat.status = constants.Inactive
                    productCat.save()
                    SupplierProductCatalog.objects.filter(productCatId=productCat.productCatelogId,
                                                                  productId=productCat.productId,
                                                                  status=constants.Active).update(
                        status=constants.Inactive,linked = False,defaultSupplier = False)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Product removed succesfully from catalog'})
                else:
                    productCat = ProductCatalogForPurchase.objects.get(purPrdtCatId=catalogId)
                    productCat.status = constants.Inactive
                    productCat.save()
                    ProductCatalogForPurchaseDetails.objects.filter(productCatelogId=productCat).update(
                        status = constants.Inactive)
                    SupplierProductCatalog.objects.filter(productCatId_id=catalogId,
                                                          status=constants.Active).update(
                        status=constants.Inactive, linked=False, defaultSupplier=False)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Catalog removed succesfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get product list belongs to particular Sales Product Catalog information and also get the product 
list that not belongs to the particular catalog by passing catalogId"""
@csrf_exempt
def productCatalogSalesViewDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        catalog = body['catalog']
        item = {}
        totalItems = []
        if 'view' in body:
            detailList = ProductCatalogForSaleDetails.objects.filter(
                productCatelogId_id=catalog, status=constants.Active
                                               ).values('itemName', 'itemCode', 'itemCategory__prtCatName',
                                                            'salesPrice','discountPrice','discountPercentage',
                                                            'salesCurrency__currencyTypeCode','discountAbsolute')
        else:
            excludeItems = ProductCatalogForSaleDetails.objects.filter(productCatelogId_id=catalog,
                                                                           status=constants.Active).values('itemCode')
            detailList =ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),status=constants.Active).\
                exclude(itemCode__in=excludeItems).values('itemName', 'itemCode', 'itemCategory__prtCatName',
                                                            'salesItem__salesPrice',
                                                             'salesItem__salesCurrency__currencyTypeCode',
                                                             'baseUom__quantityTypeCode')

        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No products found'})
        # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Add product list to particular sales catalog by using catalogId"""
@csrf_exempt
def addNewProductCatalogSale(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, "editProductFromCatalogSale")
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                objectList = body['data']
                catalogId = body['catalogId']
                productCatalogSale = utilitySD.getSaleProductCatelogById(catalogId)
                currentSchema = connection.schema_name
                for dictionaries in objectList:
                    masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                    try:
                        productCatalogSaleDet = ProductCatalogForSaleDetails.objects.get(productCatelogId_id=catalogId,
                                                                                         productId=masterItem,
                                                                                         status=constants.Inactive)
                        productCatalogSaleDet.status = constants.Active
                    except:
                        productCatalogSaleDet = ProductCatalogForSaleDetails()
                    salesDetails = utilitySD.getSalesDetailsByProduct(masterItem)
                    productCatalogSaleDet.productCatelogId = productCatalogSale
                    productCatalogSaleDet.productId = masterItem
                    productCatalogSaleDet.itemCode = masterItem.itemCode
                    productCatalogSaleDet.itemName = masterItem.itemName
                    productCatalogSaleDet.itemCategory = masterItem.itemCategory
                    productCatalogSaleDet.alterItemCode = masterItem.alterItemCode
                    productCatalogSaleDet.alterItemName = masterItem.alterItemName
                    productCatalogSaleDet.salesUom = salesDetails.salesUom
                    productCatalogSaleDet.salesTax = salesDetails.salesTax
                    productCatalogSaleDet.salesPrice = salesDetails.salesPrice
                    productCatalogSaleDet.salesCurrency = salesDetails.salesCurrency
                    productCatalogSaleDet.salesUomForKg = salesDetails.salesUomForKg
                    productCatalogSaleDet.discountPercentage = dictionaries['discountPercentage']
                    productCatalogSaleDet.discountAbsolute = dictionaries['discountAbsolute']
                    productCatalogSaleDet.discountPrice = dictionaries['discountPrice']
                    productCatalogSaleDet.save()
                    list1 = CustomerProductCatalog.objects.filter(productCatId=productCatalogSale,
                                                                  status=constants.Active).values('customerId')
                    unique_customer = []
                    for x in list1:
                        if x['customerId'] not in unique_customer:
                            unique_customer.append(x['customerId'])
                    for dictionaries in unique_customer:
                        singleCustomer = utilitySD.getCustomerById(dictionaries)
                        try:
                            customerCatalog=CustomerProductCatalog.objects.get(itemCode=productCatalogSaleDet.itemCode,
                                                                                 customerId=singleCustomer)
                            itemSup = True
                        except:
                            customerCatalog = CustomerProductCatalog()
                            customerCatalog.customerId = singleCustomer
                            itemSup = False
                        customerCatalog.discountAbsolute = productCatalogSaleDet.discountAbsolute
                        customerCatalog.discountPercentage = productCatalogSaleDet.discountPercentage
                        customerCatalog.productId = productCatalogSaleDet.productId
                        customerCatalog.productCatId = productCatalogSale
                        saveCustomerCatalog(customerCatalog, productCatalogSaleDet, productCatalogSaleDet.salesUom,
                                            productCatalogSaleDet.salesTax,
                                            productCatalogSaleDet.salesCurrency,
                                            productCatalogSaleDet.salesPrice,
                                            productCatalogSaleDet.salesUomForKg, productCatalogSaleDet.discountPrice)

                        if singleCustomer.relationshipStatus:
                            userSchema = utility.getCompanyByCompanyCode(singleCustomer.cusCompanyCode).schemaName
                            connection.set_schema(schema_name=userSchema)
                            supplier = utilitySD.getSupplierByConnectionCode(singleCustomer.connectionCode)

                            if itemSup:
                                supplierCatalog = SupplierProductCatalog.objects.get(
                                    supplierItemCode=productCatalogSaleDet.itemCode,supplierId=supplier)
                            else:
                                supplierCatalog = SupplierProductCatalog()
                                supplierCatalog.supplierId = supplier
                                supplierCatalog.status = constants.Pending
                            saveSupplierCatalog(supplierCatalog, productCatalogSaleDet, productCatalogSaleDet.salesUom,
                                                productCatalogSaleDet.salesTax,
                                                productCatalogSaleDet.salesCurrency,
                                                productCatalogSaleDet.salesPrice,
                                                productCatalogSaleDet.salesUomForKg,
                                                productCatalogSaleDet.discountPrice, True)
                        desc = supplier.supCompanyName + " assigned a product to you "
                        types = constants.AssignProductForCustomer
                        mainView.notificationView(constants.Supplier, supplier.pk, desc, types,None,1)
                    connection.set_schema(schema_name=currentSchema)
                return JsonResponse(
                    {'status': 'success', 'success_msg': 'Product(s) added successfully to the purchase catalog'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def removeCatalogProductsFromBothEnd(customerCat,singleProduct):
    currentSchema = connection.schema_name
    for dictionaries in customerCat:
        customerCat = utilitySD.getCustomerCatalogById(dictionaries['customerCatId'])
        linkedStatus = customerCat.linked
        customerCat.status = constants.Inactive
        customerCat.linked = False
        customerCat.save()
        if customerCat.customerId.relationshipStatus and linkedStatus:
            userSchema = utility.getCompanyByCompanyCode(customerCat.customerId.cusCompanyCode).schemaName
            connection.set_schema(schema_name=userSchema)
            supplier = utilitySD.getSupplierByConnectionCode(customerCat.customerId.connectionCode)
            supplierCatalog = SupplierProductCatalog.objects.get(
                supplierItemCode=dictionaries['itemCode'], supplierId=supplier)
            supplierCatalog.status = constants.Inactive
            supplierCatalog.linked = False
            supplierCatalog.defaultSupplier = False
            supplierCatalog.save()
            defaultProduct = SupplierProductCatalog.objects.filter(itemCode__iexact=supplierCatalog.itemCode,
                                                                   status=constants.Active).order_by(
                'supplierCatId').values(
                'supplierCatId'
            )
            for oneSupplier in defaultProduct:
                SupplierProductCatalog.objects.filter(supplierCatId=oneSupplier['supplierCatId']).update(
                    defaultSupplier=True)
                break
            if singleProduct:
                desc = str(supplier.supCompanyName) + " vendor removed the access of " + str(
                    supplierCatalog.supplierItemName)
                types = constants.ItemRemoveForCustomer
                mainView.notificationView(constants.Supplier, supplier.supplierId, desc, types, None, 1)
            connection.set_schema(schema_name=currentSchema)


"""Delete the particular product from particular sales catalog by passing itemCode and catalogId"""
@csrf_exempt
def delProductFromCatalogSale(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                catalogId = body['catalogId']
                if 'itemCode' in body:
                    itemCode = body['itemCode']
                    productCat = ProductCatalogForSaleDetails.objects.get(productCatelogId_id=catalogId,
                                                                          itemCode=itemCode)
                    productCat.status = constants.Inactive
                    productCat.save()
                    customerCat = CustomerProductCatalog.objects.filter(productCatId=productCat.productCatelogId,
                                                                  productId=productCat.productId,
                                                                  status=constants.Active).values('customerCatId',
                                                                                                  'itemCode')
                    removeCatalogProductsFromBothEnd(customerCat,True)
                    return JsonResponse(
                         {'status': 'success', 'success_msg': 'Product removed succesfully from catalog'})
                else:
                    currentSchema = connection.schema_name
                    productCat = ProductCatalogForSale.objects.get(salePrdtCatId=catalogId)
                    productCat.status = constants.Inactive
                    productCat.save()
                    ProductCatalogForSaleDetails.objects.filter(productCatelogId=productCat).update(
                        status=constants.Inactive)
                    customerCat = CustomerProductCatalog.objects.filter(productCatId=productCat,
                                                                        status=constants.Active).values('customerCatId',
                                                                                                        'itemCode')
                    uniqueCustomer = CustomerProductCatalog.objects.filter(productCatId=productCat,
                                                                        status=constants.Active).values(
                        'customerId').distinct()
                    for singleCustomer in uniqueCustomer:
                        customer = utilitySD.getCustomerById(singleCustomer['customerId'])
                        if customer.relationshipStatus:
                            userSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                            connection.set_schema(schema_name=userSchema)
                            supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                            desc = str(supplier.supCompanyName) + " vendor removed the access of " + str(
                                productCat.catalogName) +" catalog"
                            types = constants.ItemRemoveForCustomer
                            mainView.notificationView(constants.Supplier, supplier.supplierId, desc, types, None, 1)
                            connection.set_schema(schema_name=currentSchema)
                    removeCatalogProductsFromBothEnd(customerCat, False)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': 'Catalog removed succesfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Update the particular product details from the sales catalog and the changes reflect to their customers if the 
catalog is assigned"""
@csrf_exempt
def editProductFromCatalogSale(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                itemCode = body['itemCode']
                catalogId = body['catalogId']
                currentSchema = connection.schema_name
                productCat = ProductCatalogForSaleDetails.objects.get(productCatelogId_id=catalogId, itemCode=itemCode)
                previousPrice = productCat.discountPrice
                currency = productCat.salesCurrency.currencyTypeCode
                productCat.discountPercentage = body['discountPercentage']
                productCat.discountAbsolute = body['discountAbsolute']
                productCat.discountPrice = body['discountPrice']
                productCat.save()
                CustomerProductCatalog.objects.filter(productCatId=productCat.productCatelogId,
                                                                    productId=productCat.productId,
                                                                    status=constants.Active).update(
                    discountPercentage=body['discountPercentage'],discountAbsolute = body['discountAbsolute'],
                    discountPrice=body['discountPrice'])
                if previousPrice != float(body['discountPrice']):
                    customerLisFromCat = CustomerProductCatalog.objects.filter(productCatId=productCat.productCatelogId,
                                                                        productId=productCat.productId,
                                                                        status=constants.Active).values('customerCatId')
                    for dictionaries in customerLisFromCat:
                         customerCat = utilitySD.getCustomerCatalogById(dictionaries['customerCatId'])
                         if customerCat.customerId.relationshipStatus:
                             userSchema = utility.getCompanyByCompanyCode(
                                 customerCat.customerId.cusCompanyCode).schemaName
                             connection.set_schema(schema_name=userSchema)
                             supplier = utilitySD.getSupplierByConnectionCode(customerCat.customerId.connectionCode)
                             supplierCatalog = SupplierProductCatalog.objects.get(supplierItemCode=productCat.itemCode,
                                                                              supplierId=supplier)
                             supplierCatalog.discountPrice = body['discountPrice']
                             supplierCatalog.save()
                             desc = str(supplier.supCompanyName) + " updated price in the catelog "\
                                    +str(productCat.productCatelogId.catalogName)\
                             +" "+str(previousPrice)+""+currency+" to "+str(body['discountPrice'])+""+currency
                             mainView.notificationView(constants.Supplier, supplier.pk, desc, "UpdatePriceCatelog ", None, 1)
                             connection.set_schema(schema_name=currentSchema)
                return JsonResponse(
                     {'status': 'success', 'success_msg': 'Sales catalog updated successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})

    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get all the notification details for the current schema"""
@csrf_exempt
def viewNotification(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        detailList = Notification.objects.filter(status=constants.Active).order_by('-createdDateTime').values()
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No Notification found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to create Role with request access permissions as array list"""
@csrf_exempt
def createRole(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                roleName = body['roleName']
                alreadyExistRole = utilitySD.getRoleByRoleName(roleName)
                if alreadyExistRole is None:
                    role = RolesAndAccess()
                    role.roleName = roleName
                    role.roleArray = body['roleArray']
                    role.save()
                    return JsonResponse({'status': 'success','success_msg':'Role created successfully','id': role.pk})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Role Name already exists!!.'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Update the particular role's request access information by using roleId"""
@csrf_exempt
def editRole(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                roleId = body['roleId']
                role = utilitySD.getRoleById(roleId)
                if role:
                    role.roleArray = body['roleArray']
                    role.save()
                    return JsonResponse({'status': 'success', 'success_msg': 'Role updated successfully'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Role not found'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Delete the particular role by using roleId"""
@csrf_exempt
def deleteRole(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                roleId = body['roleId']
                role = utilitySD.getRoleById(roleId)
                if role:
                    subUsersWithTheRole = Subuser.objects.filter(role = role,status = constants.Active)
                    if subUsersWithTheRole:
                        return JsonResponse({'status': 'error', 'error_msg': 'Cannot remove this role'})
                    else:
                        role.roleName = None
                        role.status = constants.Inactive
                        role.save()
                        return JsonResponse({'status': 'success', 'success_msg': 'Role deleted successfully'})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Role not found'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Create new site for not interrelation customers"""
@csrf_exempt
def createSitesForCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                customerId = body['customerId']
                siteName = body['siteName']
                customer = utilitySD.getCustomerById(customerId)
                alreadyExistSite = utilitySD.getCustomerSiteBySiteName(customer,siteName)
                if alreadyExistSite:
                    return JsonResponse({'status': 'error', 'error_msg': 'Site Name already exists!!'})
                else:
                    customerSite = CustomerSiteDetails()
                    customerSite.userCustSitesCompany = customer
                    customerSite.userCustSiteName = body['siteName']
                    customerSite.customer_country_id = body['country']
                    customerSite.customer_address_Line1 = body['address1']
                    customerSite.customer_address_Line2 = body['address2']
                    customerSite.customer_unit1 = body['unit1']
                    customerSite.customer_unit2 = body['unit2']
                    customerSite.customer_state_id = body['state']
                    customerSite.customer_postalCode = body['postalCode']
                    customerSite.save()
                    return JsonResponse({'status': 'success', 'success_msg': 'Site created successfully'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get serive level agreement details for the particular site by using siteId and supplierId"""
@csrf_exempt
def getAssignedSlaFromSupplier(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        supplierId = body['supplierId']
        siteId = body['siteId']
        try:
            supplierSla = SupplierSlaForSites.objects.get(userSupSitesCompany_id=supplierId,mappedSites_id=siteId,
                                              status=constants.Active)
        except:
            supplierSla = None
        if supplierSla:
            item = {}
            totalItems = []
            item['sla'] = supplierSla.slaFromSupplier
            if not supplierSla.selfCreation:
                item['link'] = supplierSla.linkedStatus
            else:
                item['link'] = True
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse({'status': 'error', 'error_msg': 'Oops!!Vendor has not assigned the SLA for this site!!'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to remove Interconnection between supplier and customer and the notification is sent to respective 
customer/supplier"""
@csrf_exempt
def disconnectTrader(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        currentSchema = connection.schema_name
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                mail = body['email']
                type = body['type']
                if type == constants.Customer:
                    customer = utilitySD.getCustomerByEmail(mail)
                    ordCount = OrderPlacementfromCustomer.objects.filter(customerId=customer)
                    ordStatus = OrderPlacementfromCustomer.objects.filter(customerId=customer,
                                                                          ordstatus=constants.Pending).values()
                    if ordCount.count() == 0 or ordStatus:
                        customer.relationshipStatus = False
                        customer.invitationStatus = 1
                        customer.save()
                        userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                        connection.set_schema(schema_name=userCustomerSchema)
                        supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                        supplier.relationshipStatus = False
                        supplier.invitationStatus = 1
                        supplier.save()
                        desc = userCompany.companyName + " disconnected the relationship"
                        mainView.notificationView(constants.Supplier, supplier.supplierId, desc, "DisconnectedSupplier",None,1)
                        connection.set_schema(schema_name=currentSchema)
                        return JsonResponse({'status': 'success', 'success_msg': 'Customer disconnected successfully'})
                    else:
                        return JsonResponse({'status': 'error', 'error_msg': 'Cannot disconnect this customer'})
                else:
                    supplier = utilitySD.getSupplierByEmail(mail)
                    ordCount = OrderPlacementtoSupplier.objects.filter(productId__supplierId=supplier)
                    ordStatus = OrderPlacementtoSupplier.objects.filter(productId__supplierId=supplier,
                                                                        ordstatus=constants.Pending).values()
                    if ordCount.count() == 0 or ordStatus:
                        supplier.relationshipStatus = False
                        supplier.invitationStatus = 1
                        supplier.save()
                        userCustomerSchema = utility.getCompanyByCompanyCode(supplier.supCompanyCode).schemaName
                        connection.set_schema(schema_name=userCustomerSchema)
                        customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                        customer.relationshipStatus = False
                        customer.invitationStatus = 1
                        customer.save()
                        desc = userCompany.companyName + " disconnected the relationship"
                        mainView.notificationView(constants.Customer, customer.customerId, desc, "DisconnectedCustomer", None, 1)
                        connection.set_schema(schema_name=currentSchema)
                        return JsonResponse({'status': 'success', 'success_msg': 'Vendor disconnected successfully'})
                    else:
                        return JsonResponse({'status': 'error', 'error_msg': 'Cannot disconnect this vendor'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to accept the particular Service level agreement assigned by the supplier by using siteId and supplierId
and the accepted notification us sent to supplier"""
@csrf_exempt
def acceptSlaFromSupplier(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                supplierId = body['supplierId']
                siteId = body['siteId']
                try:
                    supplierSla = SupplierSlaForSites.objects.get(mappedSites_id=siteId,
                                                                  userSupSitesCompany_id=supplierId,linkedStatus=False)
                except:
                    supplierSla = None
                if supplierSla:
                    supplierSla.linkedStatus = True
                    supplierSla.save()
                    supplier = utilitySD.getSupplierById(supplierId)
                    noti = utilitySD.getNotificationById(body['notiId'])
                    noti.viewed = constants.Yes
                    noti.save()
                    if supplier.relationshipStatus:
                        currentSchema = connection.schema_name
                        userCustomerSchema = utility.getCompanyByCompanyCode(supplier.supCompanyCode).schemaName
                        connection.set_schema(schema_name=userCustomerSchema)
                        customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                        try:
                            customerSite = CustomerSiteDetails.objects.get(userCustSiteId__iexact=siteId,
                                                                           userCustSitesCompany=customer)
                        except:
                            customerSite  = None
                        if customerSite:
                            customerSite.linkedStatus = True
                            customerSite.selfCreation = False
                            mainView.notificationView(constants.Customer, customer.customerId,
                                                      str(customer.cusCompanyName)+" accepted the assigned Sla for "
                                                      +customerSite.userCustSiteName, "AcceptSLA", None, 1)
                            customerSite.save()
                        connection.set_schema(schema_name=currentSchema)
                        noti = utilitySD.getNotificationById(body['notiId'])
                        noti.viewed = constants.Yes
                        noti.save()
                    return JsonResponse(
                        {'status': 'success', 'success_msg': "Sla accepted successfully"})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Sla not found'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to reject the particular Service level agreement assigned by the supplier by using siteId and supplierId
and the rejected notification us sent to supplier"""
@csrf_exempt
def rejectSlaFromSupplier(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                supplierId = body['supplierId']
                siteId = body['siteId']
                try:
                    supplierSla = SupplierSlaForSites.objects.get(mappedSites_id=siteId,
                                                                  userSupSitesCompany_id=supplierId,linkedStatus=False)
                except:
                    supplierSla = None
                if supplierSla:
                    supplierSla.linkedStatus = False
                    supplierSla.status = constants.Reject
                    supplierSla.save()
                    supplier = utilitySD.getSupplierById(supplierId)
                    if supplier.relationshipStatus:
                        currentSchema = connection.schema_name
                        userCustomerSchema = utility.getCompanyByCompanyCode(supplier.supCompanyCode).schemaName
                        connection.set_schema(schema_name=userCustomerSchema)
                        customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                        try:
                            customerSite = CustomerSiteDetails.objects.get(userCustSiteId__iexact=siteId,
                                                                           userCustSitesCompany=customer)
                        except:
                            customerSite  = None
                        if customerSite:
                            customerSite.linkedStatus = False
                            customerSite.mappedSites = None
                            mainView.notificationView(constants.Customer, customer.customerId,
                                                      str(customer.cusCompanyName) + " rejected the assigned Sla for "
                                                      +customerSite.userCustSiteName, "RejectSLA", None, 1)
                            customerSite.save()
                        connection.set_schema(schema_name=currentSchema)
                    return JsonResponse(
                        {'status': 'success', 'success_msg': "Sla rejected successfully"})
                else:
                    return JsonResponse({'status': 'error', 'error_msg': 'Sla not found'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def updateCustomer(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
            mainUser = utility.getUserByCompanyId(userCompany)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                userCompanyName = userCompany.companyName
                email = mainUser.email
                #emailId = request.POST['cusEmail'].lower()
                emailId = request.POST['cusEmailData'].lower()
                # get the contact number from the submitted form
                contactNumber = request.POST['cusContactNo']
                # get the company name from the submitted form
                companyName = request.POST['cusCompanyName']
                cusCommunicationEmail = request.POST['cusCommunicationEmail'].lower()
                cusAlterNateEmail = request.POST['cusAlterNateEmail'].lower()

                # check entered and user email are same
                if email != emailId and userCompanyName.lower() != companyName.lower():
                    customer = utilitySD.getCustomerByEmail(emailId)
                    # check entered user is already exists in our system
                    contactNumberCheck = Customer.objects.filter(~Q(customerId=customer.pk),
                                                                 cusContactNo = contactNumber,status=constants.Active)
                    companyNameCheck = Customer.objects.filter(~Q(customerId=customer.pk),
                                                       cusCompanyName__iexact = companyName,status=constants.Active)
                    if contactNumberCheck:
                        return JsonResponse(
                            {'status': 'error', 'error_msg': 'Entered Contact number already exist in your system'})
                    elif companyNameCheck:
                        return JsonResponse({'status': 'error',
                                             'error_msg': 'Entered Company name already exist in your system'})
                    else:
                        customerDetailSave(customer,companyName,request.POST['cusCountry'],
                                           request.POST['cusAddress_Line1'],request.POST['cusAddress_Line2'],
                                           request.POST['cusUnit1'],request.POST['cusUnit2'],request.POST['cusState'],
                                           request.POST['cusPostalCode'],request.POST['contactPerson'],
                                           emailId,request.POST['cusCountryCode'],request.POST['cusContactNo'],
                                           customer.invitationStatus,cusAlterNateEmail,cusCommunicationEmail)
                        # save the customer/supplier info
                        customerShipping = CustomerShippingAddress.objects.get(shippingCustomer=customer)
                        customerShippingAddressSave(customerShipping, request.POST['cusShipAddress_Line1'],
                                                    request.POST['cusShipAddress_Line2'], request.POST['cusShipUnit1'],
                                                    request.POST['cusShipUnit2'],
                                                    request.POST['cusShipCountry'],
                                                    request.POST['cusShipState'], request.POST['cusShipPostalCode'])
                        return JsonResponse({'status': 'success',
                                             'success_msg': 'Customer details updated successfully'})
                elif email == emailId:
                    return JsonResponse({'status': 'error',
                                         'error_msg': 'Oops! You cannot suppose to use your email to the customer'})
                else:
                    return JsonResponse(
                        {'status': 'error',
                         'error_msg': 'Oops! You cannot suppose to use your company name to the customer'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def updateSupplier(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
            mainUser = utility.getUserByCompanyId(userCompany)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                userCompanyName = userCompany.companyName
                email = mainUser.email
                emailId = request.POST['supEmailData'].lower()
                # get the contact number from the submitted form
                contactNumber = request.POST['supContactNo']
                # get the company name from the submitted form
                companyName = request.POST['supCompanyName']
                supCommunicationEmail = request.POST['supCommunicationEmail'].lower()
                supAlterNateEmail = request.POST['supAlterNateEmail'].lower()
                # check entered and user email are same
                if email != emailId and userCompanyName.lower() != companyName.lower():
                    supplier = utilitySD.getSupplierByEmail(emailId)
                    # check entered user is already exists in our system
                    contactNumberCheck = Supplier.objects.filter(~Q(supplierId=supplier.pk),
                                                                 supContactNo=contactNumber,status=constants.Active)
                    companyNameCheck = Supplier.objects.filter(~Q(supplierId=supplier.pk),
                                                          supCompanyName__iexact=companyName,status=constants.Active)
                    if contactNumberCheck:
                        return JsonResponse(
                            {'status': 'error', 'error_msg': 'Entered Contact number already exist in your system'})
                    elif companyNameCheck:
                        return JsonResponse(
                            {'status': 'error', 'error_msg': 'Entered Company name already exist in your system'})
                    else:
                        supplierDetailSave(supplier, companyName, request.POST['supCountry'],
                                                   request.POST['supAddress_Line1'],
                                                   request.POST['supAddress_Line2'], request.POST['supUnit1'],
                                                   request.POST['supUnit2'],
                                                   request.POST['supState'], request.POST['supPostalCode'],
                                                   request.POST['supContactPerson'],
                                                   emailId, request.POST['supCountryCode'],request.POST['supContactNo'],
                                           supplier.invitationStatus, supAlterNateEmail, supCommunicationEmail)
                        # save the customer/supplier info
                        supplierShipping = SupplierShippingAddress.objects.get(shippingSupplier=supplier)
                        supplierShippingAddressSave(supplierShipping, request.POST['supShipAddress_Line1'],
                                                    request.POST['supShipAddress_Line2'],
                                                    request.POST['supShipUnit1'], request.POST['supShipUnit2'],
                                                    request.POST['supShipCountry'],
                                                    request.POST['supShipState'], request.POST['supShipPostalCode'])
                        return JsonResponse({'status': 'success',
                                             'success_msg': 'Vendor details updated successfully'})
                elif email == emailId:
                    return JsonResponse(
                        {'status': 'error', 'error_msg': 'Oops! You cannot suppose to use your email to the customer'})
                else:
                    return JsonResponse(
                        {'status': 'error',
                         'error_msg': 'Oops! You cannot suppose to use your company name to the customer'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})



"""Method is to check the company code is exists in the system or not by using companyCode"""
def companyCodeIsExists(request):
    if ('user' in request.session or 'subUser' in request.session):
        if 'code' in request.GET:
            code = request.GET['code']
            company = utility.getCompanyByCompanyCode(code)
            if company and company.schemaName != connection.schema_name:
                return JsonResponse(
                    {'status': 'success', 'success_msg': 'Successful'})
            elif company:
                return JsonResponse(
                    {'status': 'error', 'error_msg': 'Oops! You cannot suppose to use your company code'})
            else:
                return JsonResponse(
                    {'status': 'error',
                     'error_msg': 'Entered Company code doesnot exists!!!'})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'Please enter company code'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to suspend or activate the current plan"""
@csrf_exempt
def planSuspend(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        userCompany = utility.getCompanyBySchemaName(connection.schema_name)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            account.planSuspended = True
            account.save()
            return JsonResponse(
                {'status': 'success', 'success_msg': "Successfully suspended"})
        else:
            account.planSuspended = False
            account.save()
            return JsonResponse(
                {'status': 'success', 'success_msg': "Successfully activated"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def listOfItemByitemCodeAndSupplierId(request):
    if 'user' in request.session or 'subUser' in request.session:
        itemList = []
        item = {}
        totalItems = []
        a = request.body.decode('utf-8')
        body = json.loads(a)
        itemCode = body['itemCode']
        supplierId = body['supplierId']
        itemDefaultList = SupplierProductCatalog.objects.filter(supplierId_id=supplierId,
                                                         itemCode=itemCode).values(
                    'itemCode', 'itemName', 'itemCategory', 'itemCategory__prtCatName','supplierId__supCompanyName'
            , price=F('discountPrice'),
                    relId_id=F('supplierId'), priceUnit__type=F(
                        'purchaseCurrency__currencyTypeCode'), uOm__type=F('purchaseUom__quantityTypeCode'),
                    id=F('supplierCatId'))
        for items in itemDefaultList:
            subItems = {}
            defaultList = items
            subItems['itemSup'] = []
            defaultList.update(subItems)
            itemList.append(defaultList)
        if itemList:
            item["totalItem"] = list(itemList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No vendor found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def checkSetAsView(request):
   a = request.body.decode('utf-8')
   body = json.loads(a)
   masterItemCode = utilitySD.getProductByItemCode(body['itemCode'])
   masterItemName = utilitySD.getProductByItemName(body['itemName'])
   if masterItemCode or masterItemName:
      return JsonResponse(
           {'status': 'success'})
   else:
       return JsonResponse(
           {'status': 'error'})


@csrf_exempt
def saveModuleDataInSession(request):
    a = request.body.decode('utf-8')
    body = json.loads(a)
    request.session['moduleData'] = body
    return JsonResponse(
    {'status': 'success', 'success_msg': 'success'})

@csrf_exempt
def addOnModulesSave(request):
    if ('user' in request.session or 'subUser' in request.session):
        userCompany = utility.getCompanyBySchemaName(connection.schema_name)
        account = utility.getoTAccountByCompany(userCompany)
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
            mainUser = utility.getUserByCompanyId(userCompany)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                try:
                    data = request.session['moduleData']
                    unit = data["moduleUnit"]
                    sumofprice = int(data["sumofModulePrice"]) * 100
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    stripe.Charge.create(
                        amount=int(sumofprice),
                        currency=unit,
                        description='A Django charge',
                        source=request.POST['stripeToken']
                    )
                    planFeatures = Plan.objects.get(planId=account.plan_Id.planId)
                    planFeatures.planFeaturesJson['Sale Order'] = 50
                    planFeatures.save()
                    modulePlan = data['moduleAllData']
                    moduleSaving = addOnModule.objects.get(otAccountDetail=account)
                    for a in modulePlan:
                        x = Module.objects.get(moduleId=a['moduleId'])
                        moduleSaving.modulesAccess.add(x)
                        moduleSaving.save()
                    messages.success(request, 'Payment Successfully Completed')
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
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def fetchModulesNotSubsribe(request):
    if ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
        account = utility.getoTAccountByCompany(userCompany)
        subscribed =  addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
        excludeSubscribe = Module.objects.exclude(moduleId__in=subscribed).values('moduleId')
        subList = []
        for notSub in excludeSubscribe:
            module = Module.objects.filter(moduleId=notSub['moduleId']).values('moduleId', 'moduleName',
                                                                                 'modulePrice','modulePriceUnit__currencyTypeCode')
            defaultList = list(module)
            defaultList[0]['status'] = "unsubscribe"
            subList.append(defaultList)
        return JsonResponse(
            {'status': 'success', 'totalItems': subList})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

def fetchModulesSubsribe(request):
    if ('user' in request.session or 'subUser' in request.session):
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
        account = utility.getoTAccountByCompany(userCompany)
        subscribed =  addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
        excludeSubscribe = Module.objects.exclude(moduleId__in=subscribed).values('moduleId')
        subList = []
        for sub in subscribed:
            module = Module.objects.filter(moduleId=sub['modulesAccess']).values('moduleId', 'moduleName',
                                                                                 'modulePrice',
                                                                                 'modulePriceUnit__currencyTypeCode')
            defaultList = list(module)
            defaultList[0]['status'] = "subscribe"
            subList.append(defaultList)
        return JsonResponse(
            {'status': 'success', 'totalItems': subList})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def modulePaymentGateway(request):
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
            else:
                notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
                lengTh = len(notiFy)
            data = request.session['moduleData']
            unit = data["moduleUnit"]
            sumofprice = data["sumofModulePrice"]
            sumoftotalprice = int(data["sumofModulePrice"])*100
            moduleData = data["moduleData"]
            key = settings.STRIPE_PUBLISHABLE_KEY
            return render(request, 'modulePaymentGateway.html',
                          {'company': company, 'urls': list(urls), 'profileForm': profileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                           'noti': notiFy,'key':key,'moduleData':moduleData,'sumofprice':sumofprice,
                           'sumoftotalprice':sumoftotalprice,'unit':unit,
                           'leng': lengTh, 'user': currentUser, 'status': company.urlchanged})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')

@csrf_exempt
def removeOnModulesSave(request):
    if ('user' in request.session or 'subUser' in request.session):
        userCompany = utility.getCompanyBySchemaName(connection.schema_name)
        account = utility.getoTAccountByCompany(userCompany)
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
            mainUser = utility.getUserByCompanyId(userCompany)
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                moduleSaving = addOnModule.objects.filter(otAccountDetail=account).values('modulesAccess')
                if len(moduleSaving) < 3:
                    planFeatures = Plan.objects.get(planId=account.plan_Id.planId)
                    planFeatures.planFeaturesJson['Sale Order'] = 0
                    planFeatures.save()
                    try:
                        salesOrdId = upgradeFeatures.objects.get(categoryDetail="Sale Order")
                        addonFeatures.objects.get(otAccountDetail=account,featuresDetails=salesOrdId).delete()
                    except:
                        pass
                moduleData = body['moduleData']
                moduleSaving = addOnModule.objects.get(otAccountDetail=account)
                for a in moduleData:
                    x = Module.objects.get(moduleId=a['moduleId'])
                    moduleSaving.modulesAccess.remove(x)
                    moduleSaving.save()
                return JsonResponse(
                    {'status': 'success'})

        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def disableOrActiveSubUser(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        type = body['type']
        subuserId = body['subUserId']
        if type == constants.Disable:
            subUserData = Subuser.objects.get(subUserId=subuserId)
            subUserData.status = constants.Disable
            subUserData.save()
        else:
            subUserData = Subuser.objects.get(subUserId=subuserId)
            subUserData.status = constants.Active
            subUserData.save()
        return JsonResponse(
            {'status': 'success', 'success_msg': 'success'})

    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

