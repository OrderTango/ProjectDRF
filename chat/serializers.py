from rest_framework import serializers 

from .views import *
from .models import ChatRoom, ChatMessage 

from OrderTangoApp.models import User 


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = '__all__'

    # def create(self, request, validated_data):   
    #     user = User.objects.get(userId=getUser(self.request))
    #     room_name = self.validated_data['room_name']
    #     return ChatRoom.objects.create(creator=user, room_name=room_name)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage 
        fields = '__all__'