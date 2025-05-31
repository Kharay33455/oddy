from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/cashien/(?P<room_name>\w+)/$", consumers.CashienChatConsumer.as_asgi()),
    re_path(r"ws/cashien/dispute/(?P<room_name>\w+)/$", consumers.CashienDisputeConsumer.as_asgi()),
]