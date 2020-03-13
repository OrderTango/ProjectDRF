import json

from operator import itemgetter

from django.db import connection

from rest_framework import status, viewsets, views 
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny 
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from .views import *
from .models import Thread, ThreadMessage, ThreadMember
from .serializers import ThreadSerializer, ThreadMessageSerializer, ThreadMemberSerializer

from OrderTangoApp.models import *

class ThreadView(viewsets.ViewSet):
    serializer_class = ThreadSerializer

    def list(self, request, *args, **kwargs):
        """
        Get all the chat rooms of the current user
        """
        # connection.schema_name = 'public'
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)
        print(connection.schema_name)

        queryset = Thread.objects.filter(is_archived=False)
        serializer = self.serializer_class(queryset, many=True)

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create chat room
        """
        
        queryset = Thread.objects.create()
        serializer = self.serializer_class(queryset)

        try:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except: 
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ThreadDetailView(views.APIView):
    serializer_class = ThreadSerializer

    def delete(self, request, *args, **kwargs):
        """ 
        Delete thread
        """
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)
        print(connection.schema_name)
        print(self.kwargs)

        thread = Thread.objects.get(id=kwargs['pk'])
        thread.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ThreadMessageView(viewsets.ViewSet):
    serializer_class = ThreadMessageSerializer


class ThreadMemberView(views.APIView):
    serializer_class = ThreadSerializer

    def delete(self, request, *args, **kwargs):
        """ 
        Delete thread
        """
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)
        print(connection.schema_name)
        print(self.kwargs)
        thread = Thread.objects.get(name=kwargs['thread'])
        
        user = SubUser.objects.get(userId=kwargs['pk'])
        member = ThreadMember.objects.get(thread=thread, member=user)
        member.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
                