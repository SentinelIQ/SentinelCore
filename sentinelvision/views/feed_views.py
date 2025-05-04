from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from api.core.viewsets import StandardViewSet
from api.core.rbac import HasEntityPermission


@extend_schema_view(
    list=extend_schema(tags=['Threat Intelligence (SentinelVision)']),
    retrieve=extend_schema(tags=['Threat Intelligence (SentinelVision)']),
    create=extend_schema(tags=['Threat Intelligence (SentinelVision)']),
    update=extend_schema(tags=['Threat Intelligence (SentinelVision)']),
    partial_update=extend_schema(tags=['Threat Intelligence (SentinelVision)']),
    destroy=extend_schema(tags=['Threat Intelligence (SentinelVision)']),
)
class FeedViewSet(StandardViewSet):
    """
    ViewSet for viewing and editing threat intelligence feeds.
    """
