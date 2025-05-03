from django.urls import path, include
from api.routers import KebabCaseRouter
from .views import CompanyViewSet

# Configure router
router = KebabCaseRouter()
router.register(r'', CompanyViewSet, basename='company')

# URLs with kebab-case
urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),
] 