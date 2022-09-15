from email import message
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer, JsonWebsocketConsumer
from channels.layers import get_channel_layer



MESSAGE_BROADCAST_GROUP_NAME = "all_user_ws_client"
MESSAGE_USER_GROUP_NAME_TEMPLATE = "{user_id}_ws_clients"  # 不能用冒号

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        print('-------connect--------')
        print(self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print('-------disconnect--------')
        print(self.channel_name)

    async def receive(self, text_data):
        print('-------reveive--------')
        print(self.channel_name)

        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type":"chat_message",
                "message": message
            }
        )
    async def chat_message(self, event):
        print('-------chat_message--------')
        print(self.channel_name)

        message = event['message']

        await self.send(text_data=json.dumps({
            "message": message
        }))


class MessageConsumer(JsonWebsocketConsumer):
    """
    用于消息接收页面建立websocket连接：
    """
    
    # 所有的ws client都加入一个组，用于平台消息推送（广播消息）
    # 只要是websocket链接会自动将self.channel_name加入此组(看源码：websocket_connect方法)，连接断开时，自动移除出组
    groups = [MESSAGE_BROADCAST_GROUP_NAME, ]

    def connect(self):
        print('-----connect-----')
        print(f"login_user:{self.scope['user']}")
        
        # 加入用户channel group
        login_user_group = MESSAGE_USER_GROUP_NAME_TEMPLATE.format(user_id=self.scope['user'].id)
        async_to_sync(self.channel_layer.group_add)(login_user_group, self.channel_name)
        return super().connect()
    
    def disconnect(self, code):
        # 连接断开时，移出组
        login_user_group = MESSAGE_USER_GROUP_NAME_TEMPLATE.format(user_id=self.scope['user'].id)
        async_to_sync(self.channel_layer.group_discard)(login_user_group, self.channel_name)
        return super().disconnect(code)

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        print('-----receive-----')
        print(f"login_user:{self.scope['user']}")
        return super().receive(text_data, bytes_data, **kwargs)

    def notify_message(self, event):
        """
        群发消息调试代码：（给all_user_ws_client下所有的channel_name发消息）

        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("all_user_ws_client", {
            "type": "notify.message",  # 特别注意这里要与当前方法名对应
            "message": "Hello there!",
        })
        """
        print('------notify_message------')
        print(f"login_user:{self.scope['user']}")
        message = event['message']

        self.send(text_data=json.dumps({
            "message": message
        }))


class NotifyService:

    @classmethod
    def broadcast(cls, message, channel_group_name=MESSAGE_BROADCAST_GROUP_NAME):
        """
        群发消息：
            - 公告:
        
        示例：
            from chat.consumers import NotifyService
            NotifyService.broadcast("Hello",channel_group_name="all_user_ws_client")
        """
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(channel_group_name, {
            "type": "notify.message", 
            "message": message,
        })

    @classmethod
    def dialogue(cls, user_list, message):
        """
        给用户单独发消息：
            - 指的是那些打开页面，建立了ws连接的用户
            - 那些没有打开页面的用户，数据库里自然也会有数据，当他打开页面时，获取的数据便是最新的
        方案2:
            - 此消息仅用于通知client后端的某类数据有更新，请重新发送请求获取相关类型数据的最新数据。

        示例：
            from chat.consumers import NotifyService
            from chat.models import Speaker
            speaker=Speaker.objects.get(username='admin')
            NotifyService.broadcast("Hello Everyone！",channel_group_name="all_user_ws_client")
            NotifyService.dialogue([speaker,],"hello buddy！")
        """
        channel_layer = get_channel_layer()
        for u in user_list:
            user_group_name = MESSAGE_USER_GROUP_NAME_TEMPLATE.format(user_id=u.id)
            print('----dialogue----')
            print(user_group_name)
            async_to_sync(channel_layer.group_send)(user_group_name, {
                "type": "notify.message", 
                "message": message,
            })


