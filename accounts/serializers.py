from rest_framework import serializers 
from OrderTangoApp.models import User, Company
from OrderTangoSubDomainApp.models import Subuser


class CompanySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Company 
        fields = '__all__'
        

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = '__all__'

class SubUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subuser
        fields = '__all__'