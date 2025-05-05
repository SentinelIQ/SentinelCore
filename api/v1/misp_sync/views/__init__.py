from rest_framework import filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse
from api.core.responses import success_response, error_response

from api.v1.misp_sync.models import MISPServer, MISPEvent, MISPAttribute, MISPObject
from api.v1.misp_sync.serializers import (
    MISPServerSerializer, MISPServerDetailSerializer, MISPServerCreateSerializer,
    MISPEventSerializer, MISPEventDetailSerializer,
    MISPAttributeSerializer, MISPAttributeDetailSerializer
)
from api.v1.misp_sync.filters import MISPServerFilter, MISPEventFilter, MISPAttributeFilter
from api.v1.misp_sync.permissions import MISPPermission
from api.core.pagination import StandardResultsSetPagination
from api.core.viewsets import StandardViewSet
from api.v1.alerts.serializers import AlertSerializer
from api.v1.incidents.serializers import IncidentSerializer

from .misp_server_create import MISPServerCreateMixin
from .misp_server_detail import MISPServerDetailMixin
from .misp_server_custom_actions import MISPServerCustomActionsMixin


@extend_schema(tags=['MISP Sync - Servers'])
class MISPServerViewSet(
    MISPServerCreateMixin, 
    MISPServerDetailMixin, 
    MISPServerCustomActionsMixin, 
    StandardViewSet
):
    """
    API endpoint for managing MISP server configurations.
    
    MISP (Malware Information Sharing Platform) servers are external threat intelligence
    platforms that can be synchronized with SentinelIQ to import events and attributes.
    """
    serializer_class = MISPServerSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [MISPPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MISPServerFilter
    search_fields = ['name', 'url', 'description']
    ordering_fields = ['name', 'created_at', 'last_sync']
    ordering = ['name']
    entity_type = 'misp_server'
    
    # Success messages for standardized responses
    success_message_create = "MISP server created successfully"
    success_message_update = "MISP server updated successfully"
    success_message_delete = "MISP server deleted successfully"
    
    def get_serializer_class(self):
        """
        Returns the appropriate serializer based on the action.
        """
        if self.action == 'create':
            return MISPServerCreateSerializer
        elif self.action == 'retrieve':
            return MISPServerDetailSerializer
        return MISPServerSerializer
    
    def get_queryset(self):
        """
        Returns only MISP servers from the user's company, unless the user is a superuser.
        """
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return MISPServer.objects.none()
            
        user = self.request.user
        
        if user.is_superuser:
            return MISPServer.objects.all()
            
        return MISPServer.objects.filter(company=user.company)


@extend_schema(tags=['MISP Sync - Events'])
class MISPEventViewSet(StandardViewSet):
    """
    API endpoint for MISP events.
    
    MISP events are security events/incidents imported from MISP threat intelligence
    platforms, containing indicators of compromise and other threat data.
    """
    serializer_class = MISPEventSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [MISPPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MISPEventFilter
    search_fields = ['info', 'org_name', 'orgc_name', 'tags']
    ordering_fields = ['created_at', 'timestamp', 'threat_level_id']
    ordering = ['-timestamp']
    entity_type = 'misp_event'
    
    def get_serializer_class(self):
        """
        Returns the appropriate serializer based on the action.
        """
        if self.action == 'retrieve':
            return MISPEventDetailSerializer
        elif self.action == 'convert_to_alert':
            return AlertSerializer
        elif self.action == 'convert_to_incident':
            return IncidentSerializer
        return MISPEventSerializer
    
    def get_queryset(self):
        """
        Returns only MISP events from the user's company, unless the user is a superuser.
        """
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return MISPEvent.objects.none()
            
        user = self.request.user
        
        if user.is_superuser:
            return MISPEvent.objects.all()
            
        return MISPEvent.objects.filter(company=user.company)
    
    @extend_schema(
        summary="Convert MISP event to alert",
        description="Converts a MISP event to a SentinelIQ alert with associated observables.",
        responses={
            200: OpenApiResponse(description="Event successfully converted to alert"),
            400: OpenApiResponse(description="Error converting event to alert"),
            404: OpenApiResponse(description="Event not found")
        }
    )
    @action(detail=True, methods=['post'])
    def convert_to_alert(self, request, *args, **kwargs):
        """
        Convert a MISP event to a SentinelIQ alert.
        """
        instance = self.get_object()
        
        try:
            result = instance.convert_to_alert()
            
            if result.get('status') == 'completed':
                return success_response(
                    data={"event_id": instance.id, "alert_id": result.get('alert_id')},
                    message=f"MISP event '{instance.info}' successfully converted to alert."
                )
            elif result.get('status') == 'already_converted':
                return success_response(
                    data={"event_id": instance.id, "alert_id": result.get('alert_id')},
                    message=f"MISP event '{instance.info}' was already converted to alert."
                )
            else:
                return error_response(
                    message=f"Error converting MISP event to alert: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            return error_response(
                message=f"Error converting MISP event to alert: {str(e)}"
            )
    
    @extend_schema(
        summary="Convert MISP event to incident",
        description="Converts a MISP event directly to a SentinelIQ incident with associated observables.",
        responses={
            200: OpenApiResponse(description="Event successfully converted to incident"),
            400: OpenApiResponse(description="Error converting event to incident"),
            404: OpenApiResponse(description="Event not found")
        }
    )
    @action(detail=True, methods=['post'])
    def convert_to_incident(self, request, *args, **kwargs):
        """
        Convert a MISP event directly to a SentinelIQ incident.
        """
        instance = self.get_object()
        
        try:
            result = instance.convert_to_incident()
            
            if result.get('status') == 'completed':
                return success_response(
                    data={"event_id": instance.id, "incident_id": result.get('incident_id')},
                    message=f"MISP event '{instance.info}' successfully converted to incident."
                )
            elif result.get('status') == 'already_converted':
                return success_response(
                    data={"event_id": instance.id, "incident_id": result.get('incident_id')},
                    message=f"MISP event '{instance.info}' was already converted to incident."
                )
            else:
                return error_response(
                    message=f"Error converting MISP event to incident: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            return error_response(
                message=f"Error converting MISP event to incident: {str(e)}"
            )
    
    @extend_schema(
        summary="Sync MISP events",
        description="Trigger a synchronization of MISP events from all active servers.",
        responses={
            200: OpenApiResponse(description="Sync process initiated")
        }
    )
    @action(detail=False, methods=['post'])
    def sync(self, request, *args, **kwargs):
        """
        Trigger a synchronization of MISP events from all active servers.
        """
        from api.v1.misp_sync.tasks import schedule_misp_sync_for_active_servers
        
        try:
            # Trigger sync task
            result = schedule_misp_sync_for_active_servers()
            
            return success_response(
                data={
                    "servers_scheduled": result.get('servers_scheduled', 0),
                    "total_active_servers": result.get('total_active_servers', 0)
                },
                message="MISP synchronization scheduled successfully."
            )
                
        except Exception as e:
            return error_response(
                message=f"Error scheduling MISP synchronization: {str(e)}"
            )


@extend_schema(tags=['MISP Sync - Objects'])
class MISPObjectViewSet(StandardViewSet):
    """
    API endpoint for MISP objects.
    
    MISP objects are structured data within MISP events, representing complex entities
    like file objects, network connections, or other structured threat intelligence data.
    """
    serializer_class = MISPAttributeSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [MISPPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'comment']
    ordering_fields = ['created_at', 'timestamp', 'name', 'meta_category']
    ordering = ['-timestamp']
    entity_type = 'misp_object'
    
    def get_queryset(self):
        """
        Returns only MISP objects from the user's company, unless the user is a superuser.
        Enforces tenant isolation.
        """
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return MISPObject.objects.none()
            
        user = self.request.user
        
        if user.is_superuser:
            return MISPObject.objects.all()
            
        return MISPObject.objects.filter(event__company=user.company)


@extend_schema(tags=['MISP Sync - Attributes'])
class MISPAttributeViewSet(StandardViewSet):
    """
    API endpoint for MISP attributes.
    
    MISP attributes are individual indicators or data points within MISP events,
    such as IP addresses, URLs, file hashes, or other observable data.
    """
    serializer_class = MISPAttributeSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [MISPPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MISPAttributeFilter
    search_fields = ['value', 'comment', 'tags']
    ordering_fields = ['created_at', 'timestamp', 'type', 'category']
    ordering = ['-timestamp']
    entity_type = 'misp_attribute'
    
    def get_serializer_class(self):
        """
        Returns the appropriate serializer based on the action.
        """
        if self.action == 'retrieve':
            return MISPAttributeDetailSerializer
        return MISPAttributeSerializer
    
    def get_queryset(self):
        """
        Returns only MISP attributes from the user's company, unless the user is a superuser.
        Enforces tenant isolation.
        """
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return MISPAttribute.objects.none()
            
        user = self.request.user
        
        if user.is_superuser:
            return MISPAttribute.objects.all()
            
        return MISPAttribute.objects.filter(event__company=user.company)
    
    @extend_schema(
        summary="Convert MISP attribute to observable",
        description="Converts a MISP attribute to a SentinelIQ observable.",
        responses={
            200: OpenApiResponse(description="Attribute successfully converted to observable"),
            400: OpenApiResponse(description="Error converting attribute to observable"),
            404: OpenApiResponse(description="Attribute not found")
        }
    )
    @action(detail=True, methods=['post'])
    def convert_to_observable(self, request, *args, **kwargs):
        """
        Convert a MISP attribute to a SentinelIQ observable.
        """
        instance = self.get_object()
        
        try:
            observable = instance.convert_to_observable()
            
            if observable:
                return success_response(
                    data={"attribute_id": instance.id, "observable_id": observable.id},
                    message=f"MISP attribute successfully converted to observable."
                )
            else:
                return error_response(
                    message=f"Error converting MISP attribute to observable: Unsupported attribute type '{instance.type}'."
                )
                
        except Exception as e:
            return error_response(
                message=f"Error converting MISP attribute to observable: {str(e)}"
            )


__all__ = [
    'MISPServerViewSet',
    'MISPEventViewSet',
    'MISPObjectViewSet',
    'MISPAttributeViewSet',
]
