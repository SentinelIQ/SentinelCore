from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.v1.observables.views import ObservableViewSet

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'', ObservableViewSet, basename='observable')

urlpatterns = [
    path('', include(router.urls)),
] 