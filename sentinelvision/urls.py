from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sentinelvision.views import (
    FeedViewSet,
    AnalyzerViewSet,
    ResponderViewSet,
    ExecutionRecordViewSet
)

app_name = 'sentinelvision'

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'feeds', FeedViewSet, basename='feed')
router.register(r'analyzers', AnalyzerViewSet, basename='analyzer')
router.register(r'responders', ResponderViewSet, basename='responder')
router.register(r'executions', ExecutionRecordViewSet, basename='execution')

urlpatterns = [
    path('', include(router.urls)),
] 