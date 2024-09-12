from django.urls import re_path, path

from . import consumer

websocket_urlpatterns = [
  re_path(r'ws/broadcast/$', consumer.BroadCastConsumer.as_asgi()),
]