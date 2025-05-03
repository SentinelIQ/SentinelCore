from rest_framework import status
from rest_framework.decorators import action
from api.core.responses import success_response, error_response
from api.core.rbac import HasEntityPermission
import logging
from drf_spectacular.utils import extend_schema
from observables.services.elastic import ElasticLookupService
from sentinelvision.tasks.enrichment_tasks import enrich_observable
from audit_logs.models import AuditLog

logger = logging.getLogger('api.observables')


class ObservableCustomActionsMixin:
    """
    Mixin for Observable custom actions (mark as IOC, etc).
    """
    @extend_schema(
        summary="Mark observable as IOC",
        description="Mark an observable as an Indicator of Compromise (IOC).",
        responses={200: dict}
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
            
    @extend_schema(
        summary="Reprocess observable",
        description="Reprocess an observable through analyzers",
        responses={200: dict}
    )
    @action(detail=True, methods=['post'], permission_classes=[HasEntityPermission])
    def reprocess(self, request, pk=None):
        """
        Reprocess an observable through all compatible analyzers.
        """
        observable = self.get_object()
        
        # Schedule the enrichment task
        enrich_observable.delay(
            str(observable.id),
            company_id=str(observable.company.id),
            user_id=str(request.user.id)
        )
        
        return success_response(
            message=f"Observable {observable.id} has been queued for reprocessing"
        )
    
    @extend_schema(
        summary="Get observable history",
        description="Get history of changes for an observable",
        responses={200: dict}
    )
    @action(detail=True, methods=['get'], permission_classes=[HasEntityPermission])
    def history(self, request, pk=None):
        """
        Get history of changes for an observable.
        """
        observable = self.get_object()
        
        # Get execution records for this observable
        executions = observable.execution_records.all().order_by('-created_at')[:20]
        
        # Get audit logs for this observable
        audit_logs = AuditLog.objects.filter(
            entity_type='observable',
            entity_id=str(observable.id)
        ).order_by('-timestamp')[:20]
        
        # Combine history entries
        history = []
        
        # Add execution records
        for execution in executions:
            history.append({
                'timestamp': execution.created_at,
                'source': f"{execution.execution_type.capitalize()} Execution",
                'action': f"Executed {execution.module_name}",
                'user': str(execution.executed_by),
                'changes': None
            })
        
        # Add audit logs
        for log in audit_logs:
            history.append({
                'timestamp': log.timestamp,
                'source': 'Audit Log',
                'action': log.action,
                'user': str(log.user) if log.user else None,
                'changes': log.changes
            })
        
        # Sort by timestamp
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Serialize
        return success_response(
            data=history,
            metadata={'total_entries': len(history)}
        )
    
    @extend_schema(
        summary="Search Elasticsearch",
        description="Search for observables in Elasticsearch",
        responses={200: dict}
    )
    @action(detail=False, methods=['get'], permission_classes=[HasEntityPermission])
    def search_elasticsearch(self, request):
        """
        Search for observables in Elasticsearch with tenant isolation.
        
        Query parameters:
        - q: Search query string (required)
        - type: Observable type filter (optional)
        - is_ioc: Filter by IOC status (optional)
        - limit: Maximum number of results (default: 50)
        - days: How many days back to search (default: 90)
        """
        query = request.query_params.get('q')
        observable_type = request.query_params.get('type')
        is_ioc = request.query_params.get('is_ioc')
        limit = int(request.query_params.get('limit', 50))
        days = int(request.query_params.get('days', 90))
        
        if not query:
            return error_response(
                message="Search query parameter 'q' is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize lookup service with company context
        lookup_service = ElasticLookupService(company_id=request.user.company.id)
        
        # Prepare filters
        filters = {}
        if observable_type:
            filters['type'] = observable_type
        if is_ioc is not None:
            filters['is_ioc'] = is_ioc.lower() == 'true'
        
        try:
            # Execute search
            results = lookup_service.search_observables(
                query_string=query,
                limit=limit,
                days=days,
                filters=filters
            )
            
            return success_response(
                data=results.get('results', []),
                metadata={
                    'total': results.get('total', 0),
                    'query': query,
                    'filters': filters
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching Elasticsearch: {str(e)}")
            return error_response(
                message=f"Error searching Elasticsearch: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 