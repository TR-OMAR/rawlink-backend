from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileViewSet,
    WalletViewSet,
    ListingViewSet,
    OrderViewSet,
    MessageViewSet,
    UserViewSet,
)

# Initialize DRF router
router = DefaultRouter()

# Register API endpoints for each ViewSet
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'users', UserViewSet, basename='user')  # User endpoints must be registered

# Include router URLs in app's URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
