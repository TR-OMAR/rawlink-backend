import os
from django.core.asgi import get_asgi_application

# Set the default Django settings module for the ASGI application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rawlink_backend.settings')

# Initialize Django ASGI application first
django_asgi_app = get_asgi_application()

# Import Channels routing and custom middleware after Django setup
from channels.routing import ProtocolTypeRouter, URLRouter
from api.middleware import JwtAuthMiddleware
from api import routing  # Contains WebSocket URL patterns

# Define the ASGI application with HTTP and WebSocket support
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Handles traditional HTTP requests
    "websocket": JwtAuthMiddleware(
        URLRouter(
            routing.websocket_urlpatterns  # Routes WebSocket connections
        )
    ),
})
