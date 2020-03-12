from django.urls import path,re_path

from . import views

urlpatterns=[
    path('orderPlacement', views.orderPlacement),
    path('slaDetails', views.slaDetails),
    path('reviewOrderCheckSla', views.reviewOrderCheckSla),
    path('getOrderPOdetail', views.getOrderPOdetail),
    path('OrderDuplicating', views.OrderDuplicating),
    path('addNewPlaceOrder', views.addNewPlaceOrder),
    path('cancelOrDeletePlacedOrder', views.cancelOrDeletePlacedOrder),
    path('fetchDataByOrderNumber', views.fetchDataByOrderNumber),
    ]