# chat/routing.py
from django.urls import path, re_path
from . import consumers

# url级别的路由分发
websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),

    path('ws/messages/', consumers.MessageConsumer.as_asgi()),
]
