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
        # user = User.objects.get(userId=getUser(request))
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

    # def retrieve(self)

    # def update()



class ThreadMessageView(viewsets.ViewSet):
    serializer_class = ThreadMessageSerializer

    # def list(self, request, *args, **kwargs):
    #     """
    #     Get thread message
    #     """
    #     connection.schema_name = 'public'
    #     currentSchema = connection.schema_name 
    #     connection.set_schema(schema_name=currentSchema)

    #     user = User.objects.get(userId=getUser(request))
    #     thread = Thread.objects.get(id=self.kwargs['id'])
    #     queryset = ThreadMessage.objects.filter(sender=user, thread=thread)
    #     serializer = self.serializer_class(queryset, many=True)

    #     connection.schema_name = 'public'
    #     currentSchema = connection.schema_name 
    #     connection.set_schema(schema_name=currentSchema)

    #     return Response(serializer.data)

    # def create(self, request, *args, **kwargs):
    #     """
    #     Create message
    #     """
    #     user = User.objects.get(userId=getUser(request))
    #     thread = Thread.objects.get(thread=self.kwargs['id'])
    #     queryset = ThreadMessage.objects.create(sender=user, thread=thread, message=self.request.data['message'])
    #     serializer = self.serializer_class(queryset)

    #     try: 
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     except: 
    #         return Response(status=status.HTTP_400_BAD_REQUEST)

    # def retrieve(self, request, *args, **kwargs):
    #     """
    #     Retrieve message
    #     """
    #     user = User.objects.get(userId=getUser(request))
    #     thread = Thread.objects.get(id=self.kwargs['id'])
    #     thread_message = ThreadMessage.objects.get(id=self.kwargs['id'])
    #     queryset = ThreadMessage.objects.filter(id=thread_message, sender=user, thread=thread)
    #     serializer = self.serializer_class(queryset)
    #     return Response(serializer.data)

    # def update()

    # def delete


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
        user = User.objects.get(userId=kwargs['pk'])
        member = ThreadMember.objects.get(thread=thread, member=user)
        member.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
                