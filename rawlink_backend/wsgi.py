"""
WSGI config for rawlink_backend project.

This file exposes the WSGI callable as a module-level variable named `application`.
It is used by WSGI servers to serve the application.

For more info: https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the default settings module for Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rawlink_backend.settings')

# Create WSGI application for use by WSGI servers
application = get_wsgi_application()
