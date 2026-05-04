from django.urls import re_path
from vps.consumers import SSHConsumer

websocket_urlpatterns = [
    re_path(r"ws/ssh/(?P<vmid>\d+)/$", SSHConsumer.as_asgi())
]