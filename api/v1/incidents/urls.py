from django.urls import path, include
from api.routers import KebabCaseRouter
from .views import IncidentViewSet

# Configure router
router = KebabCaseRouter()
router.register(r'', IncidentViewSet, basename='incident')

# URLs with kebab-case
urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),
] 