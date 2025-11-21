from django.urls import re_path
from . import consumers # We will create this file next

websocket_urlpatterns = [
    # This regex matches a WebSocket URL for chat
    # We will use this URL in our frontend
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
]