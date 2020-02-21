from django.http import JsonResponse
import os, io, json
from OrderTangoOrderFulfilmtApp.models import *
from OrderTangoOrdermgmtApp.models import *
from OrderTangoSubDomainApp.models import *
from OrderTangoSubDomainApp import utilitySD
from django.views.decorators.csrf import csrf_exempt
from OrderTangoApp import utility, constants,views as mainView
from django.db.models import Q, Count, F
from django.db import connection
from django.conf import settings
# Create your views here.

@csrf_exempt
def viewPlacedOrderDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
            loginUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
            subusr = Subuser.objects.get(userName=loginUser.userName)
            subSites = SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=subusr).values(
                'subuserSiteAssignSites__siteAddress')
            if request.body:
                a = request.body.decode('utf-8')
                # would take a file-like object, read the data from that object, and use that string to create an object
                body = json.loads(a)
                if 'ordNumber' in body:
                    ordNumber = body['ordNumber']

                    detailList = OrderPlacementfromCustomer.objects.filter(ordNumber=ordNumber,
                                                                           ).values('customerId','orderdetail__ordstatus',
                        'ordNumber','connectedStatus', itemCode=F('orderdetail__itemCode'), itemName=F('orderdetail__itemName'),
                                                                                     itemCategory=F('orderdetail__itemCategory'), quantity=F('orderdetail__quantity'),
                                                                            price=F('orderdetail__price'), actualQuantity=F('orderdetail__actualQuantity'),
                                    comment=F('orderdetail__comment'),priceUnit = F('orderdetail__priceUnit__currencyTypeCode'),goodsReceive=F('orderdetail__goodsReceive'),
                                                                                    goodsIssue=F('orderdetail__goodsIssue'),uOm = F('orderdetail__uOm__quantityTypeCode') )
            else:
                detailList = OrderPlacementfromCustomer.objects.filter(ordFrmCusId__in=subSites).values('orderDate','ordNumber','connectedStatus',
                                                                       'customerId', 'expectedDate', 'expectedTime',
                                                                       'customer_address_Line1',
                                                                       'customer_address_Line2',
                                                                       'customer_unit1',
                                                                       'customer_unit2',
                                                                       'customer_postalCode',
                                                                       'customer_country__countryName',
                                                                       'customer_state__stateName',
                                                                       'customerId__cusCompanyName').annotate(
                    customerIdCount=Count('customerId'), orderDateCount=Count('orderDate')).order_by('expectedDate')
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
            if request.body:
                a = request.body.decode('utf-8')
                # would take a file-like object, read the data from that object, and use that string to create an object
                body = json.loads(a)
                if 'ordNumber' in body:
                    ordNumber = body['ordNumber']
                    detailList = OrderPlacementfromCustomer.objects.filter(ordNumber=ordNumber,
                                                                           ).values('customerId',
                                                                                    'orderdetail__ordstatus',
                                                                                    'ordNumber', 'connectedStatus',
                                                                                    itemCode=F('orderdetail__itemCode'),
                                                                                    itemName=F('orderdetail__itemName'),
                                                                                    itemCategory=F(
                                                                                        'orderdetail__itemCategory'),
                                                                                    quantity=F('orderdetail__quantity'),
                                                                                    price=F('orderdetail__price'),
                                                                                    actualQuantity=F(
                                                                                        'orderdetail__actualQuantity'),
                                                                                    comment=F('orderdetail__comment'),
                                                                                    priceUnit=F(
                                                                                        'orderdetail__priceUnit__currencyTypeCode'),
                                                                                    goodsReceive=F(
                                                                                        'orderdetail__goodsReceive'),
                                                                                    goodsIssue=F(
                                                                                        'orderdetail__goodsIssue'),
                                                                                    uOm=F(
                                                                                        'orderdetail__uOm__quantityTypeCode'))
            else:
                detailList = OrderPlacementfromCustomer.objects.values('orderDate', 'ordNumber', 'connectedStatus',
                                                                       'customerId', 'expectedDate', 'expectedTime',
                                                                       'customer_address_Line1',
                                                                       'customer_address_Line2',
                                                                       'customer_unit1',
                                                                       'customer_unit2',
                                                                       'customer_postalCode',
                                                                       'customer_country__countryName',
                                                                       'customer_state__stateName',
                                                                       'customerId__cusCompanyName').annotate(
                    customerIdCount=Count('customerId'), orderDateCount=Count('orderDate')).order_by('expectedDate')
        if detailList:
            item['totalItem'] = list(detailList)
            totalItems.append(item)
            return JsonResponse(
                {'status': 'success', 'totalItems': totalItems})
        else:
            return JsonResponse(
                {'status': 'error', 'error_msg': 'No orders found'})
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


@csrf_exempt
def viewOrderDetails(request):
    if request.method == "POST" and ('user' in request.session or 'subUser' in request.session):
        item = {}
        totalItems = []
        if 'subUser' in request.session:
            currentUser = utility.getObjectFromSession(request, 'subUser')
            subUserProfile = constants.Yes
            company = utility.getCompanyBySchemaName(connection.schema_name)
            urls = utility.checkRequesURLisPresentForSubUser(currentUser.pk, request.path)
            loginUser = utility.getObjectFromSession(request, 'subUser')
            company = utility.getCompanyBySchemaName(connection.schema_name)
            subusr = Subuser.objects.get(userName=loginUser.userName)
            subSites = SubuserSiteAssign.objects.filter(subuserSiteAssignSubUser=subusr).values(
                'subuserSiteAssignSites__siteAddress')
            if request.body:
                a = request.body.decode('utf-8')
                # would take a file-like object, read the data from that object, and use that string to create an object
                body = json.loads(a)
                if 'ordNumber' in body:
                    ordNumber = body['ordNumber']
                    detailList = OrderPlacementtoSupplier.objects.filter(ordNumber=ordNumber,
                                                                         status=constants.Active).values('goodsIssue',
                                                                                                         'ordNumber',
                                                                                                         'productId__itemCode',
                                                                                                         'productId__itemName',
                                                                                                         'productId__itemCategory',
                                                                                                         'quantity',
                                                                                                         'price',
                                                                                                         'connectedStatus',
                                                                                                         'goodsReceive',
                                                                                                         'actualQuantity',
                                                                                                         'ordstatus',
                                                                                                         'comment',
                                                                                                         priceUnit__type=F(
                                                                                                             'priceUnit__currencyTypeCode'),
                                                                                                         uOm__type=F(
                                                                                                             'uOm__quantityTypeCode'),
                                                                                                         productId__relId__trdersId__companyName=F(
                                                                                                             'productId__supplierId__supCompanyName'),
                                                                                                         supplierId=F(
                                                                                                             'productId__supplierId'))
            else:
                detailList = OrderPlacementtoSupplier.objects.filter(ordToSupId__in=subSites).values('orderDate', 'ordNumber', 'connectedStatus',
                                                                     'shopCartId__expectedDate',
                                                                     'productId__supplierId__supCompanyName',
                                                                     'shopCartId__expectedTime',
                                                                     ).annotate(
                    customerIdCount=Count('ordNumber'), orderDateCount=Count('orderDate')).order_by(
                    'shopCartId__expectedDate')
        if 'user' in request.session:
            currentUser = utility.getObjectFromSession(request, 'user')
            subUserProfile = constants.No
            company = currentUser.userCompanyId
            urls = utility.checkRequesURLisPresentForCompany(company, request.path)
            # get the user from session using email
            if request.body:
                a = request.body.decode('utf-8')
                # would take a file-like object, read the data from that object, and use that string to create an object
                body = json.loads(a)
                if 'ordNumber' in body:
                    ordNumber = body['ordNumber']
                    detailList = OrderPlacementtoSupplier.objects.filter(ordNumber=ordNumber,
                                                                         status=constants.Active).values('goodsIssue',
                        'ordNumber', 'productId__itemCode', 'productId__itemName', 'productId__itemCategory', 'quantity',
                        'price','connectedStatus','goodsReceive','actualQuantity',
                        'ordstatus', 'comment', priceUnit__type=F(
                            'priceUnit__currencyTypeCode'), uOm__type=F('uOm__quantityTypeCode'),
                        productId__relId__trdersId__companyName=F('productId__supplierId__supCompanyName'),supplierId=F('productId__supplierId'))
            else:
                detailList = OrderPlacementtoSupplier.objects.values('orderDate','ordNumber','connectedStatus',
                                                                      'shopCartId__expectedDate',
                                                                     'productId__supplierId__supCompanyName',
                                                                     'shopCartId__expectedTime',
                                                                     ).annotate(
                    customerIdCount=Count('ordNumber'), orderDateCount=Count('orderDate')).order_by('shopCartId__expectedDate')
        if detailList:
            item['totalItem'] = list(detailList)
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
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
        body = json.loads(a)
        ordNumber = body['ordNumber']
        customerId = body['customerId']
        itemCode = body['itemCode']
        customer = utilitySD.getCustomerById(customerId)
        ordNumSup = OrderDetails.objects.get(ordNumber__ordNumber=ordNumber,itemCode=itemCode,ordNumber__customerId=customer)
        OrderPlacementtoSupplierUpdate(ordNumSup, body)
        if customer.relationshipStatus:
            currentSchema = connection.schema_name
            userCustomerSchema = utility.getCompanyByCompanyCode(customer.cusCompanyCode).schemaName
            connection.set_schema(schema_name=userCustomerSchema)
            ordNumCus = OrderPlacementtoSupplier.objects.get(ordNumber=ordNumber,productId__itemCode=itemCode)
            OrderPlacementtoSupplierUpdate(ordNumCus, body)
            connection.set_schema(schema_name=currentSchema)
        return JsonResponse({'status': 'success', 'success_msg': 'Order Updated Successfully'})
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
        a = request.body.decode('utf-8')
        # would take a file-like object, read the data from that object, and use that string to create an object
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
    # user not in the session it will redirect to login page
    return JsonResponse(
        {'status': 'error', 'error_msg': 'sessionexpired',
         'redirect_url': settings.HTTP + request.get_host() + '/login'})


