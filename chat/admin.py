from django.contrib import admin
from .models import ChatRoom, ChatMessage 


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'date_created')

@admin.register(ChatMessage)
class ChatMessageAmin(admin.ModelAdmin):
    list_display = ('room_name', 'content', 'date_created')
    lsit_filter = ('room_name', 'date_created')
