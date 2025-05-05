from django.urls import path
from rest_framework.routers import DefaultRouter
# Define app name for namespace
app_name = 'common'

from . import views
from api.core.views import test_sentry

# Router for ViewSets
router = DefaultRouter()
router.register(r'', views.CommonViewSet, basename='common')

# Individual URLs for backward compatibility and common utilities
urlpatterns = [
    path('health-check/', views.health_check, name='health-check'),
    path('whoami/', views.whoami, name='whoami'),
    path('test-sentry/', test_sentry, name='test-sentry'),
]

# Add router URLs
urlpatterns += router.urls 