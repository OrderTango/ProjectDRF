import json

from operator import itemgetter

from django.shortcuts import render
from rest_framework_jwt.settings import api_settings

from OrderTango.settings import *
from OrderTangoApp.models import *


def getUser(request):
    if 'user' in request.session:
        string_user = request.session['user']
        obj_user = json.loads(string_user)
        session_user = list(map(itemgetter('pk'), obj_user))
        return session_user[0]
    elif 'subUser' in request.session:
        string_user = request.session['subUser']
        obj_user = json.loads(string_user)
        session_user = list(map(itemgetter('pk'), obj_user))
        return session_user[0]

def getToken(user):
    user = User.objects.get(userId=user)
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER 
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER 
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return token
