from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_code>[A-Z0-9]{6,8})/$', consumers.ChatConsumer.as_asgi()),
]
