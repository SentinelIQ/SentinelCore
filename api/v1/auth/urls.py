from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    EmailPasswordTokenObtainView,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

# URLs using kebab-case standard
urlpatterns = [
    # User management endpoints
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('token/email/', EmailPasswordTokenObtainView.as_view(), name='token-email'),
] 