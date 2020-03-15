from django.db import connection

from rest_framework import status, viewsets, views 
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny 

from OrderTangoApp.models import User, Company, Schema 
from OrderTangoSubDomainApp.models import Subuser
from chat.views import *

from .serializers import UserSerializer, CompanySerializer, SubUserSerializer


class CompanyView(viewsets.ViewSet):
    serializer_class = CompanySerializer 

    def retrieve(self, request, *args, **kwargs):
        """
        Get Company details
        """
        current_schema = connection.schema_name 
        connection.set_schema(schema_name=current_schema)
        
        company_schema = Schema.objects.get(schema_name=current_schema).schemaCompanyName
        company = Company.objects.get(companyName=company_schema)
        serializer = self.serializer_class(company)
        return Response(serializer.data)

class UserListView(viewsets.ViewSet):
    serializer_class = UserSerializer 

    def list(self, request, *args, **kwargs):
        """ 
        List all the Users
        """
        current_schema = connection.schema_name 
        connection.set_schema(schema_name=current_schema)

        company_schema = Schema.objects.get(schema_name=current_schema).schemaCompanyName
        company = Company.objects.get(companyName=company_schema)
        users = User.objects.filter(userCompanyId=company) 
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data)

class UserView(viewsets.ViewSet):
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Get user details
        """
        
        user = User.objects.get(userId=getUser(request))
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete user
        """
        # user_id = self.kwargs['pk']
        user = User.objects.get(userId=getUser(request))
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SubUserListView(viewsets.ViewSet):
    serializer_class = SubUserSerializer

    def list(self, request, *args, **kwargs):
        """
        List all the Sub users
        """
        sub_users = Subuser.objects.all() 
        serializer = self.serializer_class(sub_users, many=True)
        return Response(serializer.data)


class SubUserView(viewsets.ViewSet):
    serializer_class = SubUserSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Get sub user details 
        """
        sub_user = Subuser.objects.get(subUserId=getUser(request))
        serializer = self.serializer_class(sub_user)
        return Response(serializer.data)
