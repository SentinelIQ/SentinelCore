from django.urls import path
from rest_framework.routers import DefaultRouter
# Define app name for namespace
app_name = 'tasks'

from .views import TaskViewSet

# Router for ViewSets
router = DefaultRouter()
router.register(r'', TaskViewSet, basename='task')

urlpatterns = router.urls 