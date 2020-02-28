from django.urls import path 
from django.conf.urls import url, include

from .api import ChatRoomView, ChatMessageView 


# urlpatterns = [
#     path('chat/', ChatRoomView.as_view()),
#     path('chat/<str:room_name>/', ChatMessageView.as_view())
# ]

urlpatterns = [
    path('chat/', ChatRoomView.as_view({'get': 'list', 'post': 'create'}), name='chat'),
    path('chat/<str:room_name>/', ChatMessageView.as_view())
]