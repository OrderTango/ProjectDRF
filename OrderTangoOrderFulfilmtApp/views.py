from django.http import JsonResponse
import json
import datetime
import os
from OrderTangoApp import views as mainView
from OrderTangoOrderFulfilmtApp.models import *
from OrderTangoOrdermgmtApp.models import *
from OrderTangoSubDomainApp.models import SubuserSiteAssign
from OrderTangoSubDomainApp import utilitySD
from django.views.decorators.csrf import csrf_exempt
from OrderTangoApp import utility, constants
from django.db.models import  Count, F
from django.db import connection
from django.conf import settings
from OrderTango.settings import MEDIA_ROOT
from OrderTangoOrdermgmtApp.views import createPlaceOrderHtml,pdfTobase64


"""Method is to get all the orders placed by the customers and also get the particular order details by using orderNo"""
@csrf_exempt
def viewPlacedOrderDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        detailList = []
        if request.body:
            a = request.body.decode('utf-8')
            body = json.loads(a)
            if 'ordNumber' in body:
                ordNumber = body['ordNumber']
                detailList = OrderPlacementfromCustomer.objects.filter(ordNumber=ordNumber,status=constants.Active
                                                                       ).values(
                    'customerId', 'orderdetail__ordstatus','ordNumber', 'connectedStatus',
                    itemCode=F('orderdetail__itemCode'),itemName=F('orderdetail__itemName'),
                    itemCategory=F('orderdetail__itemCategory'),quantity=F('orderdetail__quantity'),
                    price=F('orderdetail__price'),actualQuantity=F('orderdetail__actualQuantity'),
                    comment=F('orderdetail__comment'),priceUnit=F('orderdetail__priceUnit__currencyTypeCode'),
                    goodsReceive=F('orderdetail__goodsReceive'),goodsIssue=F('orderdetail__goodsIssue'),
                    uOm=F('orderdetail__uOm__quantityTypeCode'))
        elif 'subUser' in request.session:
            subusr = utility.getObjectFromSession(request, 'subUser')
            subSites = SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=subusr).values(
                'subuserSiteAssignSites__siteAddress')
            detailList = OrderPlacementfromCustomer.objects.filter(ordFrmCusId__in=subSites,
                                                                   status=constants.Active).values(
                'orderDate','ordNumber','connectedStatus','customerId', 'expectedDate', 'expectedTime',
                'customer_address_Line1','customer_address_Line2','customer_unit1','customer_unit2',
                'customer_postalCode','customer_country__countryName','customer_state__stateName',
                                                                   'customerId__cusCompanyName').annotate(
                customerIdCount=Count('customerId'), orderDateCount=Count('orderDate')).order_by('expectedDate')
        elif 'user' in request.session:
            detailList = OrderPlacementfromCustomer.objects.filter(status=constants.Active).values(
                'orderDate', 'ordNumber', 'connectedStatus','customerId', 'expectedDate', 'expectedTime',
                'customer_address_Line1','customer_address_Line2','customer_unit1','customer_unit2',
                'customer_postalCode','customer_country__countryName','customer_state__stateName',
                                                                   'customerId__cusCompanyName').annotate(
                customerIdCount=Count('customerId'), orderDateCount=Count('orderDate')).order_by('expectedDate')
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse({'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No orders found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


"""Method is to get all the orders placed to suppliers and also get the particular order details by using orderNo"""
@csrf_exempt
def viewOrderDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        detailList = []
        totalList = []
        if request.body:
            a = request.body.decode('utf-8')
            body = json.loads(a)
            if 'ordNumber' in body:
                ordNumber = body['ordNumber']
                supplierId = body['supplierId']
                detailList = OrderPlacementtoSupplier.objects.filter(ordNumber=ordNumber,productId__supplierId=supplierId,
                                                                     status=constants.Active).values(
                    'goodsIssue','ordNumber','productId__itemCode','productId__itemName','productId__itemCategory',
                    'quantity','price','connectedStatus','goodsReceive','actualQuantity','ordstatus','comment',
                    priceUnit__type=F('priceUnit__currencyTypeCode'),uOm__type=F('uOm__quantityTypeCode'),
                    productId__relId__trdersId__companyName=F('productId__supplierId__supCompanyName'),
                    supplierId=F('productId__supplierId'))
                totalList = list(detailList)
        elif 'subUser' in request.session:
            subusr = utility.getObjectFromSession(request, 'subUser')
            subSites = SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=subusr).values(
                'subuserSiteAssignSites__siteId')
            detailList = OrderPlacementtoSupplier.objects.filter(shopCartId__deliveryLocation__in=subSites,
                                                                 status=constants.Active).values(
                'orderDate', 'ordNumber', 'connectedStatus','shopCartId__expectedDate','shopCartId__totalPrice','productId__supplierId',
                'productId__supplierId__supCompanyName','shopCartId__deliveryLocation','shopCartId__expectedTime',
                                                                 ).annotate(
                customerIdCount=Count('ordNumber'), orderDateCount=Count('orderDate'))
            totalList = list(detailList)
            totalList.sort(key=lambda x: datetime.datetime.strptime(x['shopCartId__expectedDate'], "%d/%m/%Y"))
        elif 'user' in request.session:
            detailList = OrderPlacementtoSupplier.objects.filter(status=constants.Active).values(
                'orderDate','ordNumber','connectedStatus','shopCartId__expectedDate','shopCartId__totalPrice','productId__supplierId',
                'productId__supplierId__supCompanyName','shopCartId__deliveryLocation','shopCartId__expectedTime',
                                                                 ).annotate(customerIdCount=Count('ordNumber'),
                                      orderDateCount=Count('orderDate'))
            totalList = list(detailList)
            totalList.sort(key=lambda x: datetime.datetime.strptime(x['shopCartId__expectedDate'], "%d/%m/%Y"))
        if detailList:
            item['totalItem'] = totalList
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems, 'success_msg': 'Updated Successfully'})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No orders found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})

@csrf_exempt
def orderFulfillmentSupplier(request):
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
                a = request.body.decode('utf-8')
                body = json.loads(a)
                ordNumber = body['ordNumber']
                customerId = body['customerId']
                itemCode = body['itemCode']
                customer = utilitySD.getCustomerById(customerId)
                ordNumSup = OrderDetails.objects.get(ordNumber__ordNumber=ordNumber,itemCode=itemCode,
                                                     ordNumber__customerId=customer)
                OrderPlacementtoSupplierUpdate(ordNumSup, body)
                if customer.relationshipStatus:
                    currentSchema = connection.schema_name
                    userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
                    connection.set_schema(schema_name=userCustomerSchema)
                    supplierId =  utilitySD.getSupplierByCompanyName(account.companyId.companyName)
                    supplier = utilitySD.getSupplierById(supplierId)
                    ordNumCus = OrderPlacementtoSupplier.objects.get(ordNumber=ordNumber,productId__supplierId=supplierId,productId__itemCode=itemCode)
                    OrderPlacementtoSupplierUpdate(ordNumCus, body)
                    if ordNumCus.ordstatus == 'Pending':
                        desc = str(supplier.supCompanyName) +" able to deliver only " + str(ordNumCus.goodsIssue) +" products."
                        mainView.notificationView(constants.Customer, customer.pk, desc, "OrderPending ", None, 1)
                    elif ordNumCus.ordstatus == 'Closed':
                        desc = str(supplier.supCompanyName) +" Closed your order "
                        mainView.notificationView(constants.Customer, customer.pk, desc, "OrderClosed", None, 1)
                    elif ordNumCus.ordstatus == 'Reject':
                        desc = str(supplier.supCompanyName) +" "+ordNumCus.ordstatus+"ed your order "
                        mainView.notificationView(constants.Customer, customer.pk, desc, "OrderReject", None, 1)
                    else:
                        desc = str(supplier.supCompanyName) +" "+ordNumCus.ordstatus+"ed your order "
                        mainView.notificationView(constants.Customer, customer.pk, desc, "OrderAccept", None, 1)
                    connection.set_schema(schema_name=currentSchema)
                return JsonResponse({'status': 'success', 'success_msg': 'Order Updated Successfully'})
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


def OrderPlacementtoSupplierUpdate(ordNum, body):
    ordNum.ordstatus = body['status']
    ordNum.goodsIssue = body['goodsIssue']
    ordNum.save()


@csrf_exempt
def orderFulfillmentCustomer(request):
    if 'user' in request.session or 'subUser' in request.session:
        if 'user' in request.session:
            mainUser = utility.getObjectFromSession(request, 'user')
            userCompany = mainUser.userCompanyId
            check = True
        else:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            userCompany = utility.getCompanyBySchemaName(connection.schema_name)
            check = utility.checkRequesURLisPresentForSubUser(currentUser, "orderFulfillmentSupplier")
        account = utility.getoTAccountByCompany(userCompany)
        if not account.planSuspended:
            if check:
                a = request.body.decode('utf-8')
                body = json.loads(a)
                ordNumber = body['ordNumber']
                supplierId = body['supplierId']
                itemCode = body['itemCode']
                supplier = utilitySD.getSupplierById(supplierId)
                ordNumCus = OrderPlacementtoSupplier.objects.get(ordNumber=ordNumber, productId__itemCode=itemCode)
                ordNumCus.quantity = body['qty']
                if body['goodsReceive'] and body['goodsReceive'] != '':
                    ordNumCus.goodsReceive = body['goodsReceive']
                if body['goodsIssue'] and body['goodsIssue'] != '':
                    ordNumCus.goodsIssue = body['goodsIssue']
                if body['status'] and body['status'] != '':
                    ordNumCus.ordstatus = body['status']
                ordNumCus.save()
                currentCompany = utility.getCompanyBySchemaName(connection.schema_name)
                customerUser = utility.getUserByCompanyId(currentCompany.companyId)
                pdfName = "PO-" + currentCompany.companyName.replace(' ', '')[:5].upper() + ".pdf"
                supplier = utilitySD.getSupplierById(supplierId)
                date_format = "%d/%m/%Y"
                now = datetime.datetime.now()
                orderDate = datetime.datetime.strftime(now,
                                                       date_format)
                dateOfOrder = datetime.datetime.strptime(orderDate, date_format)
                orderDate = datetime.datetime.strftime(dateOfOrder, "%Y-%m-%d")
                orderDetail = {}
                orderDetail[
                    'companyImage'] = settings.HTTP + settings.IP_ADDRESS + ':' + settings.PORT + '/media/' + str(
                    currentCompany.companyImage)
                if (orderDetail[
                    'companyImage'] == settings.HTTP + settings.IP_ADDRESS + ':' + settings.PORT + '/media/'):
                    base = os.path.dirname(os.path.abspath("companyLogo.png")) + '/__shared__/images/companyLogo.png'
                    defFile = base.replace("\\", '/')
                    orderDetail['companyImage'] = defFile
                orderDetail['customerEmail'] = customerUser.email
                orderDetail['customerContactNo'] = customerUser.contactNo
                orderDetail['orderNumber'] = ordNumber
                orderDetail['date'] = orderDate
                placedOrd = OrderPlacementtoSupplier.objects.filter(ordNumber=ordNumber).values('quantity', 'price',
                                                                          'shopCartId__totalPrice',
                                                                        'shopCartId__expectedDate',
                                                                          itemCode=F(
                                                                              'productId__itemCode'),
                                                                          itemName=F(
                                                                              'productId__itemName'),
                                                                          itemCategory=F(
                                                                              'productId__itemCategory'),
                                                                          itemCategory__prtCatName=F(
                                                                              'productId__itemCategory__prtCatName'),
                                                                          relId_id=F(
                                                                              'productId__supplierId'),
                                                                          id=F(
                                                                              'productId__productId'),
                                                                          priceUnit__type=F(
                                                                              'priceUnit'),
                                                                          uOm__type=F(
                                                                              'uOm__quantityTypeCode'),
                                                                          totalPrice=F(
                                                                              'productId__discountPrice')
                                                                          )
                lis = []
                deliveryDate = []
                for x in placedOrd:
                    x['tot'] = float(x['totalPrice']) * float(x['quantity'])
                    deliveryDate.append(x['shopCartId__expectedDate'])
                    lis.append(x)
                totalprice = 0
                for x in lis:
                    totalprice = totalprice+int(x['tot'])
                orderDetail['totalPrice'] = totalprice
                orderDetail['tax'] = '7%'
                orderDetail['totalTax'] = round((float((orderDetail['totalPrice'])) * 7) / 100, 2)
                orderDetail['totalPriceWithTax'] = round(float(orderDetail['totalTax'] + float(totalprice)), 2)
                orderDetail['deliveryDate'] = deliveryDate[0]
                deliveryLocation = Sites.objects.get(siteId=1)
                html = createPlaceOrderHtml(currentCompany, supplier, lis, orderDetail, deliveryLocation)
                pdf = mainView.htmlToPdfConvertion(html, pdfName)
                base64Value = pdfTobase64(MEDIA_ROOT + pdf)
                pdfDetail = pdfDetailsForPlacedOrder.objects.get(ordNumber=ordNumber,supplierId=supplier)
                pdfDetail.ordNumber = ordNumber
                pdfDetail.pdfField = base64Value
                pdfDetail.save()
                if supplier.relationshipStatus and ordNumCus.connectedStatus:
                    currentSchema = connection.schema_name
                    userCustomerSchema = utility.getCompanyByCompanyCode(supplier.supCompanyCode).schemaName
                    connection.set_schema(schema_name=userCustomerSchema)
                    customer = utilitySD.getCustomerByConnectionCode(supplier.connectionCode)
                    ordNumSup = OrderDetails.objects.get(ordNumber__ordNumber=ordNumber, itemCode=itemCode,
                                                         ordNumber__customerId=customer)
                    ordNumSup.quantity = body['qty']
                    if body['goodsReceive'] and body['goodsReceive'] != '':
                        ordNumSup.goodsReceive = body['goodsReceive']
                    ordNumSup.save()
                    connection.set_schema(schema_name=currentSchema)
                return JsonResponse({'status': 'success', 'success_msg': 'Order Updated Successfully'})
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



