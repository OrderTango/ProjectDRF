from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('userId', 'userCompanyId', 'firstName', 'lastName', 'countryCode', 'contactNo', 'email', 'password', 'otp', 'sec_question', 'sec_answer', 'token', 'profilepic', 'lastLogin', 'activityLog', 'status', 'createdDateTime', 'updatedDateTime')
