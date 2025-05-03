from django.urls import path, include
from api.routers import KebabCaseRouter
from .views import AlertViewSet

# Configure router
router = KebabCaseRouter()
router.register(r'', AlertViewSet, basename='alert')

# URLs with kebab-case
urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),
] 