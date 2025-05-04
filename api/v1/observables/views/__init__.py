from .observable_detail import ObservableDetailViewMixin
from .observable_create import ObservableCreateViewMixin
from .observable_custom_actions import ObservableCustomActionsMixin
from rest_framework import viewsets
from api.core.viewsets import StandardViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view
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
        description="Get a paginated list of all observables for the current user's company."
    ),
    retrieve=extend_schema(
        summary="Get observable detail",
        description="Retrieve detailed information about a specific observable."
    ),
    create=extend_schema(
        summary="Create a new observable",
        description="Create a new observable with the provided data. Automatically handles duplicates."
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
    entity_type = 'observable'  # Define entity type for RBAC
    
    # Success messages for standardized responses
    success_message_create = "Observable created successfully"
    success_message_update = "Observable updated successfully"
    success_message_delete = "Observable deleted successfully"
    
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