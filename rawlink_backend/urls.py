from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

# --- ADMIN PANEL Interface ---
admin.site.site_header = "RawLink Administration"
admin.site.site_title = "RawLink Admin Portal"
admin.site.index_title = "Welcome to RawLink Dashboard"

urlpatterns = [
    # 1. Django Admin Panel
    path('admin/', admin.site.urls),
    
    # 2. API URLs (all ViewSet routes registered in api/urls.py)
    path('api/', include('api.urls')),
    
    # 3. Authentication endpoints provided by Djoser
    # - User registration: /api/auth/users/
    # - JWT login: /api/auth/jwt/create/
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
]
