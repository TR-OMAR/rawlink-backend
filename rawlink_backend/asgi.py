import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from api.middleware import JwtAuthMiddleware
import api.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rawlink_backend.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddleware(
        URLRouter(
            api.routing.websocket_urlpatterns
        )
    ),
})