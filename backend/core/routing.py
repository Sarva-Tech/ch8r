from django.urls import re_path
from core.consumers import LiveUpdatesConsumer

print("Live updates URL patterns loaded")

websocket_urlpatterns = [
    re_path(r'ws/updates/(?P<client_id>[\w\-]+)/$', LiveUpdatesConsumer.as_asgi()),
]
