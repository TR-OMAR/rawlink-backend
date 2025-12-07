"""
Django settings for rawlink_backend project.

"""
import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
from datetime import timedelta

# -----------------------------------------------------------
# Base Directory
# -----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------
# Load Environment Variables
# -----------------------------------------------------------
load_dotenv(BASE_DIR / '.env')  # Load variables from .env file

# -----------------------------------------------------------
# Security Settings
# -----------------------------------------------------------
# Secret key for Django; use environment variable in production
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key')

# Debug mode: only enable for local development
DEBUG = os.environ.get('DEBUG') == 'True' or ('RENDER' not in os.environ)

# Allowed hosts for incoming requests
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Ensure proper handling of HTTPS behind proxies (e.g., Render)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# -----------------------------------------------------------
# Installed Apps
# -----------------------------------------------------------
INSTALLED_APPS = [
    # Channels / ASGI support
    'daphne',
    'channels',

    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Cloudinary for media storage
    'cloudinary_storage',
    'cloudinary',

    # Local app
    'api.apps.ApiConfig',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'djoser',
    'corsheaders',
]

# -----------------------------------------------------------
# Middleware
# -----------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files efficiently
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -----------------------------------------------------------
# URL / WSGI / ASGI Configuration
# -----------------------------------------------------------
ROOT_URLCONF = 'rawlink_backend.urls'
WSGI_APPLICATION = 'rawlink_backend.wsgi.application'
ASGI_APPLICATION = 'rawlink_backend.asgi.application'

# -----------------------------------------------------------
# Templates
# -----------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# -----------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------
DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
}

# -----------------------------------------------------------
# Password Validation
# -----------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------------------
# Internationalization
# -----------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------
# Static & Media Files
# -----------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_build' / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Used Whitenoise for production static file handling
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# -----------------------------------------------------------
# Default primary key field type
# -----------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -----------------------------------------------------------
# Custom User Model
# -----------------------------------------------------------
AUTH_USER_MODEL = 'api.User'

# -----------------------------------------------------------
# CORS and CSRF
# -----------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://rawlink-frontend-one.vercel.app",
    'https://rawlink-api.onrender.com',
]

CSRF_TRUSTED_ORIGINS = [
    "https://rawlink-frontend-one.vercel.app",
]

# -----------------------------------------------------------
# Django REST Framework Settings
# -----------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# -----------------------------------------------------------
# JWT Settings (Simple JWT)
# -----------------------------------------------------------
SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# -----------------------------------------------------------
# Djoser Settings
# -----------------------------------------------------------
DJOSER = {
    'SERIALIZERS': {
        'user_create': 'api.serializers.UserCreateSerializer',
        'user': 'api.serializers.UserSerializer',
    },
}

# -----------------------------------------------------------
# Channels / WebSocket Layer
# -----------------------------------------------------------
if 'REDIS_URL' in os.environ:
    # Production: Redis-backed channel layer
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.environ.get('REDIS_URL')],
            },
        },
    }
else:
    # Development: In-memory channel layer
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

# -----------------------------------------------------------
# Cloudinary Media Storage
# -----------------------------------------------------------
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'do8p3on1d',        # cloud name
    'API_KEY': '192858953275565',     # API key
    'API_SECRET': 'ihx-u-IXkroZ0CdOxe9EV9ACA_o',  # API secret
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
