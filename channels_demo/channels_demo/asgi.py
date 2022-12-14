"""
ASGI config for channels_demo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter

from chat import routing
from chat import middleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'channels_demo.settings')
django_asgi_application = get_asgi_application()


# 协议级别的路由分发
application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'http':django_asgi_application,  # http协议使用django asgi处理

    'websocket': middleware.CustomAuthMiddleware(  # websocket协议使用channels asgi处理
        URLRouter(
            routing.websocket_urlpatterns
        )
    )
})
