
- 有关channel的调试
```sh
python manage.py runserver 0.0.0.0:8000

打开两个页面

http://127.0.0.1:8000/chat/cartoon/

http://127.0.0.1:8000/chat/cartoon/

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



