from django.urls import path, include
from api.routers import KebabCaseRouter
# Define app name for namespace
app_name = 'alerts'

from .views import AlertViewSet

# Configure router
router = KebabCaseRouter()
router.register(r'', AlertViewSet, basename='alert')

# URLs with kebab-case
urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),
] 