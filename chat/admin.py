from django.contrib import admin
from .models import Thread, ThreadMessage, ThreadMember


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_created', 'is_archived')

@admin.register(ThreadMessage)
class ThreadMessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'message', 'date_created', 'is_archived')
    list_filter = ('date_created', 'is_archived')

@admin.register(ThreadMember)
class ThreadMemberAdmin(admin.ModelAdmin):
    list_display = ('thread', 'member', 'date_added', 'is_active')
    list_filter = ('date_added', 'is_active')
