from django.urls import path 
from django.conf.urls import url, include 

from .api import UserListView, UserView, CompanyView, SubUserListView, SubUserView 


urlpatterns = [
    path('api/accounts/', UserListView.as_view({'get': 'list'}), name='accounts'),
    path('api/user/account/', UserView.as_view({'get': 'retrieve'}), name='account-detail'),
    path('api/user/account/<int:pk>/', UserView.as_view({'delete': 'destroy'})),
    path('api/sub-accounts/', SubUserListView.as_view({'get': 'list'}), name='sub-accounts'),
    path('api/sub-user/account/', SubUserView.as_view({'get': 'retrieve'}), name='sub-account-detail'),
    path('api/org/', CompanyView.as_view({'get': 'retrieve'}), name='org-detail'),
]