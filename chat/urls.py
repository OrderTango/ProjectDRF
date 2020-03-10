from django.urls import path 
from django.conf.urls import url, include

from .api import ThreadView, ThreadDetailView,ThreadMemberView


# urlpatterns = [
#     path('chat/', ChatRoomView.as_view()),
#     path('chat/<str:room_name>/', ChatMessageView.as_view())
# ]

urlpatterns = [
    path('api/thread/', ThreadView.as_view({'get': 'list', 'post': 'create'}), name='api-thread'),
    path('api/thread/<int:pk>/', ThreadDetailView.as_view(), name='api-thread-detail'),
    path('api/<str:thread>/<int:pk>/members/', ThreadMemberView.as_view(), name='api-thread-members'),
    # path('api/thread/<int:pk>/messages/', ThreadMessageView.as_view({'get': 'list', 'post': 'create'}), name='api-thread-message'),
    # path('api/thread/<int:pk>/messages/<int:pk>/', ThreadMessageView.as_view({'get': 'retrieve'}), name='api-thread-message-detail'),
]