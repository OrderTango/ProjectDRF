from rest_framework import status, viewsets, views 
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny 

from OrderTangoApp.models import User, Company 
from chat.views import *

from .serializers import UserSerializer, CompanySerializer


class CompanyView(viewsets.ViewSet):
    serializer_class = CompanySerializer 

    def retrieve(self, request, *args, **kwargs):
        """
        Get Company details
        """
        print(kwargs)
        company = Company.objects.get(companyId=kwargs['pk'])
        serializer = self.serializer_class(company)
        return Response(serializer.data)

class UserListView(viewsets.ViewSet):
    serializer_class = UserSerializer 

    def list(self, request, *args, **kwargs):
        """ 
        List all the Users
        """
        user = User.objects.get(userId=getUser(request))
        company = Company.objects.get(companyId=user.userCompanyId)
        users = User.objects.filter(userCompanyId=company) 
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data)

class UserView(viewsets.ViewSet):
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Get a specific user
        """
        user = User.objects.get(userId=getUser(request))
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a specific user
        """
        # user_id = self.kwargs['pk']
        user = User.objects.get(userId=getUser(request))
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
