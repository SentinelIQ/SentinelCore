from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from api.core.viewsets import StandardViewSet
from api.core.rbac import HasEntityPermission


@extend_schema_view(
    list=extend_schema(tags=['SentinelVision Feeds']),
    retrieve=extend_schema(tags=['SentinelVision Feeds']),
    create=extend_schema(tags=['SentinelVision Feeds']),
    update=extend_schema(tags=['SentinelVision Feeds']),
    partial_update=extend_schema(tags=['SentinelVision Feeds']),
    destroy=extend_schema(tags=['SentinelVision Feeds']),
)
class FeedViewSet(StandardViewSet):
    """
    ViewSet for viewing and editing threat intelligence feeds.
    """
