from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

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

# This is a helper to serve user-uploaded images (like listing photos)
# during development (when DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)