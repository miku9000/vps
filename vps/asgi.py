import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vps.settings')

# THIS is required before any model/import usage
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

import virtualmachine.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        virtualmachine.routing.websocket_urlpatterns
    ),
})