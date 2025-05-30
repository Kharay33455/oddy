from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/cashien/(?P<room_name>\w+)/$", consumers.CashienChatConsumer.as_asgi()),
]