from django.db import models
from tenant_schemas.models import TenantMixin
from OrderTangoApp.models import User 


class ChatRoom(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=500, unique=True)
    date_created = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.room_name 


class ChatMessage(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    room_name = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    content = models.TextField() 
    date_created = models.DateTimeField(auto_now_add=True)

    def limit_10_messages(self):
        return ChatMessage.objects.order_by(-date_created).all()[:10]
