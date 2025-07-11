from django.urls import re_path

from core.consumers import ChatConsumer
print("WebSocket URL patterns loaded")

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chatroom_uuid>[a-f0-9\-]+)/$', ChatConsumer.as_asgi()),
]
