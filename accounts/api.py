from rest_framework import status, viewsets, views 
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny 

from OrderTangoApp.models import User 
from chat.views import *

from .serializers import UserSerializer


class UserView(viewsets.ViewSet):
    serializer_class = UserSerializer 

    def list(self, request, *args, **kwargs):
        """ 
        List all the Users
        """
        user = User.objects.all() 
        serializer = self.serializer_class(user, many=True)
        return Response(serializer.data)

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
