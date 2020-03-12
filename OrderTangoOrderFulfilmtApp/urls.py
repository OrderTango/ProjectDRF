from django.urls import path,re_path

from . import views

urlpatterns=[
    path('viewOrderDetails', views.viewOrderDetails),
    path('orderFulfillmentSupplier', views.orderFulfillmentSupplier, name='orderFulfillmentSupplier'),
    path('orderFulfillmentCustomer', views.orderFulfillmentCustomer, name='orderFulfillmentCustomer'),
    path('viewPlacedOrderDetails',views.viewPlacedOrderDetails,name='viewPlacedOrderDetails'),
    ]