from .observable_detail import ObservableDetailViewMixin
from .observable_create import ObservableCreateViewMixin
from .observable_custom_actions import ObservableCustomActionsMixin
from rest_framework import viewsets
from api.core.viewsets import StandardViewSet
from api.core.audit import AuditLogMixin
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from rest_framework import filters, status
from django_filters.rest_framework import DjangoFilterBackend
from observables.models import Observable
from api.core.pagination import StandardResultsSetPagination
from api.core.rbac import HasEntityPermission
from api.core.responses import success_response, error_response
import logging
from django.db import IntegrityError, transaction
from ..serializers import ObservableSerializer
from ..filters import ObservableFilter
from rest_framework.decorators import action

logger = logging.getLogger('api.observables')


@extend_schema_view(
    list=extend_schema(
        summary="List all observables",
        description="Get a paginated list of all observables for the current user's company.",
        responses={
            200: OpenApiResponse(
                description="Success",
                examples=[
                    OpenApiExample(
                        name="success_response",
                        summary="Successful observables list",
                        description="Example paginated list of observables",
                        value={
                            "status": "success",
                            "message": "Data retrieved successfully",
                            "data": [
                                {
                                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                    "type": "ip",
                                    "value": "192.168.1.100",
                                    "is_ioc": True,
                                    "tags": ["lateral-movement", "internal"],
                                    "created_at": "2023-07-10T15:38:12.456Z",
                                    "updated_at": "2023-07-15T09:12:45.789Z"
                                },
                                {
                                    "id": "4fa85f64-5717-4562-b3fc-2c963f66afb7",
                                    "type": "domain",
                                    "value": "malicious-domain.com",
                                    "is_ioc": True,
                                    "tags": ["c2", "malware"],
                                    "created_at": "2023-07-12T10:24:36.123Z",
                                    "updated_at": "2023-07-14T08:45:22.567Z"
                                }
                            ],
                            "metadata": {
                                "pagination": {
                                    "count": 2,
                                    "page": 1,
                                    "pages": 1,
                                    "page_size": 50,
                                    "next": None,
                                    "previous": None
                                }
                            }
                        }
                    )
                ]
            )
        }
    ),
    retrieve=extend_schema(
        summary="Get observable detail",
        description="Retrieve detailed information about a specific observable.",
        responses={
            200: OpenApiResponse(
                description="Success",
                examples=[
                    OpenApiExample(
                        name="success_response",
                        summary="Successful observable detail",
                        description="Example detailed observable information",
                        value={
                            "status": "success",
                            "message": "Data retrieved successfully",
                            "data": {
                                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "type": "ip",
                                "value": "192.168.1.100",
                                "is_ioc": True,
                                "description": "Internal IP address involved in lateral movement",
                                "tags": ["lateral-movement", "internal"],
                                "tlp": 2,
                                "pap": 2,
                                "created_by": {
                                    "id": "1fa85f64-5717-4562-b3fc-2c963f66aaa1",
                                    "username": "analyst1"
                                },
                                "company": {
                                    "id": "5fa85f64-5717-4562-b3fc-2c963f66ccc5",
                                    "name": "Example Company" 
                                },
                                "created_at": "2023-07-10T15:38:12.456Z",
                                "updated_at": "2023-07-15T09:12:45.789Z",
                                "enrichment_data": {
                                    "geolocation": {
                                        "country": "United States",
                                        "city": "San Francisco",
                                        "timezone": "America/Los_Angeles"
                                    },
                                    "reputation": {
                                        "source": "VirusTotal",
                                        "score": 0,
                                        "malicious": 0,
                                        "suspicious": 0,
                                        "harmless": 68
                                    }
                                },
                                "related_alerts_count": 2,
                                "related_incidents_count": 1
                            }
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Observable not found",
                examples=[
                    OpenApiExample(
                        name="not_found",
                        summary="Observable not found",
                        description="Example response when the observable doesn't exist",
                        value={
                            "status": "error",
                            "message": "Observable not found",
                            "code": 404
                        }
                    )
                ]
            )
        }
    ),
    create=extend_schema(
        summary="Create a new observable",
        description="Create a new observable with the provided data. Automatically handles duplicates.",
        responses={
            201: OpenApiResponse(
                description="Observable created successfully",
                examples=[
                    OpenApiExample(
                        name="success_created",
                        summary="Successfully created",
                        description="Example response when the observable is created successfully",
                        value={
                            "status": "success",
                            "message": "Observable created successfully",
                            "data": {
                                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "type": "ip",
                                "value": "192.168.1.100",
                                "is_ioc": False,
                                "description": "Internal IP address",
                                "tags": ["internal"],
                                "tlp": 2,
                                "pap": 2,
                                "created_at": "2023-07-10T15:38:12.456Z",
                                "updated_at": "2023-07-10T15:38:12.456Z"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid request data",
                examples=[
                    OpenApiExample(
                        name="validation_error",
                        summary="Validation error",
                        description="Example response when the request data is invalid",
                        value={
                            "status": "error",
                            "message": "Invalid request data",
                            "errors": {
                                "value": ["This field is required."],
                                "type": ["Invalid observable type. Choose from ip, domain, url, file_hash, email."]
                            },
                            "code": 400
                        }
                    )
                ]
            )
        }
    ),
    update=extend_schema(
        summary="Update an observable",
        description="Update all fields of an existing observable."
    ),
    partial_update=extend_schema(
        summary="Partially update an observable",
        description="Update specific fields of an existing observable."
    ),
    destroy=extend_schema(
        summary="Delete an observable",
        description="Permanently delete an observable."
    )
)
@extend_schema(tags=['Observables & IOCs'])
class ObservableViewSet(
    AuditLogMixin,
    ObservableDetailViewMixin,
    ObservableCreateViewMixin,
    ObservableCustomActionsMixin,
    StandardViewSet
):
    """
    API endpoint for observable management.
    
    Observables represent security artifacts and indicators of compromise (IOCs).
    Each observable belongs to a specific company and can be linked to alerts and incidents.
    Examples include IP addresses, domains, file hashes, and more.
    """
    serializer_class = ObservableSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [HasEntityPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['value', 'description', 'type']
    ordering_fields = ['created_at', 'updated_at', 'type', 'is_ioc']
    ordering = ['-created_at']
    filterset_class = ObservableFilter
    entity_type = 'observable'  # Define entity type for RBAC and audit logging
    
    # Success messages for standardized responses
    success_message_create = "Observable created successfully"
    success_message_update = "Observable updated successfully"
    success_message_delete = "Observable deleted successfully"
    
    def get_additional_log_data(self, request, obj=None, action=None):
        """
        Customize audit log data for observables.
        
        Add observable-specific fields to the audit log, such as type,
        value, and whether it's an IoC.
        
        Args:
            request: The HTTP request
            obj: The observable object being acted upon
            action: The action being performed (create, update, delete)
            
        Returns:
            dict: Additional data for the audit log
        """
        # Get standard log data from parent class
        data = super().get_additional_log_data(request, obj, action)
        
        # Add observable-specific data
        if obj:
            data.update({
                'observable_type': getattr(obj, 'type', None),
                'observable_value': getattr(obj, 'value', None),
                'is_ioc': getattr(obj, 'is_ioc', False),
                'company_id': str(obj.company.id) if getattr(obj, 'company', None) else None,
                'company_name': obj.company.name if getattr(obj, 'company', None) else None,
            })
            
        return data
    
    def get_queryset(self):
        """
        Returns only observables from the user's company, unless the user is a superuser.
        """
        user = self.request.user
        
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for OpenAPI schema generation
            return Observable.objects.none()
        
        if user.is_superuser:
            return Observable.objects.all()
        
        return Observable.objects.filter(company=user.company)
    
    def perform_create(self, serializer):
        """
        Creates an observable, automatically assigning the user and company.
        Handles duplicate entries gracefully.
        """
        user = self.request.user
        
        # First check if a duplicate exists
        try:
            existing = Observable.objects.get(
                type=serializer.validated_data['type'],
                value=serializer.validated_data['value'],
                company=user.company
            )
            # If we found a duplicate without error, return it
            logger.warning(f"Duplicate observable found: {existing.type}:{existing.value}")
            return existing
        except Observable.DoesNotExist:
            # If no duplicate exists, create a new observable
            try:
                obs = serializer.save(created_by=user, company=user.company)
                logger.info(f"Observable created: {obs.type}:{obs.value} by {user.username}")
                return obs
            except IntegrityError as e:
                # If there's a race condition and another duplicate was created
                logger.error(f"Error creating observable: {str(e)}")
                raise
    
    @extend_schema(
        summary="Mark observable as IOC",
        description="Mark an observable as an Indicator of Compromise (IOC).",
        responses={200: ObservableSerializer}
    )
    @action(detail=True, methods=['post'], url_path='mark-as-ioc', permission_classes=[HasEntityPermission])
    def mark_as_ioc(self, request, pk=None):
        """
        Mark an observable as an Indicator of Compromise (IOC).
        """
        observable = self.get_object()
        user = request.user
        
        # Check if already marked as IOC
        if observable.is_ioc:
            return success_response(
                data={"observable_id": observable.id, "is_ioc": True},
                message="Observable is already marked as an IOC",
            )
        
        try:
            observable.is_ioc = True
            # Only save ioc flag and updated_at
            observable.save(update_fields=['is_ioc', 'updated_at'])
            
            logger.info(f"Observable {observable.id} ({observable.type}: {observable.value}) marked as IOC by {user.username}")
            
            return success_response(
                data={"observable_id": observable.id, "is_ioc": True},
                message="Observable successfully marked as an IOC",
            )
        except Exception as e:
            logger.error(f"Error marking observable {observable.id} as IOC: {str(e)}")
            return error_response(
                message=f"Error marking observable as IOC: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


__all__ = [
    'ObservableViewSet',
] 