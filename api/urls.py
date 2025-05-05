from django.urls import path, include
from rest_framework.routers import DefaultRouter
from auth_app.views import UserViewSet
from companies.views import CompanyViewSet

app_name = 'api'

# Create a router for API endpoints
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'companies', CompanyViewSet, basename='company')

# API URL patterns
urlpatterns = [
    # API endpoints
    path('', include(router.urls)),

    # API versions
    path('v1/', include('api.v1.urls', namespace='v1')),
] 