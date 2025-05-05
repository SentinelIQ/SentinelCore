from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Define app name for namespace
app_name = 'observables'

from api.v1.observables.views import ObservableViewSet

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'', ObservableViewSet, basename='observable')

urlpatterns = [
    path('', include(router.urls)),
] 