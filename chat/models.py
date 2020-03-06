from django.db import models
from django.db.models.signals import pre_save

from tenant_schemas.models import TenantMixin
from OrderTangoApp.models import User 


class Thread(models.Model):
    name = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)


class ThreadMessage(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField() 
    date_created = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    def limit_10_messages():
        return ThreadMessage.objects.order_by('date_created').all()


class ThreadMember(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

