from django.shortcuts import render
from django.http import  HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from OrderTangoSubDomainApp.forms import *
from OrderTangoSubDomainApp import utilitySD
from OrderTangoApp import utility
from OrderTangoApp import views as mainView
from OrderTangoApp.tokens import account_activation_token
from django.template.loader import render_to_string
import csv,datetime
from django.utils.encoding import force_bytes
import uuid,  io, json
from django.db.models import Q, F
from django.contrib import messages
from django.utils.http import  urlsafe_base64_decode,urlsafe_base64_encode
from OrderTangoApp.forms import *
from django.utils.encoding import  force_text
from OrderTangoOrdermgmtApp.models import OrderPlacementtoSupplier
from OrderTangoOrderFulfilmtApp.models import OrderPlacementfromCustomer,OrderDetails


def customerSave(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        # get the current user
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            # get the current user company name
            userCompany = currentUser.userCompanyId
            userCompanyName = userCompany.companyName
            token = currentUser.token
            email = currentUser.email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            # get the current user company name
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            userCompanyName = userCompany.companyName
            mainUser = utility.getUserByCompanyId(userCompany)
            token = mainUser.token
            email = mainUser.email
        # get the customer/supplier email from the submitted form
        emailId = request.POST['cusEmail'].lower()
        # get the contact number from the submitted form
        contactNumber = request.POST['cusContactNo']
        # get the company name from the submitted form
        companyName = request.POST['cusCompanyName']
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
        valiadtions = csvFieldValidation(emailId, contactNumber, key['country'], key['state'], usradd_country,
                                         usradd_state,postalCode,shippingPostalCode, b,request.POST['cusAlterNateEmail'].lower())
        # check entered and user email are same
        if email != emailId:
            if valiadtions is True:
                # check entered user is already exists in our system
                trader = alreadyExistCustomerOrSupplier(emailId, contactNumber, companyName, constants.Customer)
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
                        temp = views.fuzzyCompanyName(companyName, key['country'], key['state'], request.POST['cusPostalCode'],
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
                        customer.customerCode = utility.oTtradersCodeGenerator(userCompanyName, constants.Customer)
                        invitationStatus = 0
                        if request.POST.getlist('emailSent'):
                            url = settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT + '/subscription/?wsid=' + token + constants.C
                            mainView.sendingEmail(request, customer, request.POST['cusAlterNateEmail'].lower(), userCompanyName, 'traders_adding_email.html',
                                         userCompanyName + ' invite you to join in OrderTango',
                                         url, None, None)
                            invitationStatus = 1
                        customerDetailSave(customer,companyName,request.POST['cusCountry'],request.POST['cusAddress_Line1'],
                            request.POST['cusAddress_Line2'],request.POST['cusUnit1'],request.POST['cusUnit2'],
                                           request.POST['cusState'],request.POST['cusPostalCode'],request.POST['contactPerson'],
                                           emailId,request.POST['cusCountryCode'],request.POST['cusContactNo'],
                                           invitationStatus,request.POST['cusAlterNateEmail'])
                        # save the customer/supplier info
                        customerShipping = CustomerShippingAddress()
                        customerShipping.shippingCustomer =customer
                        if 'sameAddress' in request.POST:
                            customerShippingAddressSave(customerShipping, customer.cusAddress_Line1, customer.cusAddress_Line2, customer.cusUnit1, customer.cusUnit2, customer.cusCountry_id,
                                                        customer.cusState_id, customer.cusPostalCode)
                        else:
                            customerShippingAddressSave(customerShipping, request.POST['cusShipAddress_Line1'],
                                                        request.POST['cusShipAddress_Line2'], request.POST['cusShipUnit1'], request.POST['cusShipUnit2'],
                                                        request.POST['cusShipCountry'],
                                                        request.POST['cusShipState'], request.POST['cusShipPostalCode'])
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
            return JsonResponse({'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
        # no matched data or validation failures it will show success message
        else:
            return JsonResponse({'status': 'success', 'success_msg': 'Customer added successfully'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def customerDetailSave(customer,companyName,country,address1,address2,unit1,unit2,
                        state,postalCode,contactPerson,email,countryCode,contactNo,invitationStatus,alternateEmail):
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
    customer.cusAlterNateEmail = alternateEmail
    customer.save()


def customerShippingAddressSave(customerAddress,address1,address2,unit1,unit2,country,state,postalCode):
    customerAddress.cusShipAddress_Line1=address1
    customerAddress.cusShipAddress_Line2=address2
    customerAddress.cusShipUnit1=unit1
    customerAddress.cusShipUnit2=unit2
    customerAddress.cusShipCountry_id=country
    customerAddress.cusShipState_id=state
    customerAddress.cusShipPostalCode=postalCode
    customerAddress.save()


def supplierSave(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        # get the current user
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            # get the current user company name
            userCompany = currentUser.userCompanyId
            userCompanyName = userCompany.companyName
            token = currentUser.token
            email = currentUser.email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            # get the current user company name
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            userCompanyName = userCompany.companyName
            mainUser = utility.getUserByCompanyId(userCompany)
            token = mainUser.token
            email = mainUser.email
        # get the customer/supplier email from the submitted form
        emailId = request.POST['supEmail'].lower()
        # get the contact number from the submitted form
        contactNumber = request.POST['supContactNo']
        # get the company name from the submitted form
        companyName = request.POST['supCompanyName']
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
        valiadtions = csvFieldValidation(emailId, contactNumber, key['country'], key['state'], usradd_country,
                                         usradd_state,postalCode,shippingPostalCode
                                         ,b,request.POST['supAlterNateEmail'].lower())
        # check entered and user email are same
        if email != emailId:
            if valiadtions is True:
                # check entered user is already exists in our system
                trader = alreadyExistCustomerOrSupplier(emailId, contactNumber, companyName, constants.Supplier)
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
                        temp = views.fuzzyCompanyName(companyName, key['country'], key['state'], request.POST['supPostalCode'],
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
                        supplier.supplierCode = utility.oTtradersCodeGenerator(userCompanyName, constants.Supplier)
                        invitationStatus = 0
                        if request.POST.getlist('supEmailSent'):
                            url = settings.HTTP + settings.LOCAL_HOST + ':' + settings.PORT + '/subscription/?wsid=' + token + constants.S
                            mainView.sendingEmail(request, supplier, request.POST['supAlterNateEmail'].lower(), userCompanyName, 'traders_adding_email.html',
                                          userCompanyName + ' invite you to join in OrderTango',
                                         url, None, None)
                            invitationStatus = 1
                        supplierDetailSave(supplier, companyName, request.POST['supCountry'],
                                           request.POST['supAddress_Line1'],
                                           request.POST['supAddress_Line2'], request.POST['supUnit1'],
                                           request.POST['supUnit2'],
                                           request.POST['supState'], request.POST['supPostalCode'],
                                           request.POST['supContactPerson'],
                                           emailId, request.POST['supCountryCode'], request.POST['supContactNo'],
                                           invitationStatus,request.POST['supAlterNateEmail'].lower())

                        supplierShipping = SupplierShippingAddress()
                        supplierShipping.shippingSupplier =supplier
                        if 'supSameAddress' in request.POST:
                            supplierShippingAddressSave(supplierShipping, supplier.supAddress_Line1, supplier.supAddress_Line2, supplier.supUnit1, supplier.supUnit2, supplier.supCountry_id,
                                                        supplier.supState_id, supplier.supPostalCode)
                        else:
                            supplierShippingAddressSave(supplierShipping, request.POST['supShipAddress_Line1'],
                                                        request.POST['supShipAddress_Line2'], request.POST['supShipUnit1'], request.POST['supShipUnit2'],
                                                        request.POST['supShipCountry'],
                                                        request.POST['supShipState'], request.POST['supShipPostalCode'])
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
            return JsonResponse({'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
        # no matched data or validation failures it will show success message
        else:
            return JsonResponse({'status': 'success', 'success_msg': 'Supplier added successfully'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

def supplierDetailSave(supplier,companyName,country,address1,address2,unit1,unit2,
                        state,postalCode,contactPerson,email,countryCode,contactNo,invitationStatus,alternateEmail):
    supplier.supCompanyName = companyName
    supplier.supCountry_id = country
    supplier.supAddress_Line1 = address1
    supplier.supAddress_Line2 = address2
    supplier.supUnit1 = unit1
    supplier.supUnit2 = unit2
    supplier.supState_id = state
    supplier.supPostalCode = postalCode
    supplier.suptactPerson = contactPerson
    supplier.supEmail = email
    supplier.supCountryCode_id = countryCode
    supplier.supContactNo = contactNo
    supplier.invitationStatus = invitationStatus
    supplier.supAlterNateEmail = alternateEmail
    supplier.save()

def supplierShippingAddressSave(supplierAddress,address1,address2,unit1,unit2,country,state,postalCode):
    supplierAddress.supShipAddress_Line1=address1
    supplierAddress.supShipAddress_Line2=address2
    supplierAddress.supShipUnit1=unit1
    supplierAddress.supShipUnit2=unit2
    supplierAddress.supShipCountry_id=country
    supplierAddress.supShipState_id=state
    supplierAddress.supShipPostalCode=postalCode
    supplierAddress.save()


def alreadyExistCustomerOrSupplier(email,contactNo,companyName,type):
    try:
        UserTrader = None
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
                    customerObject.status = constants.Active
                    customerObject.save()
                    UserTrader = None
                    add = customerObject
        else:
            supplierObject = utilitySD.getSupplierByEmail(email)
            if supplierObject is None:
                supplierObject = utilitySD.getSupplierByContactNo(contactNo)
            if supplierObject is None:
                supplierObject = utilitySD.getSupplierByCompanyName(companyName)
            UserTrader = supplierObject
            if supplierObject:
                if supplierObject.status == constants.Inactive:
                    supplierObject.status = constants.Active
                    supplierObject.save()
                    UserTrader = None
                    add = supplierObject

    except:
        UserTrader = None
        add = None
    return UserTrader, add

def addInvitedCustomerOrSupplier(wsid,companyName):
    token = wsid[:-1]
    user = utility.getUserByToken(token)
    company = user.userCompanyId
    if wsid[-1] == constants.C:
        supplier = Supplier()
        supplier.supplierCode = utility.oTtradersCodeGenerator(companyName, constants.Supplier)
        supplierDetailSave(supplier, company.companyName, company.country_id,
                           company.address_Line1,company.address_Line2,company.unit1,
                           company.unit2,company.state_id,company.postalCode,'',user.email,user.countryCode_id,user.contactNo,1,user.email
                           )


    else:
        customer = Customer()
        customer.customerCode = utility.oTtradersCodeGenerator(companyName, constants.Customer)
        customerDetailSave(customer, company.companyName, company.country_id,
                           company.address_Line1, company.address_Line2, company.unit1,
                           company.unit2, company.state_id,company.postalCode, '', user.email, user.countryCode_id, user.contactNo, 1,user.email
                           )


# customer or supplier adding method using csv
def customerOrSupplierCsvSave(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        try:
            if 'user' in request.session:
                currentUser = utility.getObjectFromSession(request, 'user')
                # get the current user company name
                userCompany = currentUser.userCompanyId
                email = currentUser.email
            if 'subUser' in request.session:
                currentUser = utility.getObjectFromSession(request, 'subUser')
                # get the current user company name
                userCompany = utility.getCompanyBySchemaName(connection.schema_name)
                email = utility.getUserByCompanyId(userCompany).email
            # get the csv file
            inputCsv = request.FILES.get('myfile', False)
            # read the csv file as IextIO and make the text as object using DictReader
            listCsv = list(csv.DictReader(io.TextIOWrapper(inputCsv)))
            # takes an object and produces a string
            dumps = json.dumps(listCsv)
            # would take a file-like object, read the data from that object, and use that string to create an object
            usersFromCsv = json.loads(dumps)
            # get the type of the trader
            type = request.POST['type'].lower()
            resultSet = []
            resultAlreadyExistSet = []
            resultSuccessfulSet = []
            userCompanyName = userCompany.companyName
            # check the csv file has data
            if len(usersFromCsv) > 0:
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
                        a["currentData"] = {'email':emailId,'country':country,'state':state,'contactNo':contactNumber,
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
                                                     b,customerOrsupplier['ALTERNATE_EMAIL'].lower())
                    # check entered and user email are same
                    if email != emailId:
                        if valiadtions is True:
                            # check customer/supplier is already exists in our system
                            trader = alreadyExistCustomerOrSupplier(emailId, contactNumber, companyName, type)
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
                                                            customerOrsupplier['UNIT1'], customerOrsupplier['UNIT2'],
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
                                        user_Country = Country.objects.get(countryName__iexact=usradd_country)
                                    except:
                                        user_Country = ''
                                    try:
                                        user_State = State.objects.get(stateName__iexact=usradd_state)
                                    except:
                                        user_State = user_Country
                                    if type==constants.Customer:
                                        customer= Customer()
                                        customer.customerCode = utility.oTtradersCodeGenerator(userCompanyName,
                                                                                                 constants.Customer)
                                        customerDetailSave(customer,companyName,Country.objects.get(countryName__iexact=country).countryId,
                                                           customerOrsupplier['ADDRESS1'],customerOrsupplier['ADDRESS2'],
                                                           customerOrsupplier['UNIT1'],customerOrsupplier['UNIT2'],
                                                           State.objects.get(stateName__iexact=state).stateId,
                                                           customerOrsupplier['POSTAL_CODE'],customerOrsupplier['CONTACT_PERSON'],
                                                           emailId,
                                                           CountryCode.objects.get(countryCodeType=
                                                                    customerOrsupplier['COUNTRY_CODE'].replace('+', '')).countryCodeId,
                                                           contactNumber,0,customerOrsupplier['ALTERNATE_EMAIL'].lower())

                                        if user_Country != '' and user_State != '':
                                            customerAddress = CustomerShippingAddress()
                                            customerAddress.shippingCustomer = customer
                                            customerShippingAddressSave(customerAddress, customerOrsupplier['SHIPPING_ADDRESS1'],
                                                                        customerOrsupplier['SHIPPING_ADDRESS2'], customerOrsupplier['SHIPPING_UNIT1'],
                                                                        customerOrsupplier['SHIPPING_UNIT2'],
                                                                        user_Country.countryId,
                                                                        user_State.stateId
                                                                        , customerOrsupplier['SHIPPING_POSTAL_CODE'])
                                    else:
                                        supplier = Supplier()
                                        supplier.supplierCode = utility.oTtradersCodeGenerator(userCompanyName,
                                                                                                 constants.Supplier)
                                        supplierDetailSave(supplier, companyName,
                                                           Country.objects.get(countryName__iexact=country).countryId,
                                                           customerOrsupplier['ADDRESS1'],
                                                           customerOrsupplier['ADDRESS2'],
                                                           customerOrsupplier['UNIT1'], customerOrsupplier['UNIT2'],
                                                           State.objects.get(stateName__iexact=state).stateId,
                                                           customerOrsupplier['POSTAL_CODE'],
                                                           customerOrsupplier['CONTACT_PERSON'],
                                                           emailId,
                                                           CountryCode.objects.get(countryCodeType=
                                                                                   customerOrsupplier[
                                                                                       'COUNTRY_CODE'].replace('+',
                                                                                                               '')).countryCodeId,
                                                           contactNumber, 0,customerOrsupplier['ALTERNATE_EMAIL'].lower())

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
                    errormessages = errormessage(type, resultSet, resultAlreadyExistSet + resultSuccessfulSet, "")
                    return JsonResponse(
                        {'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
                # no matched data or validation failures it will show success message
                else:
                    return JsonResponse({'status': 'success', 'success_msg': type + '(s) were added successfully'})
            # csv is empty
            else:
                return JsonResponse(
                    {'status': 'showerror', 'error_msg': 'Please upload csv with data'})
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

# add the existing customer/supplier into the system
def addExistingCustomerOrSupplier(request):
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
        status = request.POST['status']
        traderUser = utility.getUserByEmail(emailId)
        traderCompany = traderUser.userCompanyId
        # check the customer or supplier already exists in the system
        trader = alreadyExistCustomerOrSupplier(emailId, traderUser.contactNo, traderCompany.companyName, type)
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
                    customer.customerCode = utility.oTtradersCodeGenerator(userCompanyName, constants.Customer)
                    customer.connectionCode = wsid
                    customerDetailSave(customer, traderCompany.companyName, traderCompany.country_id,
                                       traderCompany.address_Line1, traderCompany.address_Line2, traderCompany.unit1,
                                       traderCompany.unit2, traderCompany.state_id, traderCompany.postalCode, '',
                                       traderUser.email,
                                       traderUser.countryCode_id, traderUser.contactNo, invitationStatus,traderUser.email
                                       )
                    mainUrl = "/acceptSupplier"
                else:
                    supplier = Supplier()
                    if trader[1]:
                        supplier = trader[1]
                    supplier.connectionCode = wsid
                    supplier.supplierCode = utility.oTtradersCodeGenerator(userCompanyName, constants.Supplier)
                    supplierDetailSave(supplier, traderCompany.companyName, traderCompany.country_id,
                                       traderCompany.address_Line1, traderCompany.address_Line2, traderCompany.unit1,
                                       traderCompany.unit2, traderCompany.state_id, traderCompany.postalCode, '',
                                       traderUser.email,
                                       traderUser.countryCode_id, traderUser.contactNo, invitationStatus,traderUser.email
                                       )
                    mainUrl = "/acceptCustomer"
                # send mail to the customer/supplier
                if mailSent:
                    currentSchema = connection.schema_name
                    connection.set_schema(schema_name=traderCompany.schemaName)
                    uid = urlsafe_base64_encode(force_bytes(mainUser.pk)).decode()
                    token = account_activation_token.make_token(mainUser)
                    url = mainUrl+"/"+uid+"/"+token+"/?wsid="+wsid
                    mainView.notificationView(request,url,userCompanyName + " added you as a " + type,"href")
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
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})



# validating the csv fields
def csvFieldValidation(emailId, contactNumber, country, state, shippingCountry, shippingState,postalCode,shippingpostalCode,
                       errorArray,alternateEmail):
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
                    if variableIsNumeric(contactNumber) is True and len(contactNumber) < 13 and len(contactNumber) > 4:
                        # validating country / state present in the model
                        if len(postalCode) <= 6 and len(postalCode)!=0:
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
                                            shippingCountryName = Country.objects.get(countryName__iexact=shippingCountry)
                                        except:
                                            shippingCountryName = None
                                        if shippingCountryName is not None:
                                            try:
                                                shippingStateName = State.objects.get(stateName__iexact=shippingState)
                                            except:
                                                shippingStateName = None
                                            if shippingStateName is not None:
                                                if len(shippingpostalCode)<=6 and len(shippingpostalCode)!=0:
                                                    return True
                                                else:
                                                    errorArray['error'] = 'Please enter valid shipping postal code'
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
            errorArray['error'] = 'Please enter valid Alternate Email ID'
            return errorArray
    errorArray['error'] = 'Please enter valid Email ID'
    return errorArray


# check whether the variable is numeric
def variableIsNumeric(variable):
    # check the variable is an integer
    if isinstance(variable, int):
        return True
    # check only it contains digits
    elif variable.isdigit():
        return True
    return False


@csrf_exempt
def acceptOrrejectTrader(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        body = json.loads(a)
        type = body['type']
        relId = body['relId']
        # status = accepted / rejected
        status = body['status']
        userCompany = utility.getCompanyBySchemaName(connection.schema_name)
        traderUser = utility.getUserByEmail(body['email'])
        traderCompany = traderUser.userCompanyId
        if status == "accepted":
            if type == constants.Customer:
                customer = utilitySD.getCustomerByEmail(body['email'])
                if customer is None:
                    customer = Customer()
                customer.customerCode = utility.oTtradersCodeGenerator(userCompany.companyName, constants.Customer)
                customer.connectionCode = relId
                customer.relationshipStatus = True
                customer.status = constants.Active
                customer.cusCompanyCode = traderCompany.companyCode
                customerDetailSave(customer, traderCompany.companyName, traderCompany.country_id,
                                   traderCompany.address_Line1, traderCompany.address_Line2, traderCompany.unit1,
                                   traderCompany.unit2, traderCompany.state_id, traderCompany.postalCode, '',
                                   traderUser.email,
                                   traderUser.countryCode_id, traderUser.contactNo, 2,traderUser.email
                                   )

                mainView.notificationView(request, customer.customerId, "You are connected with " + str(customer.cusCompanyName),
                                          " ")
                currentSchema = connection.schema_name
                connection.set_schema(schema_name=traderCompany.schemaName)
                supplier = utilitySD.getSupplierByConnectionCode(relId)
                supplier.supCompanyCode = userCompany.companyCode
                supplier.relationshipStatus = True
                supplier.save()
                mainView.notificationView(request, supplier.supplierId,
                                          "Do you allow supplier " + str(supplier.supCompanyName)+" to assign SLA for your site? ",
                                          "SiteAssign")
                connection.set_schema(schema_name=currentSchema)
                return JsonResponse(
                    {'status': 'success', 'success_msg': 'Customer added successfully',
                     'redirect_url': settings.HTTP + request.get_host() + '/dashboard'})
            else:
                supplier = utilitySD.getSupplierByEmail(body['email'])
                if supplier is None:
                    supplier = Supplier()
                supplier.connectionCode = relId
                supplier.supplierCode = utility.oTtradersCodeGenerator(userCompany.companyName, constants.Supplier)
                supplier.relationshipStatus = True
                supplier.status = constants.Active
                supplier.supCompanyCode = traderCompany.companyCode
                supplierDetailSave(supplier, traderCompany.companyName, traderCompany.country_id,
                                   traderCompany.address_Line1, traderCompany.address_Line2, traderCompany.unit1,
                                   traderCompany.unit2, traderCompany.state_id, traderCompany.postalCode, '',
                                   traderUser.email,
                                   traderUser.countryCode_id, traderUser.contactNo, 2,traderUser.email
                                   )
                mainView.notificationView(request, supplier.supplierId,
                                          "Do you allow supplier " + str(supplier.supCompanyName)+" to assign SLA for your site? ",
                                          "SiteAssign")
                currentSchema = connection.schema_name
                connection.set_schema(schema_name=traderCompany.schemaName)
                customer = utilitySD.getCustomerByConnectionCode(relId)
                customer.relationshipStatus = True
                customer.cusCompanyCode = userCompany.companyCode
                customer.save()
                mainView.notificationView(request, customer.customerId,
                                          str(customer.cusCompanyName) + " accepted your request",
                                          "Customer")
                connection.set_schema(schema_name=currentSchema)
                return JsonResponse(
                    {'status': 'success', 'success_msg': 'Supplier added successfully',
                     'redirect_url': settings.HTTP + request.get_host() + '/dashboard'})
        else:
            currentSchema = connection.schema_name
            connection.set_schema(schema_name=traderCompany.schemaName)
            if type == constants.Customer:
                supplier = utilitySD.getSupplierByConnectionCode(relId)
                supplier.invitationStatus = 4
                supplier.save()
            else:
                customer = utilitySD.getCustomerByConnectionCode(relId)
                customer.invitationStatus = 4
                customer.save()
            connection.set_schema(schema_name=currentSchema)
            return JsonResponse(
                {'status': 'success', 'success_msg': type  +' rejected successfully',
                 'redirect_url': settings.HTTP + request.get_host() + '/dashboard'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# creating error message html for matched details
def errormessage(type, responseData, alreadyExistData, message):
    return render_to_string('errormessage.html',
                            {'type': type, 'data': responseData, 'alreadyExistData': alreadyExistData,
                             'message': message})

def acceptCustomer(request, uidb64, token):
    if ('user' or 'subUser') in request.session and 'wsid' in request.GET:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, '/acceptCustomer')
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, '/acceptCustomer')
        if urls:
            try:
                # getting the primary key of user from the UID
                uid = force_text(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)

            except(TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            if user and account_activation_token.check_token(user, token):
                customer = utilitySD.getCustomerByEmail(user.email)
                relId = request.GET.get('wsid', '')
                alert = None
                if customer:
                    alert = 'This Customer information is already present in your system.If you accept, the customer details override the existing'
                    if customer.status == constants.Inactive:
                        alert = 'This Customer deactivated by your request.If you accept, this customer reactivated'
                    if customer.relationshipStatus and customer.status == constants.Active:
                        alert ='The Customer already linked with your system'
                userForm = AcceptTraderForm(
                    initial={'email': user.email, 'contactNo': user.contactNo,
                             'countryCode': "+" + user.countryCode.countryCodeType,
                             'firstName': user.firstName, 'lastName': user.lastName, 'type': "customer", 'relId': relId})
                companyForm = AcceptTraderCompanyForm(
                    initial={'companyName': company.companyName, 'country': company.country.countryName,
                             'state': company.state.stateName, 'address_Line1': company.address_Line1,
                             'address_Line2': company.address_Line1, 'unit1': company.unit1,
                             'unit2': company.unit2, 'postalCode': company.postalCode})

                return render(request, 'acceptTrader.html',
                              {'company': company, 'ProfileForm': profileForm,
                               'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                               'noti': notiFy, 'form': userForm, 'companyform': companyForm,'alert':alert,
                               'leng': lengTh, 'user': currentUser, 'status': company.urlchanged, })
            else:
                return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')



def acceptSupplier(request, uidb64, token):
    if ('user' or 'subUser') in request.session and 'wsid' in request.GET:
        profileForm = UserProfileForm()
        companyProfileForm = CompanyProfileForm()
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, '/acceptSupplier')
            # get the user from session using email
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, '/acceptSupplier')
        if urls:
            try:
                # getting the primary key of user from the UID
                uid = force_text(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)

            except(TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            # getting the length of the notification
            lengTh = len(notiFy)
            if user and account_activation_token.check_token(user, token):
                supplier = utilitySD.getSupplierByEmail(user.email)
                relId = request.GET.get('wsid', '')
                alert = None
                if supplier:
                    alert = 'This Supplier information is already present in your system.If you accept, the supplier details override the existing'
                    if supplier.status == constants.Inactive:
                        alert = 'This Supplier deactivated by your request.If you accept, this supplier reactivated'
                    if supplier.relationshipStatus and supplier.status == constants.Active:
                        alert = 'The Supplier already linked with your system'
                userForm = AcceptTraderForm(
                    initial={'email': user.email, 'contactNo': user.contactNo,
                             'countryCode': "+" + user.countryCode.countryCodeType,
                             'firstName': user.firstName, 'lastName': user.lastName, 'type': "supplier", 'relId': relId})
                companyForm = AcceptTraderCompanyForm(
                    initial={'companyName': company.companyName, 'country': company.country.countryName,
                             'state': company.state.stateName, 'address_Line1': company.address_Line1,
                             'address_Line2': company.address_Line1, 'unit1': company.unit1,
                             'unit2': company.unit2, 'postalCode': company.postalCode})
                return render(request, 'acceptTrader.html',
                              {'company': company, 'ProfileForm': profileForm,
                               'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                               'noti': notiFy, 'form': userForm, 'companyform': companyForm, 'alert': alert,
                               'leng': lengTh, 'user': currentUser, 'status': company.urlchanged, })
            else:
                return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


def saveproductAttribute(Attribute,color,size,design,style,other):
    Attribute.attributeColor = color
    Attribute.attributeSize = size
    Attribute.attributeDesign = design
    Attribute.attributeStyle = style
    Attribute.attributeOther = other
    Attribute.save()


def savepurchasingItems(Purchase,uom,tax,price,currency,priceUnit,uomforKg,text):
    Purchase.purchasingUom_id = uom
    Purchase.purchasingTax_id = tax
    Purchase.purchasingPrice = price
    Purchase.purchasingCurrency_id = currency
    Purchase.purchasingPriceUnit = priceUnit
    Purchase.purchasingUomForKg_id = uomforKg
    Purchase.purchasingOrderText = text
    Purchase.save()


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


def saveitemStorage(Storage,shelf,case,tier,pallet,dept,rack):
    Storage.storageShelfLife = shelf
    Storage.storageCase = case
    Storage.storageTier = tier
    Storage.storagePallet = pallet
    Storage.storageDept_id = dept
    Storage.storageRack = rack
    Storage.save()


def saveitemParameter(Parameter,one,two,three,four):
    Parameter.alterNateParamOne = one
    Parameter.alterNateParamTwo = two
    Parameter.alterNateParamThree = three
    Parameter.alterNateParamFour = four
    Parameter.save()


def saveItemMaster(Product,itemCode,itemName,alterItemCode,alterItemName,brandName,itemDesc,articleType
                   ,itemCategory,merchantCategory,merchantCategory1,merchantCategory2,storageCondition
                   ,uom,unit,self,lead,productDetail):
    Product.itemCode = itemCode.strip()
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

def deleteProductSubModels(product):
    productAttribute.objects.get(attributeItem=product).delete()
    purchasingItems.objects.get(purchasingItem=product).delete()
    salesItems.objects.get(salesItem=product).delete()
    itemMeasurement.objects.get(measurementItem=product).delete()
    itemStorage.objects.get(storageItem=product).delete()
    itemParameter.objects.get(parameterItem=product).delete()


def saveMasterProduct(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        itemCode = request.POST['itemCode']
        itemName = request.POST['itemName']
        resultSet = []
        a = {}
        b = {}
        key = request.POST
        masterItemCode = utilitySD.getProductByItemCode(itemCode)
        masterItemName = utilitySD.getProductByItemName(itemName)

        if (not masterItemCode and not masterItemName) or (masterItemCode and masterItemCode.status == constants.Inactive) \
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
            if 'selfManufacturing' in request.POST:
                selfManufacturing = True
            saveItemMaster(Product, itemCode, itemName, request.POST['alterItemCode'], request.POST['alterItemName'],
                           request.POST['brandName'], request.POST['itemDesc'], request.POST['articleType']
                           , request.POST['itemCategory'], request.POST['itemMerchantCategory'],
                           request.POST['itemMerchantCategoryOne'], request.POST['itemMerchantCategoryTwo'],
                           request.POST['itemStorageCondition'], request.POST['baseUom']
                           , request.POST['packingUnit'],selfManufacturing ,
                           request.POST['manufacturingLeadTime'],
                           request.POST['productDetail'],
                           )
            if request.POST['attributeColor'] or request.POST['attributeSize'] or request.POST['attributeDesign'] or \
                    request.POST['attributeStyle'] or request.POST['attributeOther']:
                Attribute =productAttribute()
                Attribute.attributeItem = Product
                saveproductAttribute(Attribute, request.POST['attributeColor'], request.POST['attributeSize'],
                                     request.POST['attributeDesign'], request.POST['attributeStyle'],
                                     request.POST['attributeOther'])
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
                savesalesItems(Sales, request.POST['salesUom'], request.POST['salesTax'], request.POST['salesCategoryGrp'],
                               request.POST['salesPrice'], request.POST['salesCurrency'], request.POST['salesPriceUnit'],
                               request.POST['salesUomForKg'], request.POST['salesOrderText'])
            if request.POST['measurementDimension'] or request.POST['measurementDimensionUnit'] or \
                    request.POST['measurementLength'] or request.POST['measurementHeight'] or \
                    request.POST['measurementWidth'] or request.POST['measurementWeight'] or request.POST['measurementWeightUnit']:
                Measurement =itemMeasurement()
                Measurement.measurementItem = Product
                saveitemMeasurement(Measurement, request.POST['measurementDimension'], request.POST['measurementDimensionUnit'],
                                    request.POST['measurementLength'], request.POST['measurementWidth'],
                                    request.POST['measurementHeight'], request.POST['measurementWeight'],
                                    request.POST['measurementWeightUnit'])
            if request.POST['storageShelfLife'] or request.POST['storageCase'] or \
                    request.POST['storageTier'] or request.POST['storagePallet'] or \
                    request.POST['storageDept'] or request.POST['storageRack'] :
                Storage = itemStorage()
                Storage.storageItem = Product
                saveitemStorage(Storage, request.POST['storageShelfLife'], request.POST['storageCase'],
                                request.POST['storageTier'], request.POST['storagePallet'], request.POST['storageDept'],
                                request.POST['storageRack'])
            if request.POST['alterNateParamOne'] or request.POST['alterNateParamTwo'] or \
                    request.POST['alterNateParamThree'] or request.POST['alterNateParamFour']:
                Parameter = itemParameter()
                Parameter.parameterItem = Product
                saveitemParameter(Parameter, request.POST['alterNateParamOne'], request.POST['alterNateParamTwo'],
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

    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def assignProductForCustomer(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        type = body['type']
        primaryObject = body['primaryObject']
        currentSchema = connection.schema_name
        if 'user' in request.session:
            user = utility.getObjectFromSession(request, 'user')
            company = user.userCompanyId
            # get the user from session using email
        if 'subUser' in request.session:
            subUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(currentSchema)
        cusProLis = []
        if type == 'product':
            objectList = body['data']
            masterItem = utilitySD.getProductByItemCode(primaryObject)
            salesDetails = utilitySD.getSalesDetailsByProduct(masterItem)
            modifiedPrice = body['price']
            for dictionaries in objectList:
                singleCustomer = utilitySD.getCustomerById(dictionaries['customerId'])
                try:
                    customerCatalog = CustomerProductCatalog.objects.get(itemCode=masterItem.itemCode, customerId=singleCustomer)
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
                        supplierCatalog.status = constants.Pending
                    saveSupplierCatalog(supplierCatalog, masterItem, salesDetails.salesUom,
                                    salesDetails.salesTax,
                                    salesDetails.salesCurrency,
                                    salesDetails.salesPrice,
                                    salesDetails.salesUomForKg, modifiedPrice,True)
                    desc = supplier.supCompanyName + " assigned a product to you "
                    types = constants.AssignProductForCustomer
                    mainView.notificationView(request,supplier.pk, desc, types)
                    connection.set_schema(schema_name=currentSchema)
            return JsonResponse(
                {'status': 'success', 'success_msg': 'Product added successfully to the customer(s)'})
        elif type == 'catalog':
            objectList = body['data']
            productListSale = ProductCatalogForSaleDetails.objects.filter(productCatelogId_id=primaryObject,
                                                                          status=constants.Active).values('salePrdtCatDetId')
            for singleProduct in productListSale:
                productDetail = utilitySD.getProductFromSaleProductCatelogById(singleProduct['salePrdtCatDetId'])
                for dictionaries in objectList:
                    singleCustomer = utilitySD.getCustomerById(dictionaries['customerId'])
                    try:
                        customerCatalog = CustomerProductCatalog.objects.get(itemCode=productDetail.itemCode, customerId=singleCustomer)
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
                            supplierCatalog = SupplierProductCatalog.objects.get(supplierItemCode=productDetail.itemCode,
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
                        desc = supplier.supCompanyName + " assigned a product to you "
                        types = constants.AssignProductForCustomer
                        mainView.notificationView(request,supplier.pk, desc, types)
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
                mainView.notificationView(request, supplier.supplierId, desc, types)
                connection.set_schema(schema_name=currentSchema)
            for dictionaries in objectList:
                masterItem = utilitySD.getProductByItemCode(dictionaries['itemCode'])
                salesDetails = utilitySD.getSalesDetailsByProduct(masterItem)
                try:
                    customerCatalog = CustomerProductCatalog.objects.get(itemCode__iexact=dictionaries['itemCode'], customerId=customer)
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
                        supplierCatalog = SupplierProductCatalog.objects.get(supplierItemCode__iexact=dictionaries['itemCode'],
                                                                    supplierId=supplier)
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
            return JsonResponse({'status': 'success', 'success_msg': 'Product(s) added successfully to the customer'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

def saveCustomerCatalog(customerCatalog,masterItem,salesUom,salesTax,salesCurrency,salesPrice,salesUomForKg,modifiedPrice):
    customerCatalog.itemCode = masterItem.itemCode
    customerCatalog.itemName = masterItem.itemName
    customerCatalog.itemCategory = masterItem.itemCategory
    customerCatalog.salesUom = salesUom
    customerCatalog.salesTax = salesTax
    customerCatalog.salesCurrency = salesCurrency
    customerCatalog.salesPrice = salesPrice
    customerCatalog.salesUomForKg = salesUomForKg
    customerCatalog.discountPrice = modifiedPrice
    customerCatalog.save()

def saveSupplierCatalog(supplierCatalog,masterItem,purchaseUom,purchaseTax,purchaseCurrency,purchasePrice,purchaseUomForKg,modifiedPrice,status):
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


@csrf_exempt
def assignProductToSupplier(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        type = body['type']
        primaryObject = body['primaryObject']
        currentSchema = connection.schema_name
        if 'user' in request.session:
            user = utility.getObjectFromSession(request, 'user')
            company = user.userCompanyId
            # get the user from session using email
        if 'subUser' in request.session:
            subUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(currentSchema)
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
                    supplierCatalog = SupplierProductCatalog.objects.get(itemCode__iexact=masterItem.itemCode, supplierId=singleSupplier)
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
            return JsonResponse(
                {'status': 'success', 'success_msg': 'Product added successfully to the supplier(s)'})
        elif type == 'catalog':
            objectList = body['data']
            productListSale = ProductCatalogForPurchaseDetails.objects.filter(productCatelogId_id=primaryObject,
                                                                          status=constants.Active).values(
                'purPrdtCatDetId')
            for singleProduct in productListSale:
                productDetail = utilitySD.getProductFromPurchaseProductCatelogById(singleProduct['purPrdtCatDetId'])
                for dictionaries in objectList:
                    singleSupplier = utilitySD.getSupplierById(dictionaries['supplierId'])
                    try:
                        defaultSupplier = SupplierProductCatalog.objects.get(productId=productDetail.productId,
                                                                             defaultSupplier=True)
                    except:
                        defaultSupplier = None
                    try:
                        supplierCatalog = SupplierProductCatalog.objects.get(itemCode__iexact=productDetail.itemCode,
                                                                             supplierId=singleSupplier)
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
            return JsonResponse({'status': 'success', 'success_msg': 'Catalog added successfully to the supplier'})
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
                    supplierCatalog = SupplierProductCatalog.objects.get(itemCode__iexact=dictionaries['itemCode'], supplierId=supplier)
                except:
                    supplierCatalog = SupplierProductCatalog()
                    supplierCatalog.supplierId = supplier
                if defaultSupplier is None:
                    supplierCatalog.defaultSupplier = True
                supplierCatalog.productId = masterItem
                saveSupplierCatalog(supplierCatalog, masterItem, purchaseDetails.purchasingUom,
                                    purchaseDetails.purchasingTax,
                                    purchaseDetails.purchasingCurrency,
                                    purchaseDetails.purchasingPrice,
                                    purchaseDetails.purchasingUomForKg,
                                    dictionaries['price'],False)
            return JsonResponse({'status': 'success', 'success_msg': 'Product(s) added successfully to the supplier'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def saveTradersById(request):
    if ('user' or 'subUser') in request.session and 'type' in request.GET and 'code' in request.GET:
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
                         'countryCode': "+" + userTrder.countryCode.countryCodeType,
                         'firstName': userTrder.firstName, 'lastName': userTrder.lastName, 'type': request.GET.get('type')})
                return render(request, 'addTraderById.html',
                              {'company': company, 'form': userForm, 'ProfileForm': profileForm,
                               'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile,
                               'noti': notiFy, 'companyFormAccept': companyFormAccept, 'userFormAccept': userFormAccept,
                               'leng': lengTh, 'user': currentUser, 'status': company.urlchanged, })
            else:
                return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


@csrf_exempt
def viewSupplier(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        detailList = Supplier.objects.filter(status=constants.Active).values("supCompanyName","supContactNo",
                                                                             "supCountryCode__countryCodeType","supEmail",
                                                                             "supplierId","invitationStatus",
                                                                             "relationshipStatus")
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No Suppliers found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def viewCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        detailList = Customer.objects.filter(status=constants.Active).values("cusCompanyName","cusContactNo",
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


@csrf_exempt
def listOfItemsCustomer(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        category = body['type']
        if 'sup' in body:
            sup = body['sup']
        else:
            sup = None
        if category == 'customer' and sup:
            excludeItems = CustomerProductCatalog.objects.filter(customerId=sup, status=constants.Active).values('itemCode')
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),status=constants.Active).exclude(itemCode__in=excludeItems).values('itemCode', 'itemName', 'itemCategory',
                                                                                 'itemCategory__prtCatName',
                                                                                 'salesItem__salesPrice',
                                                                                 'salesItem__salesCurrency__currencyTypeCode',
                                                                                 'baseUom__quantityTypeCode')
            item['totalItem'] = list(itemList)
            customerList = Customer.objects.filter(status=constants.Active).values('customerId',
                                                                                   'cusCompanyName'
                                                                                   )
            item["totalCategory"] = list(customerList)
        elif category == 'product' and sup:
            itemList = ItemMaster.objects.get(~Q(productDetail=constants.Purchase),itemCode__iexact=sup, status=constants.Active)
            excludeCustomers = CustomerProductCatalog.objects.filter(itemCode__iexact=sup, status=constants.Active).values(
                'customerId')
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
        elif category == 'catalog' and sup:
            excludeCustomers = CustomerProductCatalog.objects.filter(productCatId_id=sup,
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
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),status=constants.Active).values('itemCode', 'itemName', 'itemCategory',
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
            itemList = ProductCatalogForSale.objects.filter(status=constants.Active).values('salePrdtCatId','catalogName')
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
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Purchase),status=constants.Active).values('itemName', 'itemCode')
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

@csrf_exempt
def listOfItemsSupplier(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        category = body['type']
        if 'sup' in body:
            sup = body['sup']
        else:
            sup = None
        if category == 'supplier' and sup:
            excludeItems = SupplierProductCatalog.objects.filter(supplierId_id=sup, status=constants.Active).values('itemCode')
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Sale),status=constants.Active).exclude(itemCode__in=excludeItems).values('itemCode', 'itemName', 'itemCategory__prtCatName',
                                                                                 'purchasingItem__purchasingPrice',
                                                                                 'baseUom__quantityTypeCode')
            item['totalItem'] = list(itemList)
            supplierList = Supplier.objects.filter(status=constants.Active).values('supplierId',
                                                                                   'supCompanyName'
                                                                                   )
            item["totalCategory"] = list(supplierList)
        elif category == 'product' and sup:
            itemList = ItemMaster.objects.get(~Q(productDetail=constants.Sale),itemCode__iexact=sup, status=constants.Active)
            excludeCustomers = SupplierProductCatalog.objects.filter(itemCode__iexact=sup, status=constants.Active).values(
                'supplierId')
            supplierList = Supplier.objects.filter(status=constants.Active).exclude(
                supplierId__in=excludeCustomers).values('supplierId', 'supplierCode',
                                                   'supCompanyName',
                                                   'supContactNo',
                                                   'supCountry__countryName',
                                                   'supState__stateName',
                                                   'supEmail',
                                                   )
            purchasingItemCustomer = purchasingItems.objects.get(purchasingItem=itemList)
            item["price"] = purchasingItemCustomer.purchasingPriceUnit
            item["priceUnit"] = str(purchasingItemCustomer.purchasingCurrency.currencyTypeCode)
            item['totalItem'] = list(supplierList)
        elif category == 'catalog' and sup:
            excludeCustomers = SupplierProductCatalog.objects.filter(productCatId_id=sup,
                                                                     status=constants.Active).values(
                'supplierId')
            supplierList = Supplier.objects.filter(status=constants.Active).exclude(
                supplierId__in=excludeCustomers).values('supplierId', 'supplierCode',
                                                        'supCompanyName',
                                                        'supContactNo',
                                                        'supCountry__countryName',
                                                        'supState__stateName',
                                                        'supEmail',
                                                        )
            item['totalItem'] = list(supplierList)
        elif category == 'supplier':
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Sale),status=constants.Active).values('itemCode', 'itemName', 'itemCategory__prtCatName',
                                                                                 'purchasingItem__purchasingPrice',
                                                                                 'baseUom__quantityTypeCode')
            item['totalItem'] = list(itemList)
            supplierList = Supplier.objects.filter(status=constants.Active).values('supplierId',
                                                                                   'supCompanyName'
                                                                                   )
            item["totalCategory"] = list(supplierList)
        elif category == 'catalog':
            itemList = ProductCatalogForPurchase.objects.filter(status=constants.Active).values('purPrdtCatId',
                                                                                            'catalogName')
            supplierList = Supplier.objects.filter(status=constants.Active).values('supplierId', 'supplierCode',
                                                                                   'supCompanyName',
                                                                                   'supContactNo',
                                                                                   'supCountry__countryName',
                                                                                   'supState__stateName',
                                                                                   'supEmail',
                                                                                   )
            item["totalCategory"] = list(itemList)
            item['totalItem'] = list(supplierList)
        else:
            itemList = ItemMaster.objects.filter(~Q(productDetail=constants.Sale),status=constants.Active).values('itemName', 'itemCode')
            supplierList = Supplier.objects.filter(status=constants.Active).values('supplierId', 'supplierCode',
                                                                                   'supCompanyName',
                                                                                   'supContactNo',
                                                                                   'supCountry__countryName',
                                                                                   'supState__stateName',
                                                                                   'supEmail',
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


# list the products for user
@csrf_exempt
def listOfItemsSupplierOrCustomer(request):
    if 'user' in request.session or 'subUser' in request.session:
        filterBy = None
        item = {}
        totalItems = []
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
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
                itemList = SupplierProductCatalog.objects.filter(~Q(supplierId__status=constants.Inactive),
                                                           ~Q(status=constants.Inactive),defaultSupplier=True).values(
                    'itemCode', 'itemName', 'itemCategory','itemCategory__prtCatName', price=F('discountPrice'),
                    relId_id=F('supplierId'), priceUnit__type=F(
                        'purchaseCurrency__currencyTypeCode'), uOm__type=F('purchaseUom__quantityTypeCode'),
                    id=F('supplierCatId'))
                totalCategory = productCategory.objects.all().values('prtCatName','prtCatId')
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
                    itemList = SupplierProductCatalog.objects.filter( Q(supplierId__in=supplier), status=constants.Active).values(
                        'itemCode',
                        'itemName',
                        'itemCategory',
                        'itemCategory__prtCatName',
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
                         price=F('discountPrice'),
                        relId_id=F('supplierId'),
                        id=F(
                            'supplierCatId'),
                        priceUnit__type=F(
                            'purchaseCurrency__currencyTypeCode'),
                        uOm__type=F(
                            'purchaseUom__quantityTypeCode'))
                else:
                    itemList = SupplierProductCatalog.objects.filter(Q(supplierId__in=supplier), status=constants.Active).values(
                        'itemCode',
                        'itemName', 'itemCategory',
                        'itemCategory__prtCatName',
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


def accessRemoving(itemtable):
    itemtable.status = constants.Inactive
    itemtable.relationshipStatus = False
    itemtable.save()


def itemRemoving(itemtable):
    for item in itemtable:
        item.status = constants.Inactive
        item.save()


@csrf_exempt
def removeCustomer(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            user = utility.getObjectFromSession(request, 'user')
            company = user.userCompanyId
        if 'subUser' in request.session:
            subUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        mail = body['email']
        customer = utilitySD.getCustomerByEmail(mail)
        ordCount = OrderPlacementfromCustomer.objects.filter(customerId=customer)
        ordStatus = OrderPlacementfromCustomer.objects.filter(customerId=customer,
                                                              ordstatus=constants.Pending).values()
        if ordCount.count() == 0 or ordStatus:
            itemforCus = CustomerProductCatalog.objects.filter(customerId=customer)
            itemRemoving(itemforCus)
            accessRemoving(customer)
            if customer.relationshipStatus:
                currentSchema = company.schemaName
                userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                connection.set_schema(schema_name=userCustomerSchema)
                supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                itemfromSup = SupplierProductCatalog.objects.filter(supplierId=supplier)
                itemRemoving(itemfromSup)
                accessRemoving(supplier)
                desc = company.companyName + " deleted from their supplier list"
                mainView.notificationView(request, supplier.supplierId, desc, None)
                connection.set_schema(schema_name=currentSchema)
            return JsonResponse({'status': 'success', 'success_msg': 'Customer removed successfully'})
        else:
            return JsonResponse({'status': 'success', 'success_msg': 'Cannot remove this customer'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def removeSupplier(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            user = utility.getObjectFromSession(request, 'user')
            company = user.userCompanyId
        if 'subUser' in request.session:
            subUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        mail = body['email']
        supplier = utilitySD.getSupplierByEmail(mail)
        ordCount = OrderPlacementtoSupplier.objects.filter(productId__supplierId=supplier)
        ordStatus = OrderPlacementtoSupplier.objects.filter(productId__supplierId=supplier,
                                                              ordstatus=constants.Pending).values()
        if ordCount.count() == 0 or ordStatus:
            itemfromSup = SupplierProductCatalog.objects.filter(supplierId=supplier)
            itemRemoving(itemfromSup)
            accessRemoving(supplier)
            if supplier.relationshipStatus:
                currentSchema = company.schemaName
                userCustomerSchema = utility.getCompanyByCompanyCode(supplier.cusCompanyCode).schemaName
                connection.set_schema(schema_name=userCustomerSchema)
                customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                itemforCus = CustomerProductCatalog.objects.filter(customerId=customer)
                itemRemoving(itemforCus)
                accessRemoving(customer)
                desc = company.companyName + " deleted from their customer list"
                mainView.notificationView(request,  customer.customerId,desc, None)
                connection.set_schema(schema_name=currentSchema)
            return JsonResponse({'status': 'success', 'success_msg': 'Supplier removed successfully'})
        else:
            return JsonResponse({'status': 'success', 'success_msg': 'Cannot remove this supplier'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def removeProduct(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            user = utility.getObjectFromSession(request, 'user')
            company = user.userCompanyId
        if 'subUser' in request.session:
            subUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        itemCode = body['itemCode']
        prod = OrderDetails.objects.filter(itemCode=itemCode, ordstatus=constants.Pending).values(
            'itemName')
        ordCount = OrderDetails.objects.filter(itemCode=itemCode)
        itemProdrelid = CustomerProductCatalog.objects.filter(itemCode=itemCode).values('customerId', 'itemName')
        currentSchema = company.schemaName
        if ordCount.count() == 0 or prod:
            itemMstr = ItemMaster.objects.get(itemCode=itemCode)
            itemMstr.status = constants.Inactive
            itemMstr.save()
            for singleCustomerId in itemProdrelid:
                customerId = singleCustomerId["customerId"]
                customer = utilitySD.getCustomerById(customerId)
                if customer.relationshipStatus:
                    userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                    connection.set_schema(schema_name=userCustomerSchema)
                    itemfromsup = SupplierProductCatalog.objects.get(supplierItemCode=itemCode)
                    accessRemoving(itemfromsup)
                    desc = str(itemfromsup.supplierId.supCompanyName)+ str(itemfromsup.itemName) + " deleted from your product List"
                    types = constants.RemoveCustomerOrSupplierOrProduct
                    mainView.notificationView(request,customer.customerId, desc, types)
                    connection.set_schema(schema_name=currentSchema)
            return JsonResponse({'status': 'success', 'success_msg': 'Product removed successfully'})
        else:
            return JsonResponse({'status': 'success', 'success_msg': 'Cannot remove this product'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def viewCustomerOrSupplierProducts(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        category = body['type']
        item = {}
        unit = {}
        currency = {}
        totalItems = []
        totalUnits = []
        totalcurrency = []
        if category == constants.Customer:
            relId = body['relId']
            detailList = CustomerProductCatalog.objects.filter(customerId=relId,status=constants.Active).values('itemCode',
                                                                                                     'itemName','discountPercentage',
                                                                                                     'discountAbsolute',
                                                                                                     'salesUom__quantityTypeCode','salesPrice',
                                                                                                            'salesCurrency__currencyTypeCode','discountPrice',
                                                                                                            'linked')
            unitList = []
            currencyList = []
        elif category == constants.Supplier:
            relId = body['relId']
            detailList = SupplierProductCatalog.objects.filter(supplierId=relId,status=constants.Active).values('itemCode',
                                                                                                     'itemName',
                                                                                                     'discountPrice',
                                                                                                     'purchaseUom__quantityTypeCode','purchasePrice',
                                                                                                            'purchaseCurrency__currencyTypeCode','discountPrice',
                                                                                                            'linked')
            unitList = []
            currencyList = []
        elif category == constants.Product:
            itemCode = body['itemCode']
            detailList = ItemMaster.objects.filter(itemCode=itemCode, status=constants.Active).values('itemCode',
                                                                                                      'itemName',
                                                                                                      'alterItemCode',
                                                                                                      'alterItemName',
                                                                                                      'alterItemName',
                                                                                                      'brandName',
                                                                                                      'itemDesc',
                                                                                                      'articleType__articleId',
                                                                                                      'itemCategory',
                                                                                                      'itemMerchantCategory',
                                                                                                      'itemMerchantCategoryOne',
                                                                                                      'itemMerchantCategoryTwo',
                                                                                                      'itemStorageCondition',
                                                                                                      'baseUom',
                                                                                                      'packingUnit',
                                                                                                      'selfManufacturing',
                                                                                                      'manufacturingLeadTime',
                                                                                                      'productDetail',
                                                                                                      'attributeItem__attributeColor',
                                                                                                      'attributeItem__attributeDesign',
                                                                                                      'attributeItem__attributeStyle',
                                                                                                      'attributeItem__attributeOther',
                                                                                                      'attributeItem__attributeSize',
                                                                                                      'purchasingItem__purchasingUom',
                                                                                                      'purchasingItem__purchasingTax',
                                                                                                      'purchasingItem__purchasingPrice',
                                                                                                      'purchasingItem__purchasingCurrency',
                                                                                                      'purchasingItem__purchasingCurrency',
                                                                                                      'purchasingItem__purchasingPriceUnit',
                                                                                                      'purchasingItem__purchasingUomForKg',
                                                                                                      'purchasingItem__purchasingOrderText',
                                                                                                      'salesItem__salesUom',
                                                                                                      'salesItem__salesTax',
                                                                                                      'salesItem__salesCategoryGrp',
                                                                                                      'salesItem__salesPrice',
                                                                                                      'salesItem__salesCurrency',
                                                                                                      'salesItem__salesPriceUnit',
                                                                                                      'salesItem__salesUomForKg',
                                                                                                      'salesItem__salesOrderText',
                                                                                                      'measurementItem__measurementDimension',
                                                                                                      'measurementItem__measurementDimensionUnit',
                                                                                                      'measurementItem__measurementLength',
                                                                                                      'measurementItem__measurementWidth',
                                                                                                      'measurementItem__measurementHeight',
                                                                                                      'measurementItem__measurementWeight',
                                                                                                      'measurementItem__measurementWeightUnit',
                                                                                                      'storageItem__storageShelfLife',
                                                                                                      'storageItem__storageCase',
                                                                                                      'storageItem__storageTier',
                                                                                                      'storageItem__storagePallet',
                                                                                                      'storageItem__storageDept',
                                                                                                      'storageItem__storageRack',
                                                                                                      'parameterItem__alterNateParamOne',
                                                                                                      'parameterItem__alterNateParamTwo',
                                                                                                      'parameterItem__alterNateParamThree',
                                                                                                      'parameterItem__alterNateParamFour')
            unitList = []
            currencyList = []

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

@csrf_exempt
def itemRemoveForCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        customerId = body['relId']
        itmCode = body['itemCode']
        ordCount = OrderPlacementfromCustomer.objects.filter(orderdetail__itemCode=itmCode, customerId=customerId)
        ordStatus = OrderPlacementfromCustomer.objects.filter(orderdetail__itemCode=itmCode, customerId=customerId,
                                                              ordstatus=constants.Pending).values()
        customer = utilitySD.getCustomerById(customerId)
        if ordCount.count() == 0 or ordStatus:
            itemforcus = CustomerProductCatalog.objects.get(itemCode=itmCode, customerId=customerId, status=constants.Active)
            accessRemoving(itemforcus)
            currentSchema = connection.schema_name
            if customer.relationshipStatus:
                userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                connection.set_schema(schema_name=userCustomerSchema)
                supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
                itemfromSup = SupplierProductCatalog.objects.get(supplierItemCode=itmCode, supplierId=supplier, status=constants.Active)
                accessRemoving(itemfromSup)
                desc = itemfromSup.supplierItemName + " access removed thier supplier"
                types = constants.ItemRemoveForCustomer
                mainView.notificationView(request,customer.customerId, desc, types)
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
            mainView.notificationView(request,customer.customerId, desc, types)
            connection.set_schema(schema_name=currentSchema)
            return JsonResponse({'status': 'success', 'success_msg': 'Notification for delete product send successfully'})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


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
                {'status': 'error', 'error_msg': 'No Suppliers found'})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# product adding method using csv
def saveMasterProductUsingCsv(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        try:
            if 'user' in request.session:
                currentUser = utility.getObjectFromSession(request, 'user')
                # get the current user company name
                userCompany = currentUser.userCompanyId
            if 'subUser' in request.session:
                currentUser = utility.getObjectFromSession(request, 'subUser')
                # get the current user company name
                userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            # get the email from the session
            inputCsv = request.FILES.get('myfile', False)
            listCsv = list(csv.DictReader(io.TextIOWrapper(inputCsv)))
            # takes an object and produces a string
            dumps = json.dumps(listCsv)
            # would take a file-like object, read the data from that object, and use that string to create an object
            productsFromCsv = json.loads(dumps)
            resultSet = []
            resultSuccessfulSet = []
            type = request.POST['type'].lower()
            if len(productsFromCsv) > 0:
                a = {}
                b = {}
                # get individual products from csv
                for singleProduct in productsFromCsv:
                    try:
                        itemCode = singleProduct['PRODUCT_NAME']
                        itemName = singleProduct['PRODUCT_CODE']
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
                        priceUnitKgPur = singleProduct['PURCHASE_ORDER_PRICE_UNIT_KG']
                        purchaseText = singleProduct['PURCHASE_ORDER_TEXT']
                        salesUnitSale = singleProduct['SALES_UNIT_SALES']
                        texCodeSale = singleProduct['TAX_CODE_SALES']
                        sellingPriceSale = singleProduct['SELLING_PRICE_SALES']
                        currencyKeySale = singleProduct['CURRENCY_KEY_SALES']
                        a["currentData"] = {'itemCode':itemCode,'itemName':itemName}
                    # mandatory fields are not present it will show the error messsage
                    except:
                        return JsonResponse(
                            {'status': 'showerror',
                             'error_msg': 'Please upload the csv with proper headers/mandotary fields'})

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
                        if singleProduct('SELF_MANUFACTURING_PRODUCT').lower() == "yes":
                            selfManufacturing = True
                        articleType= utilitySD.getArticleTypeByName(articleType)
                        prodCategory = utilitySD.getProductCategoryByName(prodCategory)
                        merchantCat = utilitySD.getMerchantCategoryByName(singleProduct['MERCHANDISE_CATEGORY'])
                        merchantCatOne = utilitySD.getMerchantCategoryOneByName(singleProduct['MERCHANDISE_SUB_CATEGORY_L1'])
                        merchantCatTwo = utilitySD.getMerchantCategoryTwoByName(singleProduct['MERCHANDISE_SUB_CATEGORY_L2'])
                        if articleType is None  and articleType != '':
                            articleType = typeOfArticle(articleName=articleType,articleDesc = articleType).save()

                        saveItemMaster(Product, itemCode, itemName, singleProduct['ALTERNATE_PRODUCT_CODE'],
                                       singleProduct['ALTERNATE_PRODUCT_NAME'],
                                       brandName, prodDesc, articleType
                                       , prodCategory, merchantCat,
                                       merchantCatOne, merchantCatTwo,
                                       utilitySD.getStorageConditionByName(storageCondition),
                                       utility.getQuantityTypeByName(baseUom)
                                       , singleProduct['PACKING_UNIT'], selfManufacturing,
                                       singleProduct['MANUFACTURING_LEAD_TIME'])
                        if singleProduct['COLOR_ATTRIBUTE'] !='' or singleProduct['SIZE_ATTRIBUTE']!='' or singleProduct[
                            'DESIGN_ATTRIBUTE']!='' or singleProduct['STYLE_OR_PATTERN']!='' or singleProduct['OTHER_ATTRIBUTE']!='':
                            Attribute = productAttribute()
                            Attribute.attributeItem = Product
                            saveproductAttribute(Attribute, singleProduct['COLOR_ATTRIBUTE'],
                                                 singleProduct['SIZE_ATTRIBUTE'],
                                                 singleProduct['DESIGN_ATTRIBUTE'], singleProduct['STYLE_OR_PATTERN'],
                                                 singleProduct['OTHER_ATTRIBUTE'])
                        Purchase = purchasingItems()
                        Purchase.purchasingItem = Product
                        savepurchasingItems(Purchase, utility.getQuantityTypeByName(orderUnitPur),
                                            taxCodePur,purchasePrice, currencyKeyPur,
                                            priceUnitPur, priceUnitKgPur,purchaseText)
                        Sales = salesItems()
                        Sales.salesItem = Product
                        savesalesItems(Sales, salesUnitSale, texCodeSale,
                                       singleProduct['ITEM_CATEGORY_GROUP_SALES'],
                                       sellingPriceSale, currencyKeySale,
                                       singleProduct['PRICE_UNIT_SALES'],
                                       singleProduct['SELLING_PRICE_UNIT_SALES'], singleProduct['SALES_TEXT_SALES'])
                        if singleProduct['DIMENSION_MEASUREMENT'] or singleProduct['DIMENSION_UNIT_MEASUREMENT'] or \
                                singleProduct['LENGTH_MEASUREMENT'] or singleProduct['HEIGHT_MEASUREMENT'] or \
                                singleProduct['WIDTH_MEASUREMENT'] or singleProduct['WEIGHT_MEASUREMENT'] or singleProduct[
                            'WEIGHT_UNIT_MEASUREMENT']:
                            Measurement = itemMeasurement()
                            Measurement.measurementItem = Product
                            saveitemMeasurement(Measurement, singleProduct['DIMENSION_MEASUREMENT'],
                                                singleProduct['DIMENSION_UNIT_MEASUREMENT'],
                                                singleProduct['LENGTH_MEASUREMENT'], singleProduct['WIDTH_MEASUREMENT'],
                                                singleProduct['HEIGHT_MEASUREMENT'], singleProduct['WEIGHT_MEASUREMENT'],
                                                singleProduct['WEIGHT_UNIT_MEASUREMENT'])
                        if singleProduct['SHELF_LIFE_DAYS_STORAGE'] or singleProduct['CASE_OR_TIER_STORAGE'] or \
                                singleProduct['TIER_OR_PALLET_STORAGE'] or singleProduct['CASE_OR_PALLET_STORAGE'] or \
                                singleProduct['DEPARTMENT_STORAGE'] or singleProduct['RACK_STORAGE']:
                            Storage = itemStorage()
                            Storage.storageItem = Product
                            saveitemStorage(Storage, singleProduct['SHELF_LIFE_DAYS_STORAGE'], singleProduct['CASE_OR_TIER_STORAGE'],
                                            singleProduct['TIER_OR_PALLET_STORAGE'], singleProduct['CASE_OR_PALLET_STORAGE'],
                                            singleProduct['DEPARTMENT_STORAGE'],
                                            singleProduct['RACK_STORAGE'])
                        if singleProduct['ALTERNATE_PARAMETER_ONE'] or singleProduct['ALTERNATE_PARAMETER_TWO'] or \
                                singleProduct['ALTERNATE_PARAMETER_THREE'] or singleProduct['ALTERNATE_PARAMETER_FOUR']:
                            Parameter = itemParameter()
                            Parameter.parameterItem = Product
                            saveitemParameter(Parameter, singleProduct['ALTERNATE_PARAMETER_ONE'],
                                              singleProduct['ALTERNATE_PARAMETER_TWO'],
                                              singleProduct['ALTERNATE_PARAMETER_THREE'], request.POST['ALTERNATE_PARAMETER_FOUR'])
                        b["error"] = 'The below product is added successfully'
                        a.update(b)
                        resultSuccessfulSet.append(a)
                    else:
                        if masterItemCode:
                            b["error"] = 'This Product Code is already exist'
                        elif masterItemName:
                            b["error"] = 'This Product Name is already exist'
                        a.update(b)
                        resultSet.append(a)

                # matched data or validation failure data present then it will show the data details
                if resultSet:
                    errormessages = errormessage(type, [], resultSet + resultSuccessfulSet, "")
                    return JsonResponse(
                        {'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
                # no matched data or validation failures it will show success message
                else:
                    return JsonResponse({'status': 'success', 'success_msg': 'product(s) were added successfully'})
            # csv is empty
            else:
                return JsonResponse(
                    {'status': 'showerror', 'error_msg': 'Please upload csv with data'})
        # exception is product save it will give the saved and matched details with error messsage
        except:
            if resultSet or resultSuccessfulSet:
                errormessages = errormessage("product", [], resultSet + resultSuccessfulSet,
                                             "Some of the product(s) not added please check and update the valid csv")
                return JsonResponse(
                    {'status': 'error', 'error_msg': 'matchedData', 'matchedDataContent': errormessages})
            return JsonResponse(
                {'status': 'showerror', 'error_msg': 'Please upload valid csv'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def productCatalogSales(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
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

@csrf_exempt
def saveProductCatalogSales(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        objectList = body['data']
        catalogName = body['catalogName']
        alreadyExistName = utilitySD.getSaleProductCatelogByName(catalogName)
        if alreadyExistName:
            return JsonResponse({'status': 'success', 'error_msg': 'Product Catelog Name already exists!!!.'})
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
            return JsonResponse({'status': 'success', 'success_msg': 'Product(s) added successfully to the sales catalog'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def productCatalogPurchase(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
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

@csrf_exempt
def saveProductCatalogPurchase(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        objectList = body['data']
        catalogName = body['catalogName']
        alreadyExistName = utilitySD.getPurchaseProductCatelogByName(catalogName)
        if alreadyExistName:
            return JsonResponse({'status': 'success', 'error_msg': 'Product Catelog Name already exists!!!.'})
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
            return JsonResponse({'status': 'success', 'success_msg': 'Product(s) added successfully to the purchase catalog'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def updateMasterProduct(request):
    if ('user' in request.session or 'subUser' in request.session) and request.method == 'POST':
        itemCode = request.POST['itemCode']
        resultSet = []
        a = {}
        b = {}
        selfManufacturing = False
        if 'selfManufacturing' in request.POST:
            selfManufacturing = True
        Product = ItemMaster.objects.get(itemCode=itemCode)
        saveItemMaster(Product, itemCode, request.POST['itemName'], request.POST['alterItemCode'], request.POST['alterItemName'],
                           request.POST['brandName'], request.POST['itemDesc'], request.POST['articleType']
                           , request.POST['itemCategory'], request.POST['itemMerchantCategory'],
                           request.POST['itemMerchantCategoryOne'], request.POST['itemMerchantCategoryTwo'],
                           request.POST['itemStorageCondition'], request.POST['baseUom']
                           , request.POST['packingUnit'],selfManufacturing ,
                           request.POST['manufacturingLeadTime'],request.POST['productDetail'])
        if request.POST['attributeColor'] or request.POST['attributeSize'] or request.POST['attributeDesign'] or \
                request.POST['attributeStyle'] or request.POST['attributeOther']:
            try:
                Attribute =productAttribute.objects.get(attributeItem=Product)
            except:
                Attribute = productAttribute()
            Attribute.attributeItem = Product
            saveproductAttribute(Attribute, request.POST['attributeColor'], request.POST['attributeSize'],
                                 request.POST['attributeDesign'], request.POST['attributeStyle'],
                                     request.POST['attributeOther'])
        try:
            Purchase = purchasingItems.objects.get(attributeItem=Product)
        except:
            Purchase = purchasingItems()
        Purchase.purchasingItem = Product
        savepurchasingItems(Purchase, request.POST['purchasingUom'], request.POST['purchasingTax'],
                            request.POST['purchasingPrice'], request.POST['purchasingCurrency'],
                            request.POST['purchasingPriceUnit'], request.POST['purchasingUomForKg'],
                            request.POST['purchasingOrderText'])
        try:
             Sales = salesItems.objects.get(attributeItem=Product)
        except:
            Sales = salesItems()
        Sales.salesItem = Product
        savesalesItems(Sales, request.POST['salesUom'], request.POST['salesTax'], request.POST['salesCategoryGrp'],
                       request.POST['salesPrice'], request.POST['salesCurrency'], request.POST['salesPriceUnit'],
                       request.POST['salesUomForKg'], request.POST['salesOrderText'])
        if request.POST['measurementDimension'] or request.POST['measurementDimensionUnit'] or \
                request.POST['measurementLength'] or request.POST['measurementHeight'] or \
                request.POST['measurementWidth'] or request.POST['measurementWeight'] or request.POST['measurementWeightUnit']:
            try:
                  Measurement =itemMeasurement.objects.get(attributeItem=Product)
            except:
                Measurement = itemMeasurement()
            Measurement.measurementItem = Product
            saveitemMeasurement(Measurement, request.POST['measurementDimension'], request.POST['measurementDimensionUnit'],
                                request.POST['measurementLength'], request.POST['measurementWidth'],
                                request.POST['measurementHeight'], request.POST['measurementWeight'],
                                request.POST['measurementWeightUnit'])
        if request.POST['storageShelfLife'] or request.POST['storageCase'] or \
                request.POST['storageTier'] or request.POST['storagePallet'] or \
                request.POST['storageDept'] or request.POST['storageRack']:
            try:
                Storage = itemStorage.objects.get(attributeItem=Product)
            except:
                Storage = itemStorage()
            Storage.storageItem = Product
            saveitemStorage(Storage, request.POST['storageShelfLife'], request.POST['storageCase'],
                            request.POST['storageTier'], request.POST['storagePallet'], request.POST['storageDept'],
                            request.POST['storageRack'])
        if request.POST['alterNateParamOne'] or request.POST['alterNateParamTwo'] or \
                request.POST['alterNateParamThree'] or request.POST['alterNateParamFour']:
            try:
                Parameter = itemParameter.objects.get(attributeItem=Product)
            except:
                Parameter = itemParameter()
            Parameter.parameterItem = Product
            saveitemParameter(Parameter, request.POST['alterNateParamOne'], request.POST['alterNateParamTwo'],
                              request.POST['alterNateParamThree'], request.POST['alterNateParamFour'])
        return JsonResponse({'status': 'success', 'success_msg': 'Product added successfully'})

    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def fetchSupplierProductMerging(request):
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
            noti = utilitySD.getNotificationById(request.GET['notificationId'])
            lengTh = len(notiFy)
            usrId = request.GET['id']
            supplier = utilitySD.getSupplierById(usrId)
            if supplier is None or noti is None:
                return HttpResponseRedirect('/dashboard/')
            noti.viewed = constants.Yes
            noti.save()
            assignItems = SupplierProductCatalog.objects.filter(supplierId=supplier,linked=False,status=constants.Pending).values()
            ownItems = ItemMaster.objects.all().values()
            return render(request, 'supplierproductmerging.html',
                          {'assignItems': list(assignItems), 'ownItems': list(ownItems), 'company': company, 'user': currentUser,
                           'form': userForm,
                           'ProfileForm': ProfileForm, 'companyProfileForm': companyProfileForm,
                           'subUserProfile': subUserProfile, 'status': company.urlchanged,
                           'noti': notiFy, 'leng': lengTh, 'usrId': usrId})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')


@csrf_exempt
def addOrMergingOrRejectProducts(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        datas = body['data']
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
                    sameProduct = SupplierProductCatalog.objects.get(productId=ownProduct,supplierId=supplier)
                except:
                    sameProduct = None
                suplierProCat = SupplierProductCatalog.objects.get(supplierItemCode__iexact=data['productCode'],
                                                                   supplierId=supplier)
                if not sameProduct:
                    try:
                        defaultSupplier = SupplierProductCatalog.objects.get(productId=ownProduct,
                                                                             defaultSupplier=True)
                    except:
                        defaultSupplier = None
                    suplierProCat.productId = ownProduct
                    suplierProCat.itemCode = ownProduct.itemCode
                    suplierProCat.itemName = ownProduct.itemName
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
                    b["error"] = 'Your Product is already merged with '+sameProduct.supplierItemCode
                    a["currentData"] = {'itemCode': suplierProCat.supplierItemCode,
                                        'itemName': suplierProCat.supplierItemName}
                    a.update(b)
                    resultSet.append(a)
            elif data['type'] == "add":
                suplierProCat = SupplierProductCatalog.objects.get(supplierItemCode__iexact=data['productCode'], supplierId=supplier)
                masterItemCode = utilitySD.getProductByItemCode(data['productCode'])
                masterItemName = utilitySD.getProductByItemName(suplierProCat.supplierItemName)
                try:
                    defaultSupplier = SupplierProductCatalog.objects.get(productId=masterItemCode,
                                                                         defaultSupplier=True)
                except:
                    defaultSupplier = None
                if (not masterItemCode and not masterItemName) or (
                        masterItemCode and masterItemCode.status == constants.Inactive) \
                        or (masterItemName and masterItemName.status == constants.Inactive):
                    addProduct = ItemMaster()
                    if masterItemCode:
                        addProduct = masterItemCode
                        deleteProductSubModels(addProduct)
                        addProduct.status = constants.Active
                    elif masterItemName:
                        addProduct = masterItemName
                        deleteProductSubModels(addProduct)
                        addProduct.status = constants.Active
                    addProduct.itemCode = suplierProCat.supplierItemCode
                    addProduct.itemName = suplierProCat.supplierItemName
                    addProduct.itemCategory = suplierProCat.itemCategory
                    addProduct.productDetail = constants.Purchase
                    addProduct.baseUom = suplierProCat.purchaseUom
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
                    connection.set_schema(schema_name=currentSchema)
                else:
                    if masterItemCode:
                        b["error"] = 'This Product Code is already exist'
                    elif masterItemName:
                        b["error"] = 'This Product Name is already exist'
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
                connection.set_schema(schema_name=currentSchema)
                a["currentData"] = {'itemCode': suplierProCat.supplierItemCode, 'itemName': suplierProCat.supplierItemName}
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
            mainView.notificationView(request, customer.customerId,
                                      str(customer.cusCompanyName) + " updated your catalog assignment ",
                                      "addOrMergingOrRejectProducts")
            connection.set_schema(schema_name=currentSchema)
            return JsonResponse({'status': 'success', 'success_msg': 'product(s) were updated successfully'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def updateProductAssigntoCustomer(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        customerId = body['cusId']
        itemCode = body['itemCode']
        customerProd = CustomerProductCatalog.objects.get(itemCode=itemCode, customerId=customerId)
        customerProd.discountPercentage = body['discountPercentage']
        customerProd.discountAbsolute = body['discountAbsolute']
        customerProd.discountPrice = body['discountPrice']
        customerProd.save()
        currentSchema = connection.schema_name
        customer = utility.getCustomerById(customerId)
        userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
        connection.set_schema(schema_name=userCustomerSchema)
        supplier = utilitySD.getSupplierByConnectionCode(customer.connectionCode)
        supplierProd = SupplierProductCatalog.objects.get(itemCode=itemCode, supplierId=supplier)
        supplierProd.discountPrice = body['discountPrice']
        supplierProd.save()
        connection.set_schema(schema_name=currentSchema)
        return JsonResponse({'status': 'success', 'success_msg': 'Product updated successfully'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def uploadHoliday(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
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
                    holiday.delete()
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
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def getHoliday(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        holiday = Holidays.objects.filter(status=constants.Active).values()
        if 'holidayId' in body:
            holiday = HolidaysDetails.objects.filter(holiday_id= body['holidayId']).values()
        return JsonResponse({'status': 'success', 'data': list(holiday)})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def fetchSupplierSites(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        supplierId = body['supId']
        supplier = utility.getSupplierById(supplierId)
        usrSupSites = SupplierSlaForSites.objects.filter(userSupSitesCompany=supplier).values('mappedSites')
        supplierSites = Sites.objects.all().exclude(siteId__in=usrSupSites).values('siteName','siteId')
        return JsonResponse({'status': 'success', 'userData': list(supplierSites)})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def saveSlaForSupplierFromCus(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        supId = body['supplierId']
        supplier = utility.getSupplierById(supId)
        cusAndSupMapSites = body['data']
        for sites in cusAndSupMapSites:
            try:
                customerSite = SupplierSlaForSites.objects.get(userSupSitesCompany=supplier,mappedSites=sites['cusSiteId'])
            except:
                customerSite = SupplierSlaForSites()
            customerSite.userSupSitesCompany = supplier
            customerSite.mappedSites = utility.getSiteBySiteId(sites)
            slaJsonData = utility.getSlaBySlaId(body['sla'])
            customerSite.slaFromSupplier = slaJsonData.slaDetails
            customerSite.save()
        return JsonResponse({'status': 'success', 'success_msg': 'Assigned successfully'})
    return JsonResponse(
        {'status': 'success', 'success_msg': 'SLA Added successfully',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def assignSLAForSites(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        cusId = body['customerId']
        cusAndSupMapSites = body['siteId']
        notificationId = body['notificationId']
        customer = utility.getCustomerById(cusId)
        for sites in cusAndSupMapSites:
            customerSite = CustomerSiteDetails.objects.get(userCustSitesCompany=customer,userCustSiteId=sites['cusSiteId'])
            siteInfo = utility.getSiteBySiteId(sites['supSiteId'])
            slaJsonData = siteInfo.siteArea.areaSlaId.slaDetails
            customerSite.customer_country = siteInfo.siteAddress.usradd_country
            customerSite.customer_address_Line1 = siteInfo.siteAddress.usradd_address_Line1
            customerSite.customer_address_Line2 = siteInfo.siteAddress.usradd_address_Line2
            customerSite.customer_unit1 = siteInfo.siteAddress.usradd_unit1
            customerSite.customer_unit2 = siteInfo.siteAddress.usradd_unit2
            customerSite.customer_state = siteInfo.siteAddress.usradd_state
            customerSite.customer_postalCode = siteInfo.siteAddress.usradd_postalCode
            customerSite.mappedSites_id = sites['supSiteId']
            customerSite.save()
            currentSchema = connection.schema_name
            customerCompany = utility.getCompanyByCompanyCode(customer.cusCompanyCode)
            connection.set_schema(schema_name=customerCompany.schemaName)
            supplier = utility.getSupplierByConnectionCode(customer.connectionCode)
            usersupsite = SupplierSlaForSites.objects.get(mappedSites_id=sites['cusSiteId'],userSupSitesCompany=supplier)
            usersupsite.slaFromSupplier = slaJsonData
            usersupsite.save()
            connection.set_schema(schema_name=currentSchema)
            noti = Notification.objects.get(pk=notificationId)
            noti.viewed = constants.Yes
            noti.save()
        return JsonResponse({'status': 'success','success_msg':'Site Assigned successfully'})
    return JsonResponse(
        {'status': 'success', 'success_msg': 'SLA Added successfully',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})



@csrf_exempt
def sitesAddingForSla(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        usrId = request.POST['sendFromId']
        notificationId = request.POST['id']
        supplier = utility.getSupplierById(usrId)
        supplierCompany = utility.getCompanyByCompanyCode(supplier.supCompanyCode)
        sitesid = Sites.objects.all().values('siteId')
        s = list(sitesid)
        noti = Notification.objects.get(notificationId=notificationId)
        noti.viewed = constants.Yes
        noti.save()
        for siteid in s:
            siteInfo = utility.getSiteBySiteId(siteid['siteId'])
            usersupsite = SupplierSlaForSites()
            usersupsite.userSupSitesCompany = supplier
            usersupsite.mappedSites_id = siteid['siteId']
            usersupsite.slaFromSupplier = constants.SlaDetailsJson
            usersupsite.save()
            currentSchema = connection.schema_name
            customerSite = CustomerSiteDetails()
            customerSite.customer_country = siteInfo.siteAddress.usradd_country
            customerSite.customer_address_Line1 = siteInfo.siteAddress.usradd_address_Line1
            customerSite.customer_address_Line2 = siteInfo.siteAddress.usradd_address_Line2
            customerSite.customer_unit1 = siteInfo.siteAddress.usradd_unit1
            customerSite.customer_unit2 = siteInfo.siteAddress.usradd_unit2
            customerSite.customer_state = siteInfo.siteAddress.usradd_state
            customerSite.customer_postalCode = siteInfo.siteAddress.usradd_postalCode
            customerSite.userCustSiteId = siteid['siteId']
            customerSite.userCustSiteName = siteInfo.siteName
            connection.set_schema(schema_name=supplierCompany.schemaName)
            customer = utility.getCustomerByConnectionCode(supplier.connectionCode)
            customerSite.userCustSitesCompany = customer
            customerSite.save()
            connection.set_schema(schema_name=currentSchema)
        connection.set_schema(schema_name=supplierCompany.schemaName)
        mainView.notificationView(request,customer.customerId,str(customer.cusCompanyName)+" gave access to assign SLA ","customer")
        connection.set_schema(schema_name=currentSchema)
    return JsonResponse(
        {'status': 'success', 'success_msg': 'SLA Added successfully',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def getAllSites(request):
    if 'user' in request.session or 'subUser' in request.session:
        site = Sites.objects.filter(siteStatus=constants.Active).values('siteId', 'siteName', 'siteDesc',
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


@csrf_exempt
def createSite(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        siteName = body['siteName']
        alreadyExistSite = utility.getSiteBySiteName(siteName)
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
            return JsonResponse({'status': 'success', 'success_msg': 'Site created successfully'})
        else:
            return JsonResponse({'status': 'error', 'error_msg': 'Site Name already exists!!.'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def updateSite(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        siteId = body['siteId']
        if body['type'] == 'edit':
            site = Sites.objects.filter(siteId=siteId).values('siteId', 'siteName', 'siteDesc', 'siteArea','siteType',
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
                site = utility.getSiteBySiteId(siteId)
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
                return JsonResponse({'status': 'success', 'success_msg': 'Site Updated successfully'})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def deleteSite(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        siteId = body['siteId']
        customerList = utility.getCustomerListBasedonSite(siteId)
        if customerList:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'Cant able to delete the Site.This site has customers.!!!'})
        else:
            site = utility.getSiteBySiteId(siteId)
            site.siteStatus = constants.Inactive
            site.save()
            return JsonResponse({'status': 'success', 'success_msg': 'Site deleted successfully'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


# Fetch the SLA Data
@csrf_exempt
def fetchSLAData(request):
    if 'user' in request.session or 'subUser' in request.session:
        SLAData = serviceLevelAgreement.objects.filter(slaStatus=constants.Active).values('slaId', 'slaType',
                                                                                          'slaStatus',
                                                                                          ).order_by(
                'slaId')

        return JsonResponse({'status': 'success', 'SLAData': list(SLAData)})

    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def updateSlaForCustomer(request):
    if 'user' in request.session or 'subUser' in request.session:
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(request.body.decode('utf-8'))
        slaId = body['slaId']
        if body['type'] == 'edit':
            # Fetch the SLA Data via SLA Id
            SLAData = serviceLevelAgreement.objects.filter(pk=slaId, slaStatus=constants.Active).values('slaId',
                                                                                                        'slaType',
                                                                                                        'slaDetails',
                                                                                                        'slaStatus',
                                                                                                        ).order_by(
                'slaId')
            return JsonResponse({'status': 'success', 'SLAData': list(SLAData)})
        else:
            # Update the SLA Data via SLA Id
            slaType = body['slaType']
            alreadyExistsSla = serviceLevelAgreement.objects.filter(~Q(slaId=slaId), slaType=slaType).all()
            if alreadyExistsSla.count() == 0:
                sla = utility.getSlaBySlaId(slaId)
                if sla.pk !=1:
                    sla.slaType = body['slaType']
                sla.slaDetails = body['slaJson']
                sla.save()
                customeList = utility.getCustomerListBasedonSla(slaId)
                currentSchema = connection.schema_name
                if customeList:
                    for individualCustomer in customeList:
                        connection.set_schema(schema_name=individualCustomer['schemaName'])
                        slaCustomer = utility.getSupplierById(individualCustomer['relId'])
                        slaCustomer.slaFromSupplier = body['slaJson']
                        slaCustomer.save()
                    connection.set_schema(schema_name=currentSchema)
                return JsonResponse({'status': 'success', 'success_msg': 'SLA updated successfully'})
            else:
                return JsonResponse({'status': 'error', 'error_msg': 'SLA Name already exists'})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


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


@csrf_exempt
def deleteSla(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        slaId = body['slaId']
        customerList = utility.getCustomerListBasedonSla(slaId)
        if customerList:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'Cant able to delete the SLA.This SLA has assigned to customers.!!'})
        else:
            sla = utility.getSlaBySlaId(slaId)
            sla.slaStatus = constants.Inactive
            sla.save()
            return JsonResponse({'status': 'success', 'success_msg': 'SLA deleted successfully'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})



@csrf_exempt
def accessProvideByRole(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        role = body['role']
        dic = {}
        if role == "Approver":
            lis = [1, 2, 3, 4, 5]
            dic['subuseracc'] = lis
        elif role == "Manager/ Assistant":
            lis = [6, 7]
            dic['subuseracc'] = lis
        elif role == "Supervisor":
            lis = [8, 9, 10]
            dic['subuseracc'] = lis
        elif role == "Operations 1":
            lis = [11, 12, 13]
            dic['subuseracc'] = lis
        elif role == "Operations 2":
            lis = [14, 15, 16]
            dic['subuseracc'] = lis
        else:
            lis = [20, 21, 22]
            dic['subuseracc'] = lis
        return JsonResponse({'status': 'success', 'roleAccess': dic})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def fetchAllCustomerForSlaAssign(request):
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
        if True:
            # getting the unviewed notifications for the user
            notiFy = Notification.objects.filter(viewed=constants.No).order_by('-createdDateTime')
            lengTh = len(notiFy)
            customerDetails = Customer.objects.all().values('cusCompanyName','customerId')
            sla =serviceLevelAgreement.objects.all().values('slaType','slaId')
            return render(request, 'assignSlaToCustomer.html',{'cus':customerDetails,'sla':sla,'user': currentUser, 'form': userForm, 'ProfileForm': ProfileForm,
                           'companyProfileForm': companyProfileForm, 'subUserProfile': subUserProfile, 'status': company.urlchanged,
                                                     'noti': notiFy, 'leng': lengTh})
        else:
            return HttpResponseRedirect('/unauthorize/')
    return HttpResponseRedirect('/login/')

@csrf_exempt
def fetchCustomerSites(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        customerId = body['cusId']
        customer = utility.getCustomerById(customerId)
        usrCusSites = CustomerSiteDetails.objects.filter(mappedSites=None,userCustSitesCompany=customer).values('userCustSiteName','userCustSitesId')
        return JsonResponse({'status': 'success', 'userData': list(usrCusSites)})
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def saveSlaForCustomerFromSup(request):
    if ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        cusId = body['customerId']
        customer = utility.getCustomerById(cusId)
        customerCompany = utility.getCompanyByCompanyCode(customer.cusCompanyCode)
        cusAndSupMapSites = body['data']
        currentSchema = connection.schema_name
        for sites in cusAndSupMapSites:
            customerSite = CustomerSiteDetails.objects.get(userCustSitesCompany=customer,)
            customerSite.mappedSites = utility.getSiteBySiteId(sites)
            customerSite.save()
            slaJsonData = utility.getSlaBySlaId(body['sla'])
            connection.set_schema(schema_name=customerCompany.schemaName)
            slaCustomer = utility.getSupplierByConnectionCode(customer.connectionCode)
            slaCustomer.slaFromSupplier = slaJsonData.slaDetails
            slaCustomer.save()
            connection.set_schema(schema_name=currentSchema)
        return JsonResponse({'status': 'success', 'success_msg': 'Assigned successfully'})
    return JsonResponse(
        {'status': 'success', 'success_msg': 'SLA Added successfully',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def sitePushing(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        a = request.body.decode('utf-8')
