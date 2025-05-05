from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MISPServerViewSet, MISPEventViewSet, MISPAttributeViewSet

# Set app name for namespace
app_name = 'misp_sync'

# Create a router for the API
router = DefaultRouter()
router.register(r'servers', MISPServerViewSet, basename='misp-server')
router.register(r'events', MISPEventViewSet, basename='misp-event')
router.register(r'attributes', MISPAttributeViewSet, basename='misp-attribute')

# Define URL patterns
urlpatterns = [
    path('', include(router.urls)),
] 