import logging
import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from api.core.responses import success_response, error_response, created_response
from alerts.models import Alert
from companies.models import Company
from observables.models import Observable
from api.v1.alerts.enums import AlertStatusEnum
from ..serializers import (
    AlertCreateSerializer, 
    AlertSerializer, 
    ObservableLightSerializer,
    ObservableAddToAlertSerializer
)
from incidents.models import Incident
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

logger = logging.getLogger('api.alerts')


class AlertCustomActionsMixin:
    """
    Mixin for custom alert actions such as escalation and ingestion
    """
    @extend_schema(
        tags=['Alert Management'],
        summary="Escalate alert to incident",
        description="Converts an alert to an incident by creating a new incident linked to this alert and changes the alert status to 'escalated'.",
        responses={
            201: OpenApiResponse(description="Alert successfully escalated", response=dict),
            400: OpenApiResponse(description="Alert already escalated"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    @action(detail=True, methods=['post'], url_path='escalate')
    def escalate(self, request, pk=None):
        """
        Escalates an alert to an incident.
        
        This creates a new incident linked to the alert and changes
        the alert status to 'escalated'.
        """
        alert = self.get_object()
        user = request.user
        
        # Validate tenant isolation - users can only escalate alerts from their company
        if not user.is_superuser and hasattr(user, 'company') and user.company != alert.company:
            logger.warning(f"User {user.username} from company {user.company} attempted to escalate alert {alert.id} from company {alert.company}")
            return error_response(
                message="You don't have permission to escalate alerts for this company.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if alert is already escalated
        if not alert.can_escalate():
            return error_response(
                message="Alert is already escalated.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create a new incident from the alert
        try:
            with transaction.atomic():
                # Create the timeline entry
                current_time = timezone.now().isoformat()
                
                timeline_entry = {
                    "id": str(uuid.uuid4()),
                    "title": "Incident created from alert",
                    "content": f"Escalated from alert: {alert.title} ({alert.id})",
                    "type": "escalation",
                    "timestamp": current_time,
                    "created_by": str(user.id)
                }
                
                # Create incident linked to the alert, ensuring all fields are valid
                incident = Incident.objects.create(
                    title=alert.title,
                    description=alert.description or "",
                    severity=alert.severity,
                    company=alert.company,
                    created_by=user,
                    timeline=[timeline_entry],
                    # Copy standard fields
                    tags=alert.tags or [],
                    tlp=alert.tlp,
                    pap=alert.pap
                )
                
                # Link alert to incident
                incident.related_alerts.add(alert)
                
                # Mark alert as escalated
                alert.status = AlertStatusEnum.ESCALATED.value
                alert.save(update_fields=['status'])
                
                logger.info(f"Alert escalated: {alert.title} to incident {incident.id} by {user.username}")
                
                return created_response(
                    data={"incident_id": incident.id},
                    message="Alert escalated to incident successfully."
                )
                
        except Exception as e:
            logger.error(f"Error escalating alert {alert.id}: {str(e)}")
            return error_response(
                message=f"Error escalating alert: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['Alert Management'],
        summary="Ingest alerts from external systems",
        description="Endpoint for external systems to send alerts to Sentineliq with deduplication.",
        request=AlertCreateSerializer,
        responses={
            201: OpenApiResponse(description="Alert successfully ingested", response=dict),
            200: OpenApiResponse(description="Alert already exists (duplicate)", response=dict),
            400: OpenApiResponse(description="Invalid alert data"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    @action(detail=False, methods=['post'], url_path='ingest', permission_classes=[IsAuthenticated])
    def ingest(self, request):
        """
        Ingests alerts from external systems.
        
        This endpoint allows external systems to send alerts to Sentineliq.
        It processes the incoming data, validates it, and creates a new alert
        with proper deduplication.
        """
        # Handle authentication - request.user or API token
        if hasattr(request, 'user'):
            user = request.user
        else:
            # For non-authenticated requests or testing
            user = None
        
        company = None
        alert_data = request.data.copy()
        
        # Get company from user or from company_id parameter
        if user is not None and hasattr(user, 'company') and user.company is not None:
            company = user.company
        elif 'company_id' in alert_data:
            try:
                company_id = alert_data.pop('company_id')
                company = Company.objects.get(id=company_id)
                
                # Validate that non-superuser can only ingest alerts for their company
                if user and not user.is_superuser and hasattr(user, 'company') and user.company != company:
                    logger.warning(f"User {user.username} attempted to ingest alert for company {company.id} but belongs to company {user.company.id}")
                    return error_response(
                        message="You don't have permission to ingest alerts for this company.",
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            except Company.DoesNotExist:
                return error_response(
                    message=f"Company with ID {company_id} does not exist.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        else:
            return error_response(
                message="User without a company must provide a company_id in the request.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for required fields
        required_fields = ['title', 'description', 'source', 'source_ref']
        missing_fields = [field for field in required_fields if field not in alert_data]
        
        if missing_fields:
            return error_response(
                message=f"Missing required fields: {', '.join(missing_fields)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure external_source is set - use source as default if not provided
        if not alert_data.get('external_source'):
            alert_data['external_source'] = alert_data.get('source', '')
        
        # Perform deduplication check using optimized query
        try:
            # Check for duplicates based on source_ref and external_source
            existing_alert = Alert.objects.filter(
                source_ref=alert_data.get('source_ref'),
                external_source=alert_data.get('external_source'),
                company=company
            ).first()
            
            if existing_alert:
                logger.info(f"Duplicate alert detected: {alert_data.get('source_ref')} from {alert_data.get('source')}")
                return success_response(
                    data={"alert_id": existing_alert.id, "duplicate": True},
                    message="Alert already exists.",
                    status_code=status.HTTP_200_OK
                )
            
            # Create the alert if it doesn't exist
            serializer = AlertCreateSerializer(data=alert_data, context={'request': request})
            if serializer.is_valid():
                try:
                    with transaction.atomic():
                        # Set created_by only if user is available
                        alert = serializer.save(
                            company=company,
                            created_by=user if user is not None else None,
                            external_source=alert_data.get('external_source')
                        )
                        
                        # Log with or without username
                        if user is not None:
                            logger.info(f"Alert ingested: {alert.title} ({alert.source}) by {user.username}")
                        else:
                            logger.info(f"Alert ingested: {alert.title} ({alert.source}) by API")
                        
                        return success_response(
                            data={"alert_id": alert.id, "duplicate": False},
                            message="Alert successfully ingested.",
                            status_code=status.HTTP_201_CREATED
                        )
                except Exception as e:
                    logger.error(f"Error ingesting alert: {str(e)}")
                    return error_response(
                        message=f"Error ingesting alert: {str(e)}",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return error_response(
                    message="Invalid alert data.",
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error ingesting alert: {str(e)}")
            return error_response(
                message=f"Error ingesting alert: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['Alert Management'],
        summary="List observables in alert",
        description="Lists all observables associated with this alert.",
        responses={
            200: ObservableLightSerializer(many=True)
        }
    )
    @action(detail=True, methods=['get'], url_path='observables')
    def observables(self, request, pk=None):
        """
        Lists all observables associated with this alert.
        """
        alert = self.get_object()
        observables = alert.observables.all()
        
        serializer = ObservableLightSerializer(observables, many=True)
        return success_response(
            data=serializer.data,
            message=f"Retrieved {len(observables)} observables."
        )

    @extend_schema(
        tags=['Alert Management'],
        summary="Add observable to alert",
        description="Links an existing observable to this alert.",
        request=ObservableAddToAlertSerializer,
        responses={
            201: OpenApiResponse(description="Observable added successfully", response=ObservableLightSerializer),
            400: OpenApiResponse(description="Invalid data"),
            409: OpenApiResponse(description="Observable already linked to this alert")
        }
    )
    @action(detail=True, methods=['post'], url_path='add-observable')
    def add_observable(self, request, pk=None):
        """
        Adds an observable to this alert.
        """
        alert = self.get_object()
        
        # Set context for serializer validation
        serializer = ObservableAddToAlertSerializer(data=request.data, context={'alert': alert})
        
        if serializer.is_valid():
            observable = serializer.validated_data['observable']
            is_ioc = serializer.validated_data.get('is_ioc', False)
            
            # Check if observable is already linked to this alert
            if observable in alert.observables.all():
                # Just return success since it's already linked
                observable_data = ObservableLightSerializer(observable).data
                return success_response(
                    data=observable_data,
                    message="Observable is already linked to this alert.",
                    status_code=status.HTTP_200_OK
                )
            
            try:
                # Add observable to the alert
                alert.add_observable(observable, is_ioc)
                
                logger.info(f"Observable {observable.id} added to alert {alert.id}")
                
                # Return the observable data
                observable_data = ObservableLightSerializer(observable).data
                return created_response(
                    data=observable_data,
                    message="Observable added to alert successfully."
                )
                
            except Exception as e:
                logger.error(f"Error adding observable to alert {alert.id}: {str(e)}")
                return error_response(
                    message=f"Error adding observable: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return error_response(
                message="Invalid observable data.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        tags=['Alert Management'],
        summary="Remove observable from alert",
        description="Removes the link between an observable and this alert.",
        parameters=[
            OpenApiParameter(name="observable_id", description="UUID of the observable to remove", required=True, type=str)
        ],
        responses={
            200: OpenApiResponse(description="Observable removed successfully"),
            404: OpenApiResponse(description="Observable not found in this alert"),
            500: OpenApiResponse(description="Server error")
        }
    )
    @action(detail=True, methods=['delete'], url_path='remove-observable/(?P<observable_id>[^/.]+)')
    def remove_observable(self, request, pk=None, observable_id=None):
        """
        Removes an observable from this alert.
        """
        alert = self.get_object()
        
        try:
            # Try to get the observable
            try:
                observable = Observable.objects.get(id=observable_id)
            except Observable.DoesNotExist:
                return error_response(
                    message=f"Observable with ID {observable_id} does not exist.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Check if observable is linked to this alert
            if observable not in alert.observables.all():
                return error_response(
                    message="Observable is not linked to this alert.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Remove observable from alert
            alert.remove_observable(observable)
            
            logger.info(f"Observable {observable_id} removed from alert {alert.id}")
            
            return success_response(
                message="Observable removed from alert successfully."
            )
            
        except Exception as e:
            logger.error(f"Error removing observable from alert {alert.id}: {str(e)}")
            return error_response(
                message=f"Error removing observable: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['Alert Management'],
        summary="Sync observables from JSON",
        description="Convert observables stored in observable_data JSON field to proper M2M relationships.",
        responses={
            200: OpenApiResponse(description="Observables synchronized successfully", response=dict),
            500: OpenApiResponse(description="Server error")
        }
    )
    @action(detail=True, methods=['post'], url_path='sync-from-json')
    def sync_observables_from_json(self, request, pk=None):
        """
        Synchronizes observables from observable_data JSON to M2M relationships.
        """
        alert = self.get_object()
        
        if not alert.observable_data:
            return success_response(
                message="No observable data to synchronize.",
                data={"synchronized": 0}
            )
        
        try:
            with transaction.atomic():
                # Track counts for reporting
                created_count = 0
                linked_count = 0
                skipped_count = 0
                
                # Process observable_data based on its structure
                if isinstance(alert.observable_data, dict):
                    # Process by observable type
                    for obs_type, values in alert.observable_data.items():
                        if not isinstance(values, list):
                            values = [values]  # Ensure values is a list
                            
                        for value in values:
                            if value and isinstance(value, str):
                                # Find or create observable
                                obs, created = Observable.objects.get_or_create(
                                    type=obs_type,
                                    value=value,
                                    company=alert.company,
                                    defaults={
                                        'created_by': alert.created_by,
                                    }
                                )
                                
                                if created:
                                    created_count += 1
                                
                                # Link observable to alert if not already linked
                                if obs not in alert.observables.all():
                                    alert.add_observable(observable=obs, is_ioc=True)
                                    linked_count += 1
                                else:
                                    skipped_count += 1
                                    
                elif isinstance(alert.observable_data, list):
                    # Process flat list structure
                    for item in alert.observable_data:
                        if isinstance(item, dict) and 'type' in item and 'value' in item:
                            # Find or create observable
                            obs, created = Observable.objects.get_or_create(
                                type=item['type'],
                                value=item['value'],
                                company=alert.company,
                                defaults={
                                    'created_by': alert.created_by,
                                    'is_ioc': item.get('is_ioc', False),
                                    'tags': item.get('tags', [])
                                }
                            )
                            
                            if created:
                                created_count += 1
                            
                            # Link observable to alert if not already linked
                            if obs not in alert.observables.all():
                                alert.add_observable(observable=obs, is_ioc=item.get('is_ioc', False))
                                linked_count += 1
                            else:
                                skipped_count += 1
                
                logger.info(f"Synchronized observables for alert {alert.id}: created={created_count}, linked={linked_count}, skipped={skipped_count}")
                
                return success_response(
                    message="Observables synchronized successfully.",
                    data={
                        "created": created_count,
                        "linked": linked_count,
                        "skipped": skipped_count,
                        "total": created_count + linked_count + skipped_count
                    }
                )
                
        except Exception as e:
            logger.error(f"Error synchronizing observables for alert {alert.id}: {str(e)}")
            return error_response(
                message=f"Error synchronizing observables: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['Alert Management'],
        summary="Trigger SentinelVision pipeline",
        description="Runs a SentinelVision enrichment pipeline on this alert.",
        parameters=[
            OpenApiParameter(name="pipeline", description="Name of the pipeline to run (optional)", required=False, type=str)
        ],
        responses={
            200: OpenApiResponse(description="Pipeline triggered successfully", response=dict),
            500: OpenApiResponse(description="Server error")
        }
    )
    @action(detail=True, methods=['post'], url_path='trigger-pipeline')
    def trigger_pipeline(self, request, pk=None):
        """
        Triggers a SentinelVision pipeline for this alert.
        """
        alert = self.get_object()
        pipeline_name = request.data.get('pipeline')
        
        try:
            # Call the trigger_sentinelvision_pipeline method on the alert
            result = alert.trigger_sentinelvision_pipeline(pipeline_name)
            
            return success_response(
                message="SentinelVision pipeline triggered successfully.",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error triggering SentinelVision pipeline for alert {alert.id}: {str(e)}")
            return error_response(
                message=f"Error triggering pipeline: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 