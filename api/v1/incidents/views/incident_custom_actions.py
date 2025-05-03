import logging
import uuid
from rest_framework import status
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from incidents.models import Incident, TimelineEvent, IncidentObservable, IncidentTask
from alerts.models import Alert
from api.core.responses import success_response, error_response
from api.core.rbac import HasEntityPermission
from ..serializers import (
    IncidentTimelineEntrySerializer, 
    IncidentAssignSerializer, 
    TimelineEventSerializer, 
    IncidentObservableSerializer, 
    IncidentObservableCreateSerializer, 
    IncidentTaskSerializer, 
    IncidentTaskCreateSerializer, 
    IncidentTaskUpdateSerializer, 
    IncidentReportFormatSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

logger = logging.getLogger('api.incidents')


class IncidentCustomActionsMixin:
    """
    Mixin for custom incident actions
    """
    entity_type = 'incident'  # Define entity type for RBAC
    
    @extend_schema(
        summary="Close an incident",
        description="Closes an incident and updates related alerts to 'resolved' status.",
        responses={
            200: OpenApiResponse(description="Incident closed successfully"),
            400: OpenApiResponse(description="Incident already closed"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    @action(detail=True, methods=['post'], url_path='close', permission_classes=[HasEntityPermission])
    def close_incident(self, request, pk=None):
        """
        Closes an incident and updates related alerts status.
        """
        incident = self.get_object()
        user = request.user
        
        # Check if incident is already closed
        if incident.status == Incident.Status.CLOSED:
            return error_response(
                message="This incident is already closed.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update incident status and set closure date
                incident.close()
                
                # Get related alerts
                related_alerts = incident.related_alerts.all()
                
                # Update alerts status to "resolved"
                for alert in related_alerts:
                    alert.status = Alert.Status.RESOLVED
                    alert.save(update_fields=['status'])
                
                logger.info(f"Incident {incident.id} closed by {user.username}")
                logger.info(f"{related_alerts.count()} related alerts marked as resolved")
                
                # Return response
                return success_response(
                    data={
                        "incident_id": incident.id,
                        "resolved_alerts_count": related_alerts.count()
                    },
                    message="Incident successfully closed and related alerts resolved."
                )
        
        except Exception as e:
            logger.error(f"Error closing incident {incident.id}: {str(e)}")
            return error_response(
                message=f"Error closing incident: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Add timeline entry",
        description="Adds a new entry to the incident timeline.",
        request=IncidentTimelineEntrySerializer,
        responses={
            200: OpenApiResponse(description="Timeline entry added successfully"),
            400: OpenApiResponse(description="Invalid timeline entry data"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    @action(detail=True, methods=['post'], url_path='add-timeline-entry', permission_classes=[HasEntityPermission])
    def add_timeline_entry(self, request, pk=None):
        """
        Add a timeline entry to an incident.
        """
        incident = self.get_object()
        user = request.user
        
        serializer = IncidentTimelineEntrySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid timeline entry data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                entry_data = serializer.validated_data
                
                # Get current timestamp if not provided
                timestamp = entry_data.get('timestamp', timezone.now())
                
                # Create timeline entry with metadata
                timeline_entry = {
                    "id": str(uuid.uuid4()),
                    "title": entry_data.get('title'),
                    "content": entry_data.get('content', ''),
                    "type": entry_data.get('event_type', 'note'),
                    "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else timestamp,
                    "created_by": str(user.id)
                }
                
                # Add entry to timeline
                if not incident.timeline:
                    incident.timeline = []
                incident.timeline.append(timeline_entry)
                incident.save(update_fields=['timeline'])
                
                logger.info(f"Timeline entry added to incident {incident.id} by {user.username}")
                
                # Return response
                return success_response(
                    data={
                        "incident_id": incident.id,
                        "timeline_entry": timeline_entry
                    },
                    message="Timeline entry added successfully"
                )
        
        except Exception as e:
            logger.error(f"Error adding timeline entry to incident {incident.id}: {str(e)}")
            return error_response(
                message=f"Error adding timeline entry: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Assign incident",
        description="Assigns an incident to a user.",
        request=IncidentAssignSerializer,
        responses={
            200: OpenApiResponse(description="Incident assigned successfully"),
            400: OpenApiResponse(description="Invalid assignee data"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    @action(detail=True, methods=['post'], url_path='assign', permission_classes=[HasEntityPermission])
    def assign_incident(self, request, pk=None):
        """
        Assign an incident to a user.
        """
        incident = self.get_object()
        user = request.user
        
        # Validate the request data using the serializer
        serializer = IncidentAssignSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid assignee data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the validated assignee ID
            assignee_id = serializer.validated_data.get('assignee')
            
            # Get user model
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Debug information
            logger.info(f"Looking up user with ID: {assignee_id}")
            logger.info(f"Type of ID: {type(assignee_id)}")
            
            # Different approaches to find the user
            try:
                # Try direct lookup using the ID as is
                assign_to = User.objects.get(id=assignee_id)
                logger.info(f"Found user by direct ID: {assign_to.username}")
            except User.DoesNotExist:
                try:
                    # Try converting to UUID first if it's a string
                    if isinstance(assignee_id, str):
                        uuid_obj = uuid.UUID(assignee_id)
                        assign_to = User.objects.get(id=uuid_obj)
                        logger.info(f"Found user by UUID conversion: {assign_to.username}")
                    else:
                        # If we get here, the assignee ID isn't a valid UUID
                        return error_response(
                            message=f"User with ID {assignee_id} does not exist",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
                except (ValueError, TypeError):
                    # Invalid UUID format
                    return error_response(
                        message=f"Invalid UUID format: {assignee_id}",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                except User.DoesNotExist:
                    # UUID conversion worked but user doesn't exist
                    return error_response(
                        message=f"User with ID {assignee_id} does not exist",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            
            # Check if user is active
            if not assign_to.is_active:
                return error_response(
                    message="Cannot assign to inactive user",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Update incident assignee
            with transaction.atomic():
                incident.assignee = assign_to
                
                # Add timeline entry for the assignment
                timeline_entry = {
                    "id": str(uuid.uuid4()),
                    "title": "Incident assigned",
                    "content": f"Incident assigned to user {assign_to.username}",
                    "type": "assignment",
                    "timestamp": timezone.now().isoformat(),
                    "created_by": str(user.id)
                }
                
                if not incident.timeline:
                    incident.timeline = []
                incident.timeline.append(timeline_entry)
                
                incident.save(update_fields=['assignee', 'timeline'])
                
                logger.info(f"Incident {incident.id} assigned to user {assign_to.username} by {user.username}")
                
                # Return response
                return success_response(
                    data={
                        "incident_id": incident.id,
                        "assignee": str(assign_to.id),
                        "timeline_entry": timeline_entry
                    },
                    message="Incident assigned successfully"
                )
        
        except Exception as e:
            logger.error(f"Error assigning incident {incident.id}: {str(e)}")
            return error_response(
                message=f"Error assigning incident: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get incident timeline",
        description="Retrieves the timeline for an incident.",
        responses={
            200: TimelineEventSerializer(many=True)
        }
    )
    @action(detail=True, methods=['get'], url_path='timeline', permission_classes=[HasEntityPermission])
    def get_timeline(self, request, pk=None):
        """
        Get the timeline for an incident.
        """
        incident = self.get_object()
        
        # Return timeline from incident model instead of separate TimelineEvent model
        timeline = incident.timeline or []
        
        # Sort by timestamp if available
        timeline = sorted(timeline, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Return as response
        return success_response(
            data=timeline,
            message=f"Retrieved {len(timeline)} timeline events."
        )
    
    @extend_schema(
        summary="List observables",
        description="Lists all observables associated with this incident.",
        responses={
            200: IncidentObservableSerializer(many=True)
        }
    )
    @action(detail=True, methods=['get'], url_path='observables')
    def list_observables(self, request, pk=None):
        """
        List all observables associated with this incident.
        """
        incident = self.get_object()
        incident_observables = incident.incident_observables.select_related('observable').all()
        serializer = IncidentObservableSerializer(incident_observables, many=True)
        
        return success_response(
            data=serializer.data,
            message=f"Retrieved {len(incident_observables)} observables for incident {incident.title}"
        )
    
    @extend_schema(
        summary="Add observable",
        description="Adds an observable to this incident.",
        request=IncidentObservableCreateSerializer,
        responses={
            201: IncidentObservableSerializer,
            200: IncidentObservableSerializer,
            400: OpenApiResponse(description="Invalid observable data")
        }
    )
    @action(detail=True, methods=['post'], url_path='add-observable')
    def add_observable(self, request, pk=None):
        """
        Add an observable to this incident.
        """
        incident = self.get_object()
        
        # Create serializer with incident context
        serializer = IncidentObservableCreateSerializer(
            data=request.data,
            context={'request': request, 'incident': incident}
        )
        
        if serializer.is_valid():
            try:
                observable = serializer.validated_data['observable']
                
                # Check if this observable is already linked to this incident
                existing = IncidentObservable.objects.filter(
                    incident=incident,
                    observable=observable
                ).first()
                
                if existing:
                    # Update existing relationship
                    for attr, value in serializer.validated_data.items():
                        setattr(existing, attr, value)
                    existing.save()
                    result_serializer = IncidentObservableSerializer(existing)
                    return success_response(
                        data=result_serializer.data,
                        message="Observable relationship updated",
                        status_code=status.HTTP_200_OK
                    )
                else:
                    # Create new relationship
                    incident_observable = IncidentObservable.objects.create(
                        incident=incident,
                        company=incident.company,
                        **serializer.validated_data
                    )
                    result_serializer = IncidentObservableSerializer(incident_observable)
                    
                    # Add to timeline
                    incident.add_timeline_entry(
                        title="Observable added",
                        content=f"Added observable: {observable.type}:{observable.value}",
                        event_type=TimelineEvent.EventType.OTHER,
                        created_by=request.user
                    )
                    
                    return success_response(
                        data=result_serializer.data,
                        message="Observable added to incident",
                        status_code=status.HTTP_201_CREATED
                    )
            except Exception as e:
                logger.error(f"Error adding observable to incident {incident.id}: {str(e)}")
                return error_response(
                    message=f"Error adding observable: {str(e)}",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        else:
            return error_response(
                data=serializer.errors,
                message="Invalid data",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Remove observable",
        description="Removes an observable from this incident.",
        parameters=[
            OpenApiParameter(name="observable_id", description="ID of the observable to remove", required=True, type=str)
        ],
        responses={
            200: OpenApiResponse(description="Observable removed successfully"),
            404: OpenApiResponse(description="Observable not found in this incident")
        }
    )
    @action(detail=True, methods=['delete'], url_path='remove-observable/(?P<observable_id>[^/.]+)')
    def remove_observable(self, request, pk=None, observable_id=None):
        """
        Remove an observable from this incident.
        """
        incident = self.get_object()
        
        try:
            # Attempt to find the relationship
            incident_observable = IncidentObservable.objects.filter(
                incident=incident,
                observable_id=observable_id
            ).first()
            
            if not incident_observable:
                return error_response(
                    message="Observable not found in this incident",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Save info for timeline
            observable_info = f"{incident_observable.observable.type}:{incident_observable.observable.value}"
            
            # Delete the relationship
            incident_observable.delete()
            
            # Add timeline entry
            incident.add_timeline_entry(
                title="Observable removed",
                content=f"Removed observable: {observable_info}",
                event_type=TimelineEvent.EventType.OTHER,
                created_by=request.user
            )
            
            return success_response(
                message="Observable removed from incident",
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error removing observable from incident {incident.id}: {str(e)}")
            return error_response(
                message=f"Error removing observable: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="List tasks",
        description="Lists all tasks associated with this incident.",
        responses={
            200: IncidentTaskSerializer(many=True)
        }
    )
    @action(detail=True, methods=['get'], url_path='tasks')
    def list_tasks(self, request, pk=None):
        """
        List all tasks associated with this incident.
        """
        incident = self.get_object()
        tasks = incident.tasks.all()
        serializer = IncidentTaskSerializer(tasks, many=True)
        
        return success_response(
            data=serializer.data,
            message=f"Retrieved {len(tasks)} tasks for incident {incident.title}"
        )
    
    @extend_schema(
        summary="Add task",
        description="Adds a new task to this incident.",
        request=IncidentTaskCreateSerializer,
        responses={
            201: IncidentTaskSerializer,
            400: OpenApiResponse(description="Invalid task data")
        }
    )
    @action(detail=True, methods=['post'], url_path='add-task')
    def add_task(self, request, pk=None):
        """
        Add a task to this incident.
        """
        incident = self.get_object()
        
        # Create serializer with incident context
        serializer = IncidentTaskCreateSerializer(
            data=request.data,
            context={'request': request, 'incident': incident}
        )
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Create task
                    task = serializer.save()
                    
                    # Add timeline entry
                    incident.add_timeline_entry(
                        title="Task added",
                        content=f"Added task: {task.title}",
                        event_type=TimelineEvent.EventType.TASK_ADDED,
                        created_by=request.user
                    )
                    
                    # Return response
                    result_serializer = IncidentTaskSerializer(task)
                    return success_response(
                        data=result_serializer.data,
                        message="Task added to incident",
                        status_code=status.HTTP_201_CREATED
                    )
            except Exception as e:
                logger.error(f"Error adding task to incident {incident.id}: {str(e)}")
                return error_response(
                    message=f"Error adding task: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return error_response(
                data=serializer.errors,
                message="Invalid task data",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Update task",
        description="Updates an existing task in this incident.",
        parameters=[
            OpenApiParameter(name="task_id", description="ID of the task to update", required=True, type=str)
        ],
        request=IncidentTaskUpdateSerializer,
        responses={
            200: IncidentTaskSerializer,
            400: OpenApiResponse(description="Invalid task data"),
            404: OpenApiResponse(description="Task not found")
        }
    )
    @action(detail=True, methods=['patch'], url_path='update-task/(?P<task_id>[^/.]+)')
    def update_task(self, request, pk=None, task_id=None):
        """
        Update a task in this incident.
        """
        incident = self.get_object()
        
        try:
            # Find the task
            task = IncidentTask.objects.get(id=task_id, incident=incident)
            
            # Create serializer
            serializer = IncidentTaskUpdateSerializer(
                task,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                try:
                    with transaction.atomic():
                        # Track status change for timeline
                        old_status = task.status
                        updated_task = serializer.save()
                        new_status = updated_task.status
                        
                        # Add timeline entry if status changed
                        if old_status != new_status:
                            event_type = TimelineEvent.EventType.TASK_COMPLETED if new_status == IncidentTask.Status.COMPLETED else TimelineEvent.EventType.OTHER
                            
                            incident.add_timeline_entry(
                                title=f"Task {updated_task.status}",
                                content=f"Task '{updated_task.title}' status changed from {task.get_status_display()} to {updated_task.get_status_display()}",
                                event_type=event_type,
                                created_by=request.user
                            )
                        
                        # Return response
                        result_serializer = IncidentTaskSerializer(updated_task)
                        return success_response(
                            data=result_serializer.data,
                            message="Task updated successfully"
                        )
                except Exception as e:
                    logger.error(f"Error updating task {task_id} in incident {incident.id}: {str(e)}")
                    return error_response(
                        message=f"Error updating task: {str(e)}",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return error_response(
                    data=serializer.errors,
                    message="Invalid task data",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except IncidentTask.DoesNotExist:
            return error_response(
                message="Task not found in this incident",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Delete task",
        description="Deletes a task from this incident.",
        parameters=[
            OpenApiParameter(name="task_id", description="ID of the task to delete", required=True, type=str)
        ],
        responses={
            200: OpenApiResponse(description="Task deleted successfully"),
            404: OpenApiResponse(description="Task not found")
        }
    )
    @action(detail=True, methods=['delete'], url_path='delete-task/(?P<task_id>[^/.]+)')
    def delete_task(self, request, pk=None, task_id=None):
        """
        Delete a task from this incident.
        """
        incident = self.get_object()
        
        try:
            # Find the task
            task = IncidentTask.objects.get(id=task_id, incident=incident)
            
            # Save info for timeline
            task_title = task.title
            
            # Delete the task
            task.delete()
            
            # Add timeline entry
            incident.add_timeline_entry(
                title="Task deleted",
                content=f"Deleted task: {task_title}",
                event_type=TimelineEvent.EventType.OTHER,
                created_by=request.user
            )
            
            return success_response(
                message="Task deleted successfully",
                status_code=status.HTTP_200_OK
            )
        except IncidentTask.DoesNotExist:
            return error_response(
                message="Task not found in this incident",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
    @extend_schema(
        summary="Run SentinelVision responder",
        description="Triggers a SentinelVision responder for this incident.",
        parameters=[
            OpenApiParameter(name="responder_id", description="ID of the responder to run (optional)", required=False, type=str)
        ],
        responses={
            200: OpenApiResponse(description="Responder triggered successfully"),
            500: OpenApiResponse(description="Error running responder")
        }
    )
    @action(detail=True, methods=['post'], url_path='run-responder')
    def run_responder(self, request, pk=None):
        """
        Trigger a SentinelVision responder for this incident.
        """
        incident = self.get_object()
        responder_id = request.data.get('responder_id')
        
        try:
            # Run responder
            result = incident.run_sentinelvision_responder(responder_id)
            
            # Add to timeline
            incident.add_timeline_entry(
                title="Responder triggered",
                content=f"SentinelVision responder {responder_id or 'all'} was triggered",
                event_type=TimelineEvent.EventType.SYSTEM,
                created_by=request.user
            )
            
            return success_response(
                data=result,
                message="SentinelVision responder triggered successfully"
            )
        except Exception as e:
            logger.error(f"Error running responder for incident {incident.id}: {str(e)}")
            return error_response(
                message=f"Error running responder: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Generate incident report",
        description="Generates a report for this incident in the specified format.",
        request=IncidentReportFormatSerializer,
        responses={
            200: OpenApiResponse(description="Report generated successfully"),
            400: OpenApiResponse(description="Invalid report options"),
            500: OpenApiResponse(description="Error generating report")
        }
    )
    @action(detail=True, methods=['post'], url_path='generate-report')
    def generate_report(self, request, pk=None):
        """
        Generate a report for this incident.
        """
        incident = self.get_object()
        
        # Validate format options
        serializer = IncidentReportFormatSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                data=serializer.errors,
                message="Invalid report options",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate report
            format_type = serializer.validated_data.get('format', 'pdf')
            result = incident.export_to_report(format_type)
            
            # Add to timeline
            incident.add_timeline_entry(
                title="Report generated",
                content=f"Generated {format_type} report",
                event_type=TimelineEvent.EventType.OTHER,
                created_by=request.user
            )
            
            return success_response(
                data=result,
                message=f"Report generated successfully in {format_type} format"
            )
        except Exception as e:
            logger.error(f"Error generating report for incident {incident.id}: {str(e)}")
            return error_response(
                message=f"Error generating report: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 