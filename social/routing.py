from django.urls import re_path
from social import consumers


websocket_urlpatterns = [
    re_path(r"wss/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"wss/group/$", consumers.GroupChatConsumer.as_asgi()),
]
