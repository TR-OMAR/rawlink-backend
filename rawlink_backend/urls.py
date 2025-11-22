from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve 

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

# 4. SERVE MEDIA FILES (Images)
# This block forces Django to serve user-uploaded files directly, 
# which is necessary for Render's local disk storage to work.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]