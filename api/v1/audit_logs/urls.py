from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Define app name for namespace
app_name = 'audit_logs'

from .views import AuditLogViewSet

# Create a router for the API
router = DefaultRouter()
router.register(r'', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
] 