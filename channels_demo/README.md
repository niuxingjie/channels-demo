##  执行命令

- 有关channel的调试
```sh
python manage.py runserver 0.0.0.0:8000

打开两个页面

http://127.0.0.1:8000/chat/room/cartoon/

http://127.0.0.1:8000/chat/room/cartoon/

F12 中可以看到http和ws类型的请求

从shell中拷贝出channel_name

python manage.py shell
>>> from asgiref.sync import async_to_sync
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> async_to_sync(channel_layer.send)("specific.c22c08f4d2fe42edae8fda967b9b39e7!8f1ff3d05e6547329917142e1b0e0ed0", {
>>>     "type": "chat.message", 
>>>     "message": "Hello there!",
>>> })
```

- 部署尝试
```sh
cd channels_demo

pip install --no-deps -r requirements.txt

python manage.py migrate

gunicorn channels_demo.asgi:application --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

- 用户
```text
超级管理员
username:admin
password:admin

普通用户：
user001
user001
```

- 群发消息测试
```text
第一步：登录
    url:http://127.0.0.1:8000/api/token/
    method:post
    body：
    {
        "username": "admin",
        "password": "admin"
    }
    request：
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY2MzMxMTY1MCwiaWF0IjoxNjYzMjI1MjUwLCJqdGkiOiIzY2IxZjQ0YThiMDE0MDNjYTZkMGU3Mjg2OWYwODQ1MiIsInVzZXJfaWQiOjF9.h26pH0ThiOTetKYg9-iNq3sIcs4MJ_ctpv4XB_F0Tr4",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjYzMjI1NTUwLCJpYXQiOjE2NjMyMjUyNTAsImp0aSI6IjM1NGEzYTQ4ODg3NDQ5NGU4MmVhMzA1NDU3YzFiM2EwIiwidXNlcl9pZCI6MX0.0buRKRsjSb8osLE9hT1klpO3McWGMXFjOaXN9WX4mvs"
    }


第二步：配置用户token
    将上面拿到的access的token替换到message.html文件里
    访问http://127.0.0.1:8000/chat/messsage_client/页面
    shell里可以看到登录用户信息的日志


第三步：python manage.py shell 里群发消息
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("all_user_ws_client", {
        "type": "notify.message", 
        "message": "Hello there!",
    })

```



### 请求与推送实现方案分析：

- 请求与推送实现方案分析
```text
用于处理用户消息及公告消息：
    - 请求：
        - 列表页
            - 过滤条件
            - 分页
        - 详情页
    - 推送：
        - 新增消息后，主动推送给用户

方案1：
    - 请求：完全可以仍使用http请求。
    - 推送：
        - 单个用户（代表组织）建立一个唯一个group组，用于服务器主动向用户推送消息。
        - 此推送，可以根据推送类型，处理不同的推送（消息推送，新品上架）
        - 推送，只是告诉客户端，某类型数据有更新，请重新发送http请求最新数据
        - 前端只需给每个用户建立一个websocket链接，等待推送即可。
    - 消息通知系统是可以使用的。

方案2：
    - 请求，推送：全部通过wedsocket实现。
```

- django channels 实现推送群发与单发的点：
```text
前提知识：每个websocket connection 对应着一个channel_name

群发：就定义一个group_name(如：all_user_ws_client) 将所有激活的channel_name放进去，然后对group_name进行消息发送

单发：给每个用户定义一个group_name(如：{user_id}_group) 将请求登录人相同的channel_name放在一起，，然后对group_name进行消息发送

```

## Django Channels 学习记录

[官方文档](https://channels.readthedocs.io/en/stable/)



### step 2：文档

1. Introduction
```
- 同步异步代码混合使用
- 继承django现有认证、session引擎
- 基于asgi协议


- 可以很方便的集成channels到现有的项目，而无需大量修改

- channels和asgi将处理请求的组件分为两部分：scope和event
    - 对于http请求来说scope：就相当于request，一个请求的信息
    - 对于websocket来说scope：就代表了一个socket整个生命周期的信息
        - 这个scope的生命周期中包含诸多个事件event（一条消息？）

- Consumer
    - 对比django中的view，对应处理的是某个scope的所有event
    - 由于scope包含了多个event，因此这个scope的开启、保持链接（持续交互）、关闭，可以加入更多的逻辑。
        - 放心使用django orm：channels会自动使用多线程处理io阻塞的同步代码如：django orm

- channel可以处理多协议：
    - http
    - websocket
    - telegram

- 跨进程通信（channel）
    - channel layer
```


2. Consumers消费者 （socket处理器）

- Consumers基本结构
```
- 两种consumer基类：
    - channels.consumer.AsyncConsumer  异步的ayncio实现
    - channels.consumer.SyncConsumer  线程池实现
- 注意：
    - 如果使用了django orm会阻塞整个server，所以需要使用SyncConsumer。
    - 如果你需要AsyncConsumer中使用django orm，可以使用database_sync_to_async装饰器。
- consumers的关闭：
    - 必须通过 raise channels.exceptions.StopConsumer关闭。Consumer基类已经封装了此操作。
- Channel Layers：
    - consumers中可以处理进程间通信的Channel Layers
```


- Scope 视界（一批次的请求，一次聊天的多次发送与接收）
```
self.scope


scope["path"], the path on the request. (HTTP and WebSocket)
scope["headers"], raw name/value header pairs from the request (HTTP and WebSocket)
scope["method"], the method name used for the request. (HTTP)


中间件通常会往scope中添加解析到的有用参数：
Authentication 会增加 scope["user"]
URLRouter will put captured groups from the URL into scope["url_route"].

```

- Generic Consumers 封装好了的通用consumer
```python
# channels.generic.websocket.WebsocketConsumer

from channels.generic.websocket import WebsocketConsumer

class MyConsumer(WebsocketConsumer):
    groups = ["broadcast"]

    def connect(self):
        # Called on connection.
        # To accept the connection call:  建立一个scope？
        self.accept()  
        # Or accept the connection and specify a chosen subprotocol.
        # A list of subprotocols specified by the connecting client
        # will be available in self.scope['subprotocols']
        self.accept("subprotocol")    限制接收什么协议类型的scope？
        # To reject the connection, call:
        self.close()  拒绝 or 关闭 一个scope？

    def receive(self, text_data=None, bytes_data=None):
        # Called with either text_data or bytes_data for each frame
        # You can call:
        self.send(text_data="Hello world!")   发送数据
        # Or, to send a binary frame:
        self.send(bytes_data="Hello world!")
        # Want to force-close the connection? Call:
        self.close()
        # Or add a custom WebSocket error code!
        self.close(code=4123)  关闭

    def disconnect(self, close_code):
        # Called when the socket closes 当一个socket关闭时，会调用此方法



# channels.generic.websocket.JsonWebsocketConsumer

发送和接收的数据是json格式的

```

3. Routing 路由： 并行请求是很常见的，分发socket链接

- 基本概念
```python
# 路由颗粒度：
    - 协议级别：ProtocolTypeRouter
    - scope级别： 没有
    - event级别： 没有
# 在scope的颗粒上分发，不能在event颗粒上分发

# 请配置root application及根路由

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from chat.consumers import AdminChatConsumer, PublicChatConsumer


application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("chat/admin/", AdminChatConsumer.as_asgi()),
                path("chat/", PublicChatConsumer.as_asgi()),
            ])
        )
    ),
})
```

- ProtocolTypeRouter    协议级别的路由分发
```python
application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("chat/admin/", AdminChatConsumer.as_asgi()),
                path("chat/", PublicChatConsumer.as_asgi()),
            ])
        )
    ),
})

```


- URLRouter             地址url级别的路由分发
```python
URLRouter([
    re_path(r"^longpoll/$", LongPollConsumer.as_asgi()),
    re_path(r"^notifications/(?P<stream>\w+)/$", LongPollConsumer.as_asgi()),
    re_path(r"", get_asgi_application()),
])


# consumers 中获取路径参数
stream = self.scope["url_route"]["kwargs"]["stream"]



一个url可以对应多个scope：
    - url可已进行任意组合
    - 一次链接对应应一个scope
```


- ChannelNameRouter     管道名级别的路由分发：啥作用？
```python
# ？？？？
# 
ChannelNameRouter({
    "thumbnails-generate": some_app,
    "thumbnails-delete": some_other_app,
})


```


4. Database Access 数据库访问

- 摘要
```
django orm访问数据库是同步的，会不会阻塞websocket asgi服务

SyncConsumer JsonWebsocketConsumer 中通过django orm访问数据库的异步实现已经经过处理了，无需担心

database_sync_to_async可以帮助你在AsyncWebsocketConsumer中处理django orm

```


5. Channel Layers 通道层？【重点】

- 概述
```text
- 跨进程（application实例）通信途径 The channel layer is for high-level application-to-application communication

- channels的可选组件 CHANNEL_LAYERS 不配置，即可
- 引擎：
    - redis
    - 内存
```

- 应该如何使用channels ?????
```text
- 同步调用self.send
    from asgiref.sync import async_to_sync
    async_to_sync(channel_layer.send)("channel_name", {...})


- 任何 SyncConsumer or AsyncConsumer 提供一个 self.channel_layer 和 self.channel_name：
    - 名字为self.channel_name的或者self.channel_name被加入其中的组下的

？？？？？
Any consumer based on Channels’ SyncConsumer or AsyncConsumer will automatically provide you a self.channel_layer and self.channel_name attribute, which contains a pointer to the channel layer instance and the channel name that will reach the consumer respectively.

Any message sent to that channel name - or to a group the channel name was added to - will be received by the consumer much like an event from its connected client, and dispatched to a named method on the consumer. The name of the method will be the type of the event with periods replaced by underscores - so, for example, an event coming in over the channel layer with a type of chat.join will be handled by the method chat_join.

```

- Single Channels 单通道
```text
Each application instance - so, for example, each long-running HTTP request or open WebSocket - results in a single Consumer instance, and if you have channel layers enabled, Consumers will generate a unique channel name for themselves, and start listening on it for events.

每个application实例（一个进程，或一个websocket scope?）每个长期运行的http请求或websocket结果集，都会被分配一个唯一的channel name(类似于给每个request一个uid？)


这意味着：可以通过其他consumer或着其他进程或者命令行，给指定的channel name发消息event。

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        # Make a database row with our channel name
        Clients.objects.create(channel_name=self.channel_name)  # 记录下channel_name，绑定channel_name与其他信息？

    def disconnect(self, close_code):
        # Note that in some rare cases (power loss, etc) disconnect may fail
        # to run; this naive example would leave zombie channel names around.
        Clients.objects.filter(channel_name=self.channel_name).delete()  # 根据channel_name查询出

    # 注意这里方法的命名方式 type_message 类型_消息 意味着：使用此方法处理消息类型为type的消息
    def chat_message(self, event):
        # Handles the "chat.message" event when it's sent to us.  
        self.send(text_data=event["text"])



from channels.layers import get_channel_layer

channel_layer = get_channel_layer()
await channel_layer.send("channel_name", {
    "type": "chat.message",  # 消息类型为chat，处理此类型消息的方法名为chat_message
    "text": "Hello there!",
})


调试方法：代码中打印出channel_name，然后python manage.py shell中向此channel_name发送笑死

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

async_to_sync(channel_layer.send)("specific.c22c08f4d2fe42edae8fda967b9b39e7!8f1ff3d05e6547329917142e1b0e0ed0", {
    "type": "chat.message", 
    "message": "Hello there!",
})


```

- Groups 内建的组系统管理channels
```text
- 允许你把channel_name加入和移除出可命名的组

- 提供过期处理未关闭的链接

# This example uses WebSocket consumer, which is synchronous, and so
# needs the async channel layer functions to be converted.
from asgiref.sync import async_to_sync

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        async_to_sync(self.channel_layer.group_add)("chat", self.channel_name)  将当前链接加入到chat组

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)("chat", self.channel_name)  将当前链接移出chat组

    def receive(self, text_data):
        async_to_sync(self.channel_layer.group_send)(   给chat组素有channel成员发送消息
            "chat",
            {
                "type": "chat.message",
                "text": text_data,
            },
        )

    def chat_message(self, event):
        self.send(text_data=event["text"])


还可以用从Consumer外部向group组发送消息
    from asgiref.sync import async_to_sync
    async_to_sync(channel_layer.group_send)("chat", {"type": "chat.force_disconnect"})

也就是：一个用户应该与唯一一个group绑定，此用户可以同时开启多个页面，每个页面一个channel_name。管理用户的消息，就通过group去管理。
```


6. sessions 状态保持？？？
```



```

7. Authentication

- 概述
```
Note that the AuthMiddleware will only work on protocols that provide HTTP headers in their scope - by default, this is HTTP and WebSocket.
- 认证中间件只支持那些在scope中提供了http headers的协议，比如：http,websocket

```

- Custom Authentication 自定义认证，就是往self.scope中添加user信息
```python
from channels.db import database_sync_to_async

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class QueryAuthMiddleware:
    """
    Custom middleware (insecure) that takes user IDs from the query string.
    """

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        # Look up user from query string (you should also do things like
        # checking if it is a valid user ID, or if scope["user"] is already
        # populated).
        scope['user'] = await get_user(int(scope["query_string"]))

        return await self.app(scope, receive, send)

```

- How to log a user in/out 内置的登录与登出
```


```


8. Security

-  cross-site request forgery (CSRF) 防护
```python
from channels.security.websocket import OriginValidator

application = ProtocolTypeRouter({

    "websocket": OriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                ...
            ])
        ),
        [".goodsite.com", "http://.goodsite.com:80", "http://other.site.com"],  # ['*'] 限制来源
    ),
})


application = ProtocolTypeRouter({

    "websocket": AllowedHostsOriginValidator(   # 限制源等同于django allowed_host
        AuthMiddlewareStack(
            URLRouter([
                ...
            ])
        ),
    ),
})
```


9. 测试



10. Worker and Background Tasks  把channel当作消息队列的broker来用做进程间通讯

- 向 写死的channel_name（类似pulsar topic）发送消息
```python
# Inside a consumer
self.channel_layer.send(
    "thumbnails-generate",
    {
        "type": "generate",
        "id": 123456789,
    },
)

```

- channel_name级别的路由
```python
application = ProtocolTypeRouter({
    ...
    "channel": ChannelNameRouter({
        "thumbnails-generate": consumers.GenerateConsumer.as_asgi(),   # 根据channel_name路由分发请求
        "thumbnails-delete": consumers.DeleteConsumer.as_asgi(),
    }),
})

```


11. 部署： gunicorn是否可以用？？？？
```
uvnicorn应该是可以使用的

```





### step 1：Tutorial

1. 示例
```
- [中文](https://www.jianshu.com/p/e4d1e5e3ad39)
- [英文](https://channels.readthedocs.io/en/stable/tutorial/part_1.html)
```


2. 步骤

- 创建django项目
- 添加app
- 测试
```
$ python3 manage.py shell
import channels.layers
channel_layer = channels.layers.get_channel_layer()
from asgiref.sync import async_to_sync
async_to_sync(channel_layer.send)('test_channel', {'type': 'hello'})
async_to_sync(channel_layer.receive)('test_channel')
{'type': 'hello'}
```


## wsgi 与 asgi 协议

- wsgi:
    - [WSGI到底是什么？](https://zhuanlan.zhihu.com/p/95942024)
    - 全称Python Web Server Gateway Interface
    - 本质：
        - WSGI是一套接口标准协议/规范；
        - 通信（作用）区间是Web服务器和Python Web应用程序之间；
        - 目的是制定标准，以保证不同Web服务器可以和不同的Python程序之间相互通信
    - 主要规定：
        - Web程序必须有一个可调用对象，且该可调用对象接收两个参数，返回一个可迭代对象：
            - environ：字典，包含请求的所有信息
            - start_response：在可调用对象中调用的函数，用来发起响应，参数包括状态码，headers等
        - 例子：
        ```python
        # wsgi协议实现
        def hello(environ, start_response):
            status = "200 OK"
            response_headers = [('Content-Type', 'text/html')]
            start_response(status, response_headers)
            path = environ['PATH_INFO'][1:] or 'hello'
            return [b'<h1> %s </h1>' % path.encode()]
        
        ```

- asgi:
    - 





## WebSocket 教程


1. webdocker协议

- [WebSocket 教程](https://www.ruanyifeng.com/blog/2017/05/websocket.html)

- [万字长文，一篇吃透WebSocket：概念、原理、易错常识](https://cloud.tencent.com/developer/article/1887095)



2. http协议

- 简单来说：
    - http就是tcp上的一次请求（数据储传输）的格式规范
    - 规定了：状态码、响应体、长短链接、GET、POST等方法


3. tcp 协议

- 简单来说：
    - tcp协议主要是socket的建立与销毁
    - ip:端口 为socket的唯一标识

- [TCP协议详解](https://zhuanlan.zhihu.com/p/64155705)




4. websocket报文分析
```text
请求建立一个websocket链接：请求Headers如下

GET ws://127.0.0.1:8000/ws/chat/cartoon/ HTTP/1.1
Host: 127.0.0.1:8000
Connection: Upgrade
Pragma: no-cache
Cache-Control: no-cache
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36
Upgrade: websocket
Origin: http://127.0.0.1:8000
Sec-WebSocket-Version: 13
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cookie: csrftoken=PwZcHPNREH1gw0ylxrx7ygSmogPXWKWbGZ4OpFZtuc70D06C1ljTyL8uRV3XfojE
Sec-WebSocket-Key: NYbZ2MksCIuiLsG5kDegqQ==
Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits


响应：响应Headers如下

HTTP/1.1 101 Switching Protocols
Server: Daphne
Upgrade: WebSocket
Connection: Upgrade
Sec-WebSocket-Accept: CaPg3SGHTnEZ0y4n7KzSrcEQ26I=

```








