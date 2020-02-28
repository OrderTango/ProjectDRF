import json

from operator import itemgetter

from rest_framework import status, viewsets, views 
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny 
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from .views import *
from .models import ChatRoom, ChatMessage
from .serializers import ChatRoomSerializer, ChatMessageSerializer

from OrderTangoApp.models import *


class ChatRoomView(viewsets.ViewSet):
    serializer_class = ChatRoomSerializer

    def list(self, request, *args, **kwargs):
        """
        Get all the chat rooms of the current user
        """
        user = User.objects.get(userId=getUser(request))
        queryset = ChatRoom.objects.filter(creator=user)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create chat room
        """
        user = User.objects.get(userId=getUser(request))
        queryset = ChatRoom.objects.create(creator=user, room_name=self.request.data['room_name'])

        serializer = self.serializer_class(queryset)

        try:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except: 
            return Response(status=status.HTTP_400_BAD_REQUEST)

# class ChatRoomView(views.APIView):
#     serializer_class = ChatRoomSerializer

#     def get(self, request, *args, **kwargs):
#         """
#         Get all the chat rooms of the current user
#         """
#         import pdb; pdb.set_trace()
#         user = User.objects.get(userId=getUser(request))
#         print('User', user)
#         queryset = ChatRoom.objects.filter(creator=user)
#         serializer = self.serializer_class(queryset, many=True)
#         return Response(serializer.data)

#     def post(self, request, *args, **kwargs):
#         """
#         Create chat room
#         """
#         user = User.objects.get(userId=getUser(request))
#         queryset = ChatRoom.objects.create(creator=user, room_name=self.request.data['room_name'])

#         serializer = self.serializer_class(queryset)

#         try:
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         except: 
#             return Response(status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, *args, **kwargs):
#         """
#         Delete chat room
#         """
#         user = User.objects.get(userId=getUser(request))
#         chat_room = ChatRoom.objects.get(creator=user, room_name=self.request.data['room_name'])
#         chat_room.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


        # serializer = self.serializer_class(data=self.request.data)

        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(status=status.HTTP_400_BAD_REQUEST)


class ChatMessageView(views.APIView):
    serializer_class = ChatMessageSerializer

    def get(self, request, *args, **kwargs):
        """
        Get all the messages of the current user and chat room
        """
        user = User.objects.get(userId=getUser(request))
        room_name = ChatRoom.objects.get(room_name=self.kwargs['room_name'])

        queryset = ChatMessage.objects.filter(author=user, room_name=room_name)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Create chat messages
        """
        user = User.objects.get(userId=getUser(request))
        room_name = ChatRoom.objects.get(room_name=self.kwargs['room_name'])
        queryset = ChatMessage.objects.create(author=user, room_name=room_name, content=self.request.data['content'])
        serializer = self.serializer_class(queryset)

        try: 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except: 
            return Response(status=status.HTTP_400_BAD_REQUEST)

    

                