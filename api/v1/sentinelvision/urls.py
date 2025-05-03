"""
URL patterns for the SentinelVision API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.v1.sentinelvision.views.feed_views import FeedModuleViewSet
from api.v1.sentinelvision.views.enrichment_views import EnrichmentViewSet

router = DefaultRouter()
router.register(r'feeds', FeedModuleViewSet, basename='feed')
router.register(r'enrichment', EnrichmentViewSet, basename='enrichment')

urlpatterns = [
    path('', include(router.urls)),
] 