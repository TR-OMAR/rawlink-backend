from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve 

# --- ADMIN PANEL CUSTOMIZATION ---
admin.site.site_header = "RawLink Administration"
admin.site.site_title = "RawLink Admin Portal"
admin.site.index_title = "Welcome to RawLink Dashboard"

urlpatterns = [
    # 1. Django Admin Panel
    path('admin/', admin.site.urls),
    
    # 2. Our API app's URLs
    # This includes all the ViewSet URLs (listings, orders, etc.)
    path('api/', include('api.urls')),
    
    # 3. Authentication URLs from Djoser
    # This gives us /api/auth/users/ (register)
    # and /api/auth/jwt/create/ (login to get token)
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
]
