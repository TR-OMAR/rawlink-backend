import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rawlink_backend.settings')

# 1. Initialize Django ASGI application FIRST
# This step ensures django.setup() is called and apps are loaded.
django_asgi_app = get_asgi_application()

# 2. Now it is safe to import middleware/routing that relies on models
from channels.routing import ProtocolTypeRouter, URLRouter
from api.middleware import JwtAuthMiddleware
from api import routing  # Assuming you have a routing.py

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddleware(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})