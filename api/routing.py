from django.urls import re_path
from . import consumers


# WebSocket routes used by Django Channels.
# Each path connects a client to the corresponding consumer.
websocket_urlpatterns = [
    re_path(r"ws/chat/$", consumers.ChatConsumer.as_asgi()),
]
