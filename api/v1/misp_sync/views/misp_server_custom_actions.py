from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from api.core.responses import success_response, error_response
from api.v1.misp_sync.models import MISPServer
from api.v1.misp_sync.serializers import MISPServerSerializer, MISPEventSerializer
from django.utils import timezone
from api.v1.misp_sync.tasks import sync_misp_server
import logging
import threading

logger = logging.getLogger('api')


class MISPServerCustomActionsMixin:
    """
    Mixin for custom actions on MISP server viewsets.
    """
    
    @extend_schema(
        summary="Synchronize with MISP server",
        description="Triggers a synchronization with the selected MISP server to import events",
        responses={
            200: OpenApiResponse(description="Synchronization initiated"),
            400: OpenApiResponse(description="Synchronization failed"),
            404: OpenApiResponse(description="MISP server not found")
        },
        parameters=[
            OpenApiParameter(
                name="days_back", 
                description="Number of days to go back for event synchronization", 
                type=int, 
                default=7
            ),
            OpenApiParameter(
                name="max_events", 
                description="Maximum number of events to sync", 
                type=int, 
                default=1000
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def sync(self, request, *args, **kwargs):
        """
        Trigger synchronization with a MISP server.
        """
        try:
            instance = self.get_object()
            
            # Get synchronization parameters
            days_back = int(request.query_params.get('days_back', 7))
            max_events = int(request.query_params.get('max_events', 1000))
            
            try:
                # Update last_sync timestamp to show sync was initiated
                instance.last_sync = timezone.now()
                instance.save(update_fields=['last_sync'])
                
                # Start the sync in a background thread instead of using Celery
                def run_sync():
                    try:
                        sync_misp_server(instance.id, days_back, max_events)
                        logger.info(f"Completed MISP synchronization for server {instance.name} (ID: {instance.id})")
                    except Exception as e:
                        logger.error(f"Background sync failed for server {instance.name} (ID: {instance.id}): {str(e)}")
                
                # Start the thread
                sync_thread = threading.Thread(target=run_sync)
                sync_thread.daemon = True
                sync_thread.start()
                
                logger.info(f"MISP synchronization initiated for server {instance.name} (ID: {instance.id})")
                
                # Return success response
                return success_response(
                    data={
                        "server_id": instance.id,
                        "status": "sync_started",
                        "parameters": {
                            "days_back": days_back,
                            "max_events": max_events
                        }
                    },
                    message="MISP synchronization initiated successfully"
                )
                
            except Exception as e:
                logger.error(f"Failed to initiate MISP synchronization for server {instance.name} (ID: {instance.id}): {str(e)}")
                
                return error_response(
                    message="Failed to initiate MISP synchronization",
                    errors={"detail": str(e)}
                )
        except NotFound:
            logger.error(f"MISP server not found with ID: {kwargs.get('pk')}")
            return error_response(
                message="MISP server not found",
                errors={"detail": f"No MISP server found with ID: {kwargs.get('pk')}"},
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Get MISP sync status",
        description="Retrieve the status of the last synchronization with this MISP server",
        responses={
            200: OpenApiResponse(description="Sync status retrieved"),
            404: OpenApiResponse(description="MISP server not found")
        }
    )
    @action(detail=True, methods=['get'])
    def sync_status(self, request, *args, **kwargs):
        """
        Get the status of synchronization with a MISP server.
        """
        try:
            instance = self.get_object()
            
            try:
                # Get event statistics
                total_events = instance.events.count()
                total_attributes = sum(event.attributes.count() for event in instance.events.all())
                total_objects = sum(event.objects.count() for event in instance.events.all())
                
                # Get the latest events
                latest_events = instance.events.order_by('-timestamp')[:5]
                latest_events_data = MISPEventSerializer(latest_events, many=True).data
                
                # Get event statistics by threat level
                threat_level_counts = {
                    'high': instance.events.filter(threat_level_id=1).count(),
                    'medium': instance.events.filter(threat_level_id=2).count(),
                    'low': instance.events.filter(threat_level_id=3).count(),
                    'undefined': instance.events.filter(threat_level_id=4).count()
                }
                
                return success_response(
                    data={
                        "server_id": instance.id,
                        "server_name": instance.name,
                        "last_sync": instance.last_sync,
                        "is_active": instance.is_active,
                        "stats": {
                            "total_events": total_events,
                            "total_attributes": total_attributes,
                            "total_objects": total_objects,
                            "threat_level_counts": threat_level_counts
                        },
                        "latest_events": latest_events_data
                    },
                    message="MISP synchronization status retrieved successfully"
                )
                
            except Exception as e:
                logger.error(f"Failed to get MISP sync status for server {instance.name} (ID: {instance.id}): {str(e)}")
                
                return error_response(
                    message="Failed to get MISP sync status",
                    errors={"detail": str(e)}
                )
        except NotFound:
            logger.error(f"MISP server not found with ID: {kwargs.get('pk')}")
            return error_response(
                message="MISP server not found",
                errors={"detail": f"No MISP server found with ID: {kwargs.get('pk')}"},
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Get MISP server events",
        description="Retrieve a paginated list of events from this MISP server",
        responses={
            200: MISPEventSerializer(many=True),
            404: OpenApiResponse(description="MISP server not found")
        }
    )
    @action(detail=True, methods=['get'])
    def events(self, request, *args, **kwargs):
        """
        Get events from a MISP server.
        """
        try:
            instance = self.get_object()
            queryset = instance.events.all()
            
            # Apply pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = MISPEventSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            # Return all events if pagination is not available
            serializer = MISPEventSerializer(queryset, many=True)
            return success_response(data=serializer.data)
        except NotFound:
            logger.error(f"MISP server not found with ID: {kwargs.get('pk')}")
            return error_response(
                message="MISP server not found",
                errors={"detail": f"No MISP server found with ID: {kwargs.get('pk')}"},
                status_code=status.HTTP_404_NOT_FOUND
            ) 