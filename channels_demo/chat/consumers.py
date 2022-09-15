from email import message
import json

from channels.generic.websocket import AsyncWebsocketConsumer, JsonWebsocketConsumer


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
    用于处理用户消息及公告消息：
        - 请求：
            - 列表页
                - 过滤条件
                - 分页
            - 详情页
        - 推送：
            - 新增消息后，主动推送给用户

    方案1：(此处选择的方案)
        - 请求：完全可以仍使用http请求。
        - 推送：
            - 单个用户（代表组织）建立一个唯一个group组，用于服务器主动向用户推送消息。
            - 此推送，可以根据推送类型，处理不同的推送（消息推送，新品上架）
            - 推送，只是告诉客户端，某类型数据有更新，请重新发送http请求最新数据
        - 消息通知系统是可以使用的。

    方案2：
        - 请求，推送：全部通过wedsocket实现。
        - 更适合聊天室这种对“传输增量数据”要求较高的场景。
    """
    MESSAGE_GROUP_NAME_TEMPLATE = "{org_id}:{user_id}"
    
    # 所有的ws client都加入一个组，用于平台消息推送（广播消息）
    # 只要是websocket链接会自动将self.channel_name加入此组
    groups = ["all_user_ws_client"]

    def connect(self):
        print('-----connect-----')
        print(f"login_user:{self.scope['user']}")
        self.groups.append(self.channel_name)
        return super().connect()
    
    def disconnect(self, code):
        return super().disconnect(code)

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        return super().receive(text_data, bytes_data, **kwargs)

    def notify_message(self, event):
        """
        群发消息调试代码：（给all_user_ws_client下所有的channel_name发消息）

        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("all_user_ws_client", {
            "type": "notify.message", 
            "message": "Hello there!",
        })
        """
        message = event['message']

        self.send(text_data=json.dumps({
            "message": message
        }))



