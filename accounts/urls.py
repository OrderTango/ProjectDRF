from django.urls import path 
from django.conf.urls import url, include 

from .api import UserListView, UserView, CompanyView 


urlpatterns = [
    path('api/accounts/', UserListView.as_view({'get': 'list'}), name='accounts'),
    path('api/user/account/', UserView.as_view({'get': 'retrieve'}), name='account-detail'),
    path('api/user/account/<int:pk>/', UserView.as_view({'delete': 'destroy'})),
    path('api/org/<int:pk>/', CompanyView.as_view({'get': 'retrieve'}), name='org-detail'),
]