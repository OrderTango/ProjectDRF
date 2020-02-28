from django.urls import path 
from django.conf.urls import url, include 

from .api import UserView 


urlpatterns = [
    path('accounts/', UserView.as_view({'get': 'list'}), name='accounts'),
    path('accounts/<int:pk>', UserView.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='account-detail'),
]