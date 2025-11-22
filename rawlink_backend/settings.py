"""
Django settings for rawlink_backend project.
Merged and cleaned version.
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
# Reads .env at project root (BASE_DIR / '.env')
load_dotenv(BASE_DIR / '.env')

# -----------------------------------------------------------
# Security
# -----------------------------------------------------------
# SECRET_KEY: prefer env var; fallback to a dev key (DO NOT use fallback in production)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key')

# DEBUG:
# - If DEBUG env var explicitly set to 'True' use it.
# - Otherwise, treat presence of RENDER env var as production (DEBUG=False).
DEBUG = os.environ.get('DEBUG') == 'True' or ('RENDER' not in os.environ)
# (If you want stricter behavior, change above to only rely on env var.)

# -----------------------------------------------------------
# Allowed Hosts
# -----------------------------------------------------------
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# 3. Handle SSL/HTTPS behind Render's proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
# -----------------------------------------------------------
# Installed Apps
# -----------------------------------------------------------
INSTALLED_APPS = [
    'daphne',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -----------------------------------------------------------
# URL / WSGI / ASGI
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
# Database (Neon/Render or local fallback)
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
# Static / Media
# -----------------------------------------------------------
STATIC_URL = 'static/'
# when running on Render/production, collectstatic should populate STATIC_ROOT
STATIC_ROOT = BASE_DIR / 'staticfiles_build' / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Whitenoise staticfiles storage in production (only use when DEBUG is False)
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# -----------------------------------------------------------
# Default primary key field
# -----------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -----------------------------------------------------------
# Custom User Model
# -----------------------------------------------------------
AUTH_USER_MODEL = 'api.User'

# -----------------------------------------------------------
# CORS
# -----------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://rawlink-frontend.vercel.app",
    'https://rawlink-api.onrender.com',
    # add frontend host(s) here when available
]
CSRF_TRUSTED_ORIGINS = [
    "https://rawlink-frontend.vercel.app", # <--- Add your Vercel URL here
]

# -----------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# -----------------------------------------------------------
# JWT Settings
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
# Channels / WebSocket Layer (Redis in prod, InMemory in dev)
# -----------------------------------------------------------
if 'REDIS_URL' in os.environ:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.environ.get('REDIS_URL')],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
