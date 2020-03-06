from rest_framework import serializers 

from .views import *
from .models import Thread, ThreadMessage, ThreadMember

from OrderTangoApp.models import User 


class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = '__all__'


class ThreadMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadMessage 
        fields = '__all__'


class ThreadMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadMember
        fields = '__all__'
