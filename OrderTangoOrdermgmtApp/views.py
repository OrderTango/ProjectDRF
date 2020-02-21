from django.http import JsonResponse,HttpResponse,HttpResponseRedirect
from OrderTangoApp.forms import *
import datetime
import os, json,base64
from django.views.decorators.csrf import csrf_exempt
from OrderTangoApp import utility, constants,views as mainView
from OrderTangoSubDomainApp import utilitySD
from OrderTangoOrdermgmtApp.models import *
from OrderTangoOrderFulfilmtApp.models import *
from OrderTango.settings import MEDIA_ROOT
from OrderTangoOrdermgmtApp import utilityOM
from django.template.loader import render_to_string

def createPlaceOrderHtml(userObject,supplierObject,orderObjects, orderDetail):
    return render_to_string('poorder.html', {'userObject':userObject,'supplierObject':supplierObject,
                                'orderArray':orderObjects,'orderDetail':orderDetail})

@csrf_exempt
def orderPlacement(request):
    if request.method == 'POST' and ('user' in request.session or 'subUser' in request.session):
        currentCompany = utility.getCompanyBySchemaName(connection.schema_name)
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        deliveryAddressId = body['deliveryAddressId']
        deliveryDate = body['deliveryDate']
        expectedTime = body['expectedTime']
        totalPrice = body['totalPrice']
        data = body['data']
        deliveryLocation = utilitySD.getSiteBysiteAddressId(deliveryAddressId)
        shopCart = openShopppingCart(deliveryDate, expectedTime, totalPrice, deliveryLocation)
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
                        objects['totalPrice'] = int(objects['quantity']) * int(objects['price'])
                        supplierTotalPrice = supplierTotalPrice + (int(objects['quantity']) * int(objects['price']))

                        if 'nextDeliveryDate' in objects:
                            dateOfOrder = objects['nextDeliveryDate']
                            if objects['nextDeliveryDate'] == constants.Available:
                                dateOfOrder = deliveryDate
                        arrayData.append(objects)
               # print(supplierTotalPrice)
                object['orderData'] = arrayData
                object['supplierTotalPrice'] = supplierTotalPrice
                object['dateOfOrder'] = dateOfOrder
                newArray.append(object)
        for object in newArray:
           supplier = utilitySD.getSupplierById(object['relId_id'])
           customerUser = utility.getUserByCompanyId(currentCompany.companyId)
           supplierName = supplier.supCompanyName.replace(' ','')[:5]
           pdfName = "PO-"+currentCompany.companyName.replace(' ','')[:5].upper()+".pdf"
           orderNumber = "OT" + supplierName.upper()+str(utility.oTorderNumberGenerator())
           now = datetime.datetime.now()
           orderDetail = {}
           orderDetail['companyImage'] = settings.HTTP + settings.IP_ADDRESS + ':' + settings.PORT+'/media/'+str(currentCompany.companyImage)
           orderDetail['customerEmail'] = customerUser.email
           orderDetail['customerContactNo'] = customerUser.contactNo
           orderDetail['orderNumber'] = orderNumber
           orderDetail['date'] = now.strftime("%d/%m/%Y")
           orderDetail['deliveryDate'] = object['dateOfOrder']
           orderDetail['expectedTime'] = expectedTime
           orderDetail['totalPrice'] = object['supplierTotalPrice']
           orderDetail['tax'] = '7%'
           orderDetail['totalTax'] = int(( object['supplierTotalPrice'] * 7 ) / 100)
           orderDetail['totalPriceWithTax'] = int(orderDetail['totalTax'] + object['supplierTotalPrice'])
           print(orderDetail['totalPriceWithTax'])
           for dictionary in object['orderData']:
               customerItem = SupplierProductCatalog.objects.get(itemCode__iexact=dictionary['itemCode'], supplierId=supplier)
               placToSup = OrderPlacementtoSupplier()
               placToSup.productId = customerItem
               placToSup.ordNumber = orderNumber
               placToSup.shopCartId = shopCart
               if supplier.relationshipStatus:
                   placToSup.connectedStatus = True
               orderSavetoCustomerOrSupplier(placToSup, dictionary)
           html = createPlaceOrderHtml(currentCompany, supplier, object['orderData'], orderDetail)
           pdf = mainView.htmlToPdfConvertion(html, pdfName)
           base64Value = pdfTobase64(MEDIA_ROOT+pdf)
           pdfDetail = pdfDetailsForPlacedOrder()
           pdfDetail.ordNumber = orderNumber
           pdfDetail.pdfField = base64Value
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
               customerDeliveryLoc = utilitySD.getCustomerSiteBySiteId(deliveryAddressId,customer.customerId)
               if customerDeliveryLoc:
                   site = customerDeliveryLoc.mappedSites
               else:
                   site = utilitySD.getSiteBysiteAddressId(1)
               placFromCus.customerId = customer
               placFromCus.ordNumber = orderNumber
               placFromCus.expectedDate = object['dateOfOrder']
               placFromCus.expectedTime = expectedTime
               placFromCus.siteId = site
               placFromCus.orderDate = now
               placFromCus.pdfField = base64Value
               placFromCus.connectedStatus = True
               placFromCus.save()
               for dictionary in object['orderData']:
                   orderDetails = OrderDetails()
                   orderDetails.ordNumber = placFromCus
                   orderDetails.itemCode = dictionary['itemCode']
                   orderDetails.itemName = dictionary['itemName']
                   orderDetails.itemCategory = dictionary['itemCategory']
                   orderSavetoCustomerOrSupplier(orderDetails, dictionary)
               mainView.notificationView(request, customer.customerId,
                                          str(customer.cusCompanyName)+ " placed an order",
                                         " ")
               connection.set_schema(schema_name=currentSchema)
           else:
               sendEmail = supplier.supEmail
               if supplier.supAlterNateEmail:
                   sendEmail = supplier.supAlterNateEmail
               mainView.sendingEmail(request, supplier,sendEmail , currentCompany.companyName, "orderpomail.html",
                                     "Order placement from " + currentCompany.companyName.upper(), None, pdf, None)
               os.remove(MEDIA_ROOT + pdf)
        return JsonResponse({'status': 'success', 'success_msg': 'Order placement successfully completed'})
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


def orderSavetoCustomerOrSupplier(table, dictionary):
    table.quantity = dictionary['quantity']
    table.actualQuantity = dictionary['quantity']
    table.price = dictionary['price']
    table.priceUnit = CurrencyType.objects.get(currencyTypeCode=dictionary['priceUnit__type'])
    table.uOm = QuantityType.objects.get(quantityTypeCode=dictionary['uOm__type'])
    table.orderDate = datetime.datetime.today()
    table.save()



@csrf_exempt
def slaDetails(request):
    if 'user' in request.session or 'subUser' in request.session:
        body = json.loads(request.body.decode('utf-8'))
        slaObject = utilitySD.getSiteSlabasedOnSupplierIdAndSiteId(body['siteId'],body['supplierId'])
        if slaObject:
            sla = slaObject.slaFromSupplier
        else:
            sla = constants.SlaDetailsJson
        item = {}
        totalItems = []
        item['sla'] = sla
        totalItems.append(item)
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


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
                if reviewOrderCheckAvailablity(slaJson['cutOffTime'],slaJson['deliveryDays'],slaJson['holidayDate'],slaJson['orderingSchedule'], orderDate,currentDate) is False:
                    dictionary['nextDeliveryDate'] = nextAvailabilityDateFinder(slaJson['cutOffTime'],slaJson['deliveryDays'], currentDate, orderDate, slaJson['orderingSchedule'], slaJson['holidayDate'])
            totalItems.append(dictionary)
        return JsonResponse(
            {'status': 'success', 'totalItems': totalItems})
    return JsonResponse({'status': 'error', 'error_msg': 'sessionexpired',
                         'redirect_url': settings.HTTP + request.get_host() + '/login'})


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


def base64ToPdf(base64String):
      return  base64.b64decode(base64String)

def pdfTobase64(fileNameWithLocation):
    with open(fileNameWithLocation, "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read())
    return encoded_string

def getOrderPOdetail(request):
    if ('user' in request.session or 'subUser' in request.session) and 'orderNo' in request.GET:
        pdf = utilityOM.getPdfBasedOnOrderNo(request.GET.get('orderNo'))
        if pdf:
            byteValue = pdf.pdfField
            return HttpResponse(base64.b64decode(byteValue),content_type='application/pdf')
    return HttpResponseRedirect('/placeOrder')
