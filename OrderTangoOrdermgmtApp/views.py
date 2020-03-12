from django.http import JsonResponse,HttpResponse,HttpResponseRedirect
from OrderTangoApp.forms import *
from OrderTangoSubDomainApp.models import *
import datetime
import os, json,base64
from django.views.decorators.csrf import csrf_exempt
from OrderTangoApp import utility, constants,views as mainView
from OrderTangoSubDomainApp import utilitySD
from OrderTangoOrdermgmtApp.models import *
from OrderTangoOrderFulfilmtApp.models import *
from OrderTango.settings import MEDIA_ROOT
from django.template.loader import render_to_string
from django.db.models import F

def createPlaceOrderHtml(userObject,slaObject,orderObjects, orderDetail,deliveryLocation):
    return render_to_string('poorder.html', {'userObject':userObject,'slaObject':slaObject,'orderArray':orderObjects,
                                             'orderDetail':orderDetail,'deliveryLocation':deliveryLocation})

@csrf_exempt
def orderPlacement(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
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
                                                                  'ShoppingCart',
                                                                 utilitySD.getCountOftheModelByModelName(
                                                                     "ShoppingCart")):
                    a = request.body.decode('utf-8')
                    body = json.loads(a)
                    deliveryAddressId = body['deliveryAddressId']
                    deliveryDate = body['deliveryDate']
                    expectedTime = body['expectedTime']
                    totalPrice = body['totalPrice']
                    orderDate = datetime.datetime.now()
                    data = body['data']
                    deliveryLocation = utilitySD.getSiteBysiteAddressId(deliveryAddressId)
                    currentSchema = connection.schema_name
                    l = []
                    newArray = []
                    for dictionary in data:
                        if dictionary['relId_id'] not in l:
                            l.append(dictionary['relId_id'])
                            object = {}
                            object['relId_id'] = dictionary['relId_id']
                            arrayData = []
                            supplierTotalPrice = 0
                            dateOfOrder = deliveryDate
                            for objects in data:
                                if object['relId_id'] == objects['relId_id']:
                                    objects['totalPrice']=round(float(objects['quantity']) * float(objects['price']),2)
                                    supplierTotalPrice = supplierTotalPrice + round((float(objects['quantity']) *
                                                                                     float(objects['price'])),2)
                                    if 'nextDeliveryDate' in objects:
                                        dateOfOrder = objects['nextDeliveryDate']
                                        if objects['nextDeliveryDate'] == constants.Available:
                                            dateOfOrder = deliveryDate
                                    arrayData.append(objects)
                            object['orderData'] = arrayData
                            object['supplierTotalPrice'] = supplierTotalPrice
                            object['dateOfOrder'] = dateOfOrder
                            newArray.append(object)
                    shopCart = openShopppingCart(object['dateOfOrder'], expectedTime, totalPrice, deliveryLocation)
                    for object in newArray:
                       supplier = utilitySD.getSupplierById(object['relId_id'])
                       customerUser = utility.getUserByCompanyId(userCompany.companyId)
                       supplierName = supplier.supCompanyName.replace(' ','')[:5]
                       pdfName = "PO-"+userCompany.companyName.replace(' ','')[:5].upper()+".pdf"
                       orderNumber = str(utility.oTorderNumberGenerator(object['relId_id'],supplierName))
                       now = datetime.datetime.now()
                       orderDetail = {}
                       orderDetail['companyImage'] = settings.HTTP + settings.IP_ADDRESS + ':' + \
                                                     settings.PORT+'/media/'+str(userCompany.companyImage)
                       if (orderDetail['companyImage']==settings.HTTP + settings.IP_ADDRESS + ':' +
                               settings.PORT+'/media/'):
                           base = os.path.dirname(os.path.abspath("companyLogo.png")) + \
                                  '/__shared__/images/companyLogo.png'
                           defFile = base.replace("\\", '/')
                           orderDetail['companyImage'] = defFile
                       orderDetail['customerEmail'] = customerUser.email
                       orderDetail['customerContactNo'] = customerUser.contactNo
                       orderDetail['orderNumber'] = orderNumber
                       orderDetail['date'] = now.strftime("%d/%m/%Y")
                       orderDetail['deliveryDate'] = object['dateOfOrder']
                       orderDetail['expectedTime'] = expectedTime
                       orderDetail['totalPrice'] = object['supplierTotalPrice']
                       orderDetail['tax'] = '7%'
                       orderDetail['totalTax'] = round(float(( object['supplierTotalPrice'] * 7 ) / 100),2)
                       orderDetail['totalPriceWithTax'] = round(float(orderDetail['totalTax'] +
                                                                      object['supplierTotalPrice']),2)
                       slaObject = utilitySD.getSiteSlabasedOnSupplierIdAndSiteId(deliveryLocation.pk, supplier.pk)
                       if slaObject:
                           slaJson = slaObject.slaFromSupplier
                           days = cutOffTimeCheck(slaJson['cutOffTime'])
                           if days == 1:
                               orderDate += datetime.timedelta(days=1)
                       for dictionary in object['orderData']:
                           customerItem = SupplierProductCatalog.objects.get(itemCode__iexact=dictionary['itemCode'],
                                                                             supplierId=supplier,
                                                                             status=constants.Active)
                           placToSup = OrderPlacementtoSupplier()
                           placToSup.productId = customerItem
                           placToSup.ordNumber = orderNumber
                           placToSup.shopCartId = shopCart
                           placToSup.orderType = constants.Orginal
                           if supplier.relationshipStatus:
                               placToSup.connectedStatus = True
                           orderSavetoCustomerOrSupplier(placToSup, dictionary,orderDate)
                       supplierAddressObject = {}
                       if slaObject:
                           supplierAddressObject['supCompanyCode'] = slaObject.userSupSitesCompany.supCompanyCode
                           supplierAddressObject['supCompanyName'] = slaObject.userSupSitesCompany.supCompanyName
                           supplierAddressObject['supplier_unit1'] = slaObject.supplier_unit1
                           supplierAddressObject['supplier_unit2'] = slaObject.supplier_unit2
                           supplierAddressObject['supplier_address_Line1'] = slaObject.supplier_address_Line1
                           supplierAddressObject['supplier_address_Line2'] = slaObject.supplier_address_Line2
                           supplierAddressObject['supplier_state'] = slaObject.supplier_state
                           supplierAddressObject['supplier_country'] = slaObject.supplier_country
                           supplierAddressObject['supplier_postalCode'] = slaObject.supplier_postalCode
                           supplierAddressObject['supEmail'] = slaObject.userSupSitesCompany.supEmail
                       else:
                           if supplier.supCompanyCode == None:
                               supplierAddressObject['supCompanyCode'] = " "
                           else:
                                supplierAddressObject['supCompanyCode'] = supplier.supCompanyCode
                           supplierAddressObject['supCompanyName'] = supplier.supCompanyName
                           supplierAddressObject['supplier_unit1'] = supplier.supUnit1
                           supplierAddressObject['supplier_unit2'] = supplier.supUnit2
                           supplierAddressObject['supplier_address_Line1'] = supplier.supAddress_Line1
                           supplierAddressObject['supplier_address_Line2'] = supplier.supAddress_Line2
                           supplierAddressObject['supplier_state'] = supplier.supState
                           supplierAddressObject['supplier_country'] = supplier.supCountry
                           supplierAddressObject['supplier_postalCode'] = supplier.supPostalCode
                           supplierAddressObject['supEmail'] = supplier.supEmail
                       html = createPlaceOrderHtml(userCompany,supplierAddressObject, object['orderData'],orderDetail,
                                                   deliveryLocation)
                       pdf = mainView.htmlToPdfConvertion(html, pdfName)
                       base64Value = pdfTobase64(MEDIA_ROOT+pdf)
                       pdfDetail = pdfDetailsForPlacedOrder()
                       pdfDetail.ordNumber = orderNumber
                       pdfDetail.pdfField = base64Value
                       pdfDetail.supplierId = supplier
                       pdfDetail.save()
                       if supplier.relationshipStatus:
                           os.remove(MEDIA_ROOT + pdf)
                           placFromCus = OrderPlacementfromCustomer()
                           placFromCus.customer_country = deliveryLocation.siteAddress.usradd_country
                           placFromCus.customer_address_Line1 = deliveryLocation.siteAddress.usradd_address_Line1
                           placFromCus.customer_address_Line2 = deliveryLocation.siteAddress.usradd_address_Line2
                           placFromCus.customer_unit1 = deliveryLocation.siteAddress.usradd_unit1
                           placFromCus.customer_unit2 = deliveryLocation.siteAddress.usradd_unit2
                           placFromCus.customer_state = deliveryLocation.siteAddress.usradd_state
                           placFromCus.customer_postalCode = deliveryLocation.siteAddress.usradd_postalCode
                           userSchema = utility.getCompanyByCompanyCode(supplier.supCompanyCode).schemaName
                           connection.set_schema(schema_name=userSchema)
                           customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                           customerDeliveryLoc=utilitySD.getCustomerSiteBySiteId(deliveryAddressId,customer.customerId)
                           if customerDeliveryLoc:
                               site = customerDeliveryLoc.mappedSites
                           else:
                               site = utilitySD.getSiteBySiteId(1)
                           placFromCus.customerId = customer
                           placFromCus.ordNumber = orderNumber
                           placFromCus.expectedDate = object['dateOfOrder']
                           placFromCus.expectedTime = expectedTime
                           placFromCus.siteId = site
                           placFromCus.orderDate = orderDate
                           placFromCus.pdfField = base64Value
                           placFromCus.connectedStatus = True
                           placFromCus.save()
                           for dictionary in object['orderData']:
                               orderDetails = OrderDetails()
                               orderDetails.ordNumber = placFromCus
                               orderDetails.itemCode = dictionary['itemCode']
                               orderDetails.itemName = dictionary['itemName']
                               orderDetails.itemCategory = dictionary['itemCategory']
                               orderSavetoCustomerOrSupplier(orderDetails, dictionary,orderDate)
                           mainView.notificationView(constants.Customer, customer.customerId,
                                                      str(customer.cusCompanyName)+ " placed an order",
                                                     "placeOrder",None,1)
                           connection.set_schema(schema_name=currentSchema)
                       else:
                           sendEmail = supplier.supEmail
                           if supplier.supCommunicationEmail:
                               sendEmail = supplier.supCommunicationEmail
                           mainView.sendingEmail(request,supplier,sendEmail,userCompany.companyName,"orderpomail.html",
                                                 "Order placement from " + userCompany.companyName.upper(),
                                                 None, pdf, None)
                           os.remove(MEDIA_ROOT + pdf)
                    return JsonResponse({'status': 'success',
                                         'success_msg': 'Order placement is successfully completed'})
                else:
                    return JsonResponse({'status': 'error',
                                         'error_msg': 'Your Purchased Order Placement Limit Is Exceeded'})
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


def openShopppingCart(expectedDate, expectedTime, totalPrice, deliveryLocation):
    shopCart = ShoppingCart()
    shopCart.totalPrice=totalPrice
    # shopCart.totalPriceUnit=CurrencyType.objects.get(id=currencyId)
    shopCart.expectedDate = expectedDate
    shopCart.expectedTime = expectedTime
    shopCart.deliveryLocation = deliveryLocation
    shopCart.save()
    return shopCart


def orderSavetoCustomerOrSupplier(table, dictionary,date):
    table.quantity = dictionary['quantity']
    table.actualQuantity = dictionary['quantity']
    table.price = dictionary['price']
    table.priceUnit = CurrencyType.objects.get(currencyTypeCode=dictionary['priceUnit__type'])
    table.uOm = QuantityType.objects.get(quantityTypeCode=dictionary['uOm__type'])
    table.orderDate = date
    table.save()


"""Method is to get Service Level Agreement details with next available date for place order by using siteId and 
supplierId"""
@csrf_exempt
def slaDetails(request):
    if 'user' in request.session or 'subUser' in request.session:
        body = json.loads(request.body.decode('utf-8'))
        slaObject = utilitySD.getSiteSlabasedOnSupplierIdAndSiteId(body['siteId'],body['supplierId'])
        if slaObject:
            slaJson = slaObject.slaFromSupplier
        else:
            slaJson = constants.SlaDetailsJson
        item = {}
        totalItems = []
        item['sla'] = slaJson
        date_format = "%d/%m/%Y"
        now = datetime.datetime.now()
        currentDate = datetime.datetime.strftime(now,date_format)
        orderDate = datetime.datetime.strftime(now+datetime.timedelta(days=int(slaJson['orderingSchedule'])),
                                               date_format)
        if reviewOrderCheckAvailablity(slaJson['cutOffTime'], slaJson['deliveryDays'], slaJson['holidayDate'],
                                       slaJson['orderingSchedule'], orderDate, currentDate) is False:
            nextDate = nextAvailabilityDateFinder(slaJson['cutOffTime'], slaJson['deliveryDays'],
                                                                        currentDate, orderDate,
                                                                        slaJson['orderingSchedule'],
                                                                        slaJson['holidayDate'])
            prevDate= datetime.datetime.strptime(nextDate, date_format)-datetime.timedelta(days=1)
            item['hideDate']=datetime.datetime.strftime(prevDate,date_format)
        else:
            item['hideDate'] = 1
        totalItems.append(item)
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to check whether the selected supplier is available for the delivery date that is selected by the user"""
@csrf_exempt
def reviewOrderCheckSla(request):
    if 'user' in request.session or 'subUser' in request.session:
        body = json.loads(request.body.decode('utf-8'))
        orderDate = body['deliveryDate']
        siteId = body['siteId']
        currentDate = body['currentDate']
        data = body['data']
        totalItems = []
        for dictionary in data:
            supplierId = dictionary['relId_id']
            slaObject = utilitySD.getSiteSlabasedOnSupplierIdAndSiteId(siteId, supplierId)
            dictionary['nextDeliveryDate'] = constants.Available
            if slaObject:
                slaJson = slaObject.slaFromSupplier
                if reviewOrderCheckAvailablity(slaJson['cutOffTime'],slaJson['deliveryDays'],slaJson['holidayDate'],
                                               slaJson['orderingSchedule'], orderDate,currentDate) is False:
                    dictionary['nextDeliveryDate'] = nextAvailabilityDateFinder(slaJson['cutOffTime'],
                                                                                slaJson['deliveryDays'], currentDate,
                                                                                orderDate, slaJson['orderingSchedule'],
                                                                                slaJson['holidayDate'])
            totalItems.append(dictionary)
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method to get available date for place order.Parameters- cutOffTime = List of cut off time,deliveryDays = list of
working days,holidayDate = List of holiday dates,orderingSchedule = Nuumber of days for delivery,
orderDate = Date of delivery,currentDate = Current date"""
def reviewOrderCheckAvailablity(cutOffTime,deliveryDays,holidayDate,orderingSchedule,orderDate,currentDate):
    date_format = "%d/%m/%Y"
    dateOfOrder = datetime.datetime.strptime(orderDate, date_format)
    todayDate = datetime.datetime.strptime(currentDate, date_format)
    index = dateOfOrder.isoweekday()
    if index == 7:
        index = 0
    if deliveryDays[index] == 0:
        return False
    elif (dateOfOrder - todayDate).days < int(orderingSchedule):
        return False
    elif (dateOfOrder - todayDate).days == int(orderingSchedule):
        d = datetime.datetime.now().strftime("%I:%M%p")
        currentTime = datetime.datetime.strptime(d, "%I:%M%p")
        for workingHours in cutOffTime:
            splitHours = workingHours['cutOffTime'].split("-")
            startTime = datetime.datetime.strptime(splitHours[0], "%I:%M%p")
            endTime = datetime.datetime.strptime(splitHours[1], "%I:%M%p")
            if startTime <= currentTime <= endTime:
                return dateOfOrder
        return False
    else:
        for holidayDateOne in holidayDate:
            if orderDate in holidayDateOne['holidayDate']:
                return False
        return dateOfOrder


"""Method is to get the next available for the particular supplier. Parameters- workingHours = List of cut off time,
deliveryDays = list of working days,holidayDate = List of holiday dates,orderingSchedule = Nuumber of days for delivery,
orderDate = Date of delivery,currentDate = Current date """
def nextAvailabilityDateFinder(workingHours,deliveryDays,currentDate,orderDate,orderingSchedule,holidayDate):
    date_format = "%d/%m/%Y"
    dateOfOrder = datetime.datetime.strptime(orderDate, date_format)
    while True:
        orderDate = dateOfOrder.strftime(date_format)
        deliveryNextDate = reviewOrderCheckAvailablity(workingHours,deliveryDays, holidayDate,
                                                       orderingSchedule, orderDate, currentDate)
        if deliveryNextDate is False:
            dateOfOrder += datetime.timedelta(days=1)
            continue
        else:
            break
    return deliveryNextDate.strftime(date_format)


"""Method is to convert base64 to Pdf"""
def base64ToPdf(base64String):
      return  base64.b64decode(base64String)


"""Method is to convert Pdf to base64"""
def pdfTobase64(fileNameWithLocation):
    with open(fileNameWithLocation, "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read())
    return encoded_string

"""Method to get the PO detail pdf by using orderNo"""
def getOrderPOdetail(request):
    if ('user' in request.session or 'subUser' in request.session) and 'orderNo' in request.GET and 'supplierId' in request.GET:
        pdf = utilitySD.getPdfBasedOnOrderNo(request.GET.get('orderNo'),request.GET.get('supplierId'))
        if pdf:
            byteValue = pdf.pdfField
            return HttpResponse(base64.b64decode(byteValue),content_type='application/pdf')
    return HttpResponseRedirect('/placeOrder')


"""Method is to check the cut off time period is available for current date"""
def cutOffTimeCheck(cutOffTime):
    d = datetime.datetime.now().strftime("%I:%M%p")
    currentTime = datetime.datetime.strptime(d, "%I:%M%p")
    days = 0
    for workingHours in cutOffTime:
        splitHours = workingHours['cutOffTime'].split("-")
        startTime = datetime.datetime.strptime(splitHours[0], "%I:%M%p")
        endTime = datetime.datetime.strptime(splitHours[1], "%I:%M%p")
        if startTime <= currentTime <= endTime:
            days = 0
            break
        else:
            days = 1
    return days


@csrf_exempt
def OrderDuplicating(request):
    if 'user' in request.session or 'subUser' in request.session:
        body = json.loads(request.body.decode('utf-8'))
        orderNum = body['orderNum']
        supplierId = body['supplierId']
        OrderDupNum = str(orderNum)
        alreadyOrderDupNum = utilitySD.getalreadyOrderDupNum(OrderDupNum)
        if alreadyOrderDupNum and alreadyOrderDupNum.status == constants.Active:
            return JsonResponse(
                {'status': 'success', 'success_msg': 'Oops!!!This PO already contains a duplicate copy!!!'})
        elif alreadyOrderDupNum and alreadyOrderDupNum.status == constants.Inactive:
            alreadyOrderDupNum.status = constants.Active
            alreadyOrderDupNum.save()
            return JsonResponse(
                {'status': 'success', 'success_msg': 'Created duplicate order'})
        else:
            placedOrder = OrderPlacementtoSupplier.objects.filter(ordNumber=orderNum,productId__supplierId=supplierId).values('ordToSupId')
            for prod in placedOrder:
                DupOrderPlacementtoSup = utilitySD.getOrderPlacementtoSupplierById(prod['ordToSupId'])
                DupOrderPlacementtoSup.ordNumber = str(orderNum)+"-COPY"
                DupOrderPlacementtoSup.orderType = constants.Copy
                DupOrderPlacementtoSup.pk = None
                DupOrderPlacementtoSup.save()
            dupPdfOfOrder = utilitySD.getPdfBasedOnOrderNo(orderNum,supplierId)
            dupPdfOfOrder.ordNumber = str(orderNum)+"-COPY"
            dupPdfOfOrder.pk = None
            dupPdfOfOrder.save()
            return JsonResponse(
                {'status': 'success', 'success_msg': 'Duplicate order has been created'})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


def cutOffTime(cutOffTime):
    d = datetime.datetime.now().strftime("%I:%M%p")
    currentTime = datetime.datetime.strptime(d, "%I:%M%p")
    days = 0
    for workingHours in cutOffTime:
        splitHours = workingHours['cutOffTime'].split("-")
        startTime = datetime.datetime.strptime(splitHours[0], "%I:%M%p")
        endTime = datetime.datetime.strptime(splitHours[1], "%I:%M%p")
        if startTime <= currentTime <= endTime:
            days = 0
            break
        else:
            days = 1
    return days


@csrf_exempt
def cancelOrDeletePlacedOrder(request):
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
                type = body["type"]
                orderNum = body['orderNum']
                compName = body['compName']
                deliveryAddressId = body['deliveryAddressId']
                supId = utilitySD.getSupplierByCompanyName(compName)
                supplier = utilitySD.getSupplierById(supId)
                deliveryLocation = utilitySD.getSiteBysiteAddressId(deliveryAddressId)
                slaObject = utilitySD.getSiteSlabasedOnSupplierIdAndSiteId(deliveryLocation.pk, supplier.pk)
                days = 0
                if slaObject:
                    slaJson = slaObject.slaFromSupplier
                    days = cutOffTime(slaJson['cutOffTime'])
                supplierCompany = utility.getCompanyByCompanyCode(supplier.supCompanyCode)
                l = []
                ordDate = []
                placedOrder = OrderPlacementtoSupplier.objects.filter(ordNumber=orderNum,productId__supplierId=supplier).values('ordstatus',
                                                                                                'ordNumber','orderDate')
                placedOrderList = list(placedOrder)
                currentSchema = connection.schema_name

                if type == constants.Cancel:
                    cd = [ ]
                    cancelStatus = OrderPlacementtoSupplier.objects.filter(ordNumber=orderNum,productId__supplierId=supplier).values('ordstatus',
                                                                                                                    'ordNumber','orderDate')
                    for i in cancelStatus:
                        if i['ordstatus'] == constants.Cancel:
                            cd = i['ordstatus']
                            break
                    if cd == constants.Cancel:
                        return JsonResponse(
                            {'status': 'success', 'success_msg': 'Oops!!Your Order is already cancelled'})
                    else:
                        for status in placedOrderList:
                            l.append(status["ordstatus"])
                            ordDate.append(status["orderDate"])
                        ordDat = ordDate[0]
                        today = datetime.date.today()
                        if "Accept" not in l and ordDat>today or (ordDat == today and days == 0):
                            for order in placedOrder:
                                ord = OrderPlacementtoSupplier.objects.filter(ordNumber=order["ordNumber"],productId__supplierId=supplier)
                                for i in ord:
                                    i.ordstatus = constants.Cancel
                                    i.save()
                            if supplier.relationshipStatus:
                                connection.set_schema(schema_name=supplierCompany.schemaName)
                                vieworder = OrderPlacementfromCustomer.objects.filter(ordNumber=orderNum).values(
                                    'ordstatus', 'ordNumber')
                                for order in vieworder:
                                    ord = OrderPlacementfromCustomer.objects.filter(ordNumber=order["ordNumber"])
                                    s = 0
                                    for i in ord:
                                        s = s+i.ordFrmCusId
                                        i.ordstatus = constants.Cancel
                                        i.save()
                                    OrdDet = OrderDetails.objects.filter(ordNumber=s)
                                    for orde in OrdDet:
                                        orde.ordstatus = constants.Cancel
                                        orde.save()
                                mainView.notificationView(constants.Customer, account.companyId,
                                                          str(
                                                              account.companyId.companyName) + " Cancel the order",
                                                          "cancelPlacedOrder", None, 1)
                                connection.set_schema(schema_name=currentSchema)

                                return JsonResponse(
                                    {'status': 'success', 'success_msg': 'Order has been cancelled'})
                            else:
                                mainView.notificationView(constants.Customer, account.companyId,
                                                          str(
                                                              account.companyId.companyName) + " Cancel the order",
                                                          "cancelPlacedOrder", None, 1)
                                return JsonResponse(
                                    {'status': 'success', 'success_msg': 'Order has been cancelled'})
                        else:
                            return JsonResponse(
                                {'status': 'success', 'success_msg': 'Oops!!Your Order is in progress.Cannot be cancelled'})

                else:
                    for status in placedOrderList:
                        l.append(status["ordstatus"])
                        ordDate.append(status["orderDate"])
                    ordDat = ordDate[0]
                    today = datetime.date.today()
                    if "Accept" not in l and ordDat > today or (ordDat == today and days == 0):
                        for order in placedOrder:
                            ord = OrderPlacementtoSupplier.objects.filter(ordNumber=order["ordNumber"],productId__supplierId=supplier)
                            for i in ord:
                                i.status = constants.Inactive
                                i.save()
                        if supplier.relationshipStatus:
                            connection.set_schema(schema_name=supplierCompany.schemaName)
                            vieworder = OrderPlacementfromCustomer.objects.filter(ordNumber=orderNum).values(
                                'ordstatus', 'ordNumber')
                            for order in vieworder:
                                ord = OrderPlacementfromCustomer.objects.filter(ordNumber=order["ordNumber"])
                                for i in ord:
                                    i.status = constants.Inactive
                                    i.save()
                            mainView.notificationView(constants.Customer, account.companyId,
                                                      str(account.companyId.companyName) + " deleted the order",
                                                      "cancelOrDeletePlacedOrder", None, 1)
                            connection.set_schema(schema_name=currentSchema)
                            return JsonResponse(
                                {'status': 'success', 'success_msg': 'Order has been deleted'})
                        else:
                            return JsonResponse(
                                {'status': 'success', 'success_msg': 'Order has been deleted'})
                    else:
                        return JsonResponse(
                            {'status': 'success', 'success_msg': 'Oops!!Your Order is in progress.Cannot be deleted'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def addNewPlaceOrder(request):
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
                if utility.checkEntryCountBasedOnPlanAndFeatures(utility.getCompanyBySchemaName(connection.schema_name),
                                                                 'ShoppingCart',
                                                                 utilitySD.getCountOftheModelByModelName(
                                                                     "ShoppingCart")):
                    currentCompany = utility.getCompanyBySchemaName(connection.schema_name)
                    customerUser = utility.getUserByCompanyId(currentCompany.companyId)
                    body = json.loads(request.body.decode('utf-8'))
                    orderNum = body['orderNum']
                    compName = body['compName']
                    deliveryAddressId = body['deliveryAddressId']
                    expectedTime = body['expectedTime']
                    deliveryLocation = utilitySD.getSiteBySiteId(deliveryAddressId)
                    supplier = utilitySD.getSupplierByCompanyName(compName)
                    slaFromSupplier = utilitySD.getSiteSlabasedOnSupplierIdAndSiteId(deliveryAddressId,supplier.pk)
                    if slaFromSupplier:
                        slaJson = slaFromSupplier.slaFromSupplier
                    else:
                        slaJson = constants.SlaDetailsJson
                    date_format = "%d/%m/%Y"
                    days = cutOffTimeCheck(slaJson['cutOffTime'])
                    now = datetime.datetime.now()
                    currentDate = datetime.datetime.strftime(now, date_format)
                    if days == 1:
                        now += datetime.timedelta(days=1)
                    orderDate = datetime.datetime.strftime(now,
                                                           date_format)
                    deliveryDate = nextAvailabilityDateFinder(slaJson['cutOffTime'], slaJson['deliveryDays'],
                                                              currentDate, orderDate, slaJson['orderingSchedule'],
                                                              slaJson['holidayDate'])
                    placedOrder = OrderPlacementtoSupplier.objects.filter(ordNumber=orderNum,productId__supplierId=supplier).values(
                        'productId__itemCode','ordToSupId','quantity')
                    dateOfOrder = datetime.datetime.strptime(orderDate, date_format)
                    orderDate = datetime.datetime.strftime(dateOfOrder, "%Y-%m-%d")
                    total = 0
                    for prod in placedOrder:
                        productPrice = SupplierProductCatalog.objects.get(itemCode=prod['productId__itemCode'],
                                                                          supplierId=supplier).purchasePrice
                        total = total+float(productPrice)*float(prod['quantity'])
                    totalPrice = total
                    shopCart = openShopppingCart(deliveryDate, expectedTime, totalPrice, deliveryLocation)
                    supplierName = supplier.supCompanyName.replace(' ', '')[:5]
                    supplierCompany = utility.getCompanyByCompanyCode(supplier.supCompanyCode)
                    orderNumber = str(utility.oTorderNumberGenerator(supplier,supplierName))
                    pdfName = "PO-" + currentCompany.companyName.replace(' ', '')[:5].upper() + ".pdf"
                    orderDetail = {}
                    orderDetail['companyImage'] = settings.HTTP + settings.IP_ADDRESS + ':' + settings.PORT + \
                                                  '/media/' + str( currentCompany.companyImage)
                    if (orderDetail['companyImage'] == settings.HTTP + settings.IP_ADDRESS + ':' +
                            settings.PORT + '/media/'):
                        base = os.path.dirname(os.path.abspath("companyLogo.png"))+'/__shared__/images/companyLogo.png'
                        defFile = base.replace("\\", '/')
                        orderDetail['companyImage'] = defFile
                    orderDetail['customerEmail'] = customerUser.email
                    orderDetail['customerContactNo'] = customerUser.contactNo
                    orderDetail['orderNumber'] = orderNumber
                    orderDetail['date'] = orderDate
                    orderDetail['deliveryDate'] = deliveryDate
                    orderDetail['expectedTime'] = expectedTime
                    currentSchema = connection.schema_name
                    for prod in placedOrder:
                        productPrice = SupplierProductCatalog.objects.get(itemCode=prod['productId__itemCode'],
                                                                          supplierId=supplier).purchasePrice
                        NewOrderPlacementtoSup = utilitySD.getOrderPlacementtoSupplierById(prod['ordToSupId'])
                        NewOrderPlacementtoSup.ordNumber = orderNumber
                        NewOrderPlacementtoSup.price = productPrice
                        NewOrderPlacementtoSup.shopCartId = shopCart
                        NewOrderPlacementtoSup.orderDate = orderDate
                        NewOrderPlacementtoSup.ordstatus = constants.Pending
                        NewOrderPlacementtoSup.pk = None
                        NewOrderPlacementtoSup.save()
                    placedOrd = OrderPlacementtoSupplier.objects.filter(ordNumber=orderNumber,productId__supplierId=supplier).values(
                        'quantity', 'price','shopCartId__totalPrice',itemCode=F('productId__itemCode'),
                        itemName=F('productId__itemName'),itemCategory=F('productId__itemCategory'),
                        itemCategory__prtCatName=F('productId__itemCategory__prtCatName'),
                        relId_id=F('productId__supplierId'),id=F('productId__productId'),priceUnit__type=F('priceUnit'),
                        uOm__type=F('uOm__quantityTypeCode'),totalPrice=F('productId__discountPrice'))
                    lis = []
                    for x in placedOrd:
                        x['tot'] = float(x['totalPrice']) * float(x['quantity'])
                        lis.append(x)
                    totalpri = 0
                    for i in placedOrd:
                        totalpri = float(i['shopCartId__totalPrice'])
                    orderDetail['totalPrice'] = totalpri
                    orderDetail['tax'] = '7%'
                    orderDetail['totalTax'] = round((float((orderDetail['totalPrice'])) * 7) / 100, 2)
                    orderDetail['totalPriceWithTax'] = round(float(orderDetail['totalTax'] + float(totalpri)), 2)
                    supplierAddressObject = {}
                    supplierAddressObject['supCompanyCode'] = supplier.supCompanyCode
                    supplierAddressObject['supCompanyName'] = supplier.supCompanyName
                    supplierAddressObject['supplier_unit1'] = supplier.supUnit1
                    supplierAddressObject['supplier_unit2'] = supplier.supUnit2
                    supplierAddressObject['supplier_address_Line1'] = supplier.supAddress_Line1
                    supplierAddressObject['supplier_address_Line2'] = supplier.supAddress_Line2
                    supplierAddressObject['supplier_state'] = supplier.supState
                    supplierAddressObject['supplier_country'] = supplier.supCountry
                    supplierAddressObject['supplier_postalCode'] = supplier.supPostalCode
                    supplierAddressObject['supEmail'] = supplier.supEmail
                    html = createPlaceOrderHtml(currentCompany, supplierAddressObject, lis, orderDetail,deliveryLocation)
                    pdf = mainView.htmlToPdfConvertion(html, pdfName)
                    base64Value = pdfTobase64(MEDIA_ROOT + pdf)
                    pdfDetail = pdfDetailsForPlacedOrder()
                    pdfDetail.ordNumber = orderNumber
                    pdfDetail.pdfField = base64Value
                    pdfDetail.supplierId = supplier
                    pdfDetail.save()
                    if supplier.relationshipStatus:
                        connection.set_schema(schema_name=supplierCompany.schemaName)
                        viewOrder = OrderPlacementfromCustomer.objects.filter(ordNumber=orderNum).values()
                        cusId = utilitySD.getCustomerByCompanyName(currentCompany.companyName)
                        for prod in viewOrder:
                            NewOrderPlacementfromCus = utilitySD.getOrderPlacementfromCustomerById(prod['ordFrmCusId'])
                            NewOrderPlacementfromCus.ordNumber = orderNumber
                            NewOrderPlacementfromCus.expectedDate = deliveryDate
                            NewOrderPlacementfromCus.expectedTime = expectedTime
                            NewOrderPlacementfromCus.orderDate =  orderDate
                            NewOrderPlacementfromCus.pdfField = base64Value
                            NewOrderPlacementfromCus.ordstatus = constants.Pending
                            NewOrderPlacementfromCus.pk = None
                            NewOrderPlacementfromCus.save()
                            order = OrderDetails.objects.filter(ordNumber=prod['ordFrmCusId']).values()
                            for ord in order:
                                prodPrice = CustomerProductCatalog.objects.get(itemName=ord['itemName'],
                                                                               customerId=cusId).salesPrice
                                orderDet = OrderDetails.objects.get(itemCode=ord['itemCode'],
                                                                    ordNumber=prod['ordFrmCusId'])
                                orderDet.ordNumber = NewOrderPlacementfromCus
                                orderDet.price = prodPrice
                                orderDet.ordstatus = constants.Pending
                                orderDet.pk = None
                                orderDet.save()
                        connection.set_schema(schema_name=currentSchema)
                        return JsonResponse(
                            {'status': 'success', 'success_msg': 'New Order has been Placed Successfully'})
                    else:
                        sendEmail = supplier.supEmail
                        if supplier.supCommunicationEmail:
                            sendEmail = supplier.supCommunicationEmail
                        mainView.sendingEmail(request, supplier, sendEmail, currentCompany.companyName,
                                              "orderpomail.html",
                                              "Order placement from "+currentCompany.companyName.upper(),None,pdf,None)
                        os.remove(MEDIA_ROOT + pdf)
                        return JsonResponse(
                            {'status': 'success', 'success_msg': 'Mail Sent Successfully'})
                else:
                    return JsonResponse({'status': 'error',
                                         'error_msg': 'Your Purchased Order Placement Limit Is Exceeded'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error_msg': "Your don't have access for this action"})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': "Your plan has suspended"})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Get the placed order information by using orderNumber"""
@csrf_exempt
def fetchDataByOrderNumber(request):
   if 'user' in request.session or 'subUser' in request.session:
       body = json.loads(request.body.decode('utf-8'))
       orderNumber = body["orderNum"]
       supplierId = body["supplierId"]
       placedOrdData = OrderPlacementtoSupplier.objects.filter(ordNumber=orderNumber,productId__supplierId=supplierId).values(
           'quantity', 'price','shopCartId__totalPrice',itemCode=F('productId__itemCode'),
           itemName=F('productId__itemName'),itemCategory=F('productId__itemCategory'),
           itemCategory__prtCatName=F('productId__itemCategory__prtCatName'),relId_id=F('productId__supplierId'),
           id=F('productId__productId'),priceUnit__type=F('priceUnit__currencyTypeCode'),
           uOm__type=F('uOm__quantityTypeCode'),currentPrice=F('productId__discountPrice'))
       return JsonResponse({'status': 'success', 'placedOrdData': list(placedOrdData)})
   return JsonResponse(
           {'status': 'error', 'error_msg': 'sessionexpired',
            'redirect_url': settings.HTTP + request.get_host() + '/login'})