from django.conf.urls import url
from django.contrib import admin
from django.urls import path


from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('room/<str:room_name>/', views.room, name='room'),
    
    # 用来调试消息推送的客户端
    path('messsage_client/', views.message_test_page, name='message_test_page'),

    path('messages/', views.MessageListView.as_view(), name='messages'),
]



