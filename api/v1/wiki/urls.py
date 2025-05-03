from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KnowledgeArticleViewSet, KnowledgeCategoryViewSet

app_name = 'wiki'

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'articles', KnowledgeArticleViewSet, basename='knowledge-article')
router.register(r'categories', KnowledgeCategoryViewSet, basename='knowledge-category')

urlpatterns = [
    path('', include(router.urls)),
] 