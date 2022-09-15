from dataclasses import field
from django.shortcuts import render


from rest_framework import serializers

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView

from rest_framework_simplejwt.authentication import JWTAuthentication


from .models import Message


def index(request):
    return render(request, 'chat/index.html')


def room(request, room_name):
    return render(request, 'chat/room.html', {
        "room_name": room_name
    })


def message_test_page(request):
    return render(request, 'chat/message.html')


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            "id", "title", "content"
        )


class MessageListView(ListAPIView):
    """
    消息列表
    """
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

    def get_queryset(self):
        user = self.request.user
        print(user)
        return Message.objects.filter(receiver=user)
    

class MessageRetrieveView(RetrieveAPIView):
    """
    消息详情
    """
    pass
