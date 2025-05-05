from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.v1.auth.views import (
    UserViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    EmailPasswordTokenObtainView,
    test_audit_log
)
from api.v1.audit_logs.views import AuditLogViewSet

# Define app name for URL namespace
app_name = 'auth'

# Create router for viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

# URLs using kebab-case standard
urlpatterns = [
    # Token endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/email-password/', EmailPasswordTokenObtainView.as_view(), name='token_email_password'),
    
    # Audit logs endpoints - Authentication & Access Control related logs
    path('audit-logs/', AuditLogViewSet.as_view({'get': 'list'}), name='audit-logs'),
    
    # Test endpoint for audit logs - FOR TESTING ONLY, REMOVE IN PRODUCTION
    path('test-audit-log/', test_audit_log, name='test-audit-log'),
]

# Add router URLs
urlpatterns += router.urls 