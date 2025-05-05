from rest_framework import status
from rest_framework.decorators import action
from api.core.responses import success_response, error_response
from api.core.rbac import HasEntityPermission
import logging
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
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
        description=(
            "Mark an observable as an Indicator of Compromise (IOC). This action flags the "
            "observable as malicious or suspicious for tracking purposes and enables special "
            "handling in the system. IOCs are key elements in threat intelligence and security "
            "operations, allowing analysts to track and correlate malicious indicators across incidents."
        ),
        responses={
            200: OpenApiResponse(
                description="Operation successful",
                examples=[
                    OpenApiExample(
                        name="success_marked",
                        summary="Successfully marked as IOC",
                        description="The observable was successfully marked as an IOC",
                        value={
                            "status": "success",
                            "message": "Observable successfully marked as an IOC",
                            "data": {
                                "observable_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "is_ioc": True
                            }
                        }
                    ),
                    OpenApiExample(
                        name="already_ioc",
                        summary="Already marked as IOC",
                        description="The observable was already marked as an IOC",
                        value={
                            "status": "success",
                            "message": "Observable is already marked as an IOC",
                            "data": {
                                "observable_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "is_ioc": True
                            }
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Server error",
                examples=[
                    OpenApiExample(
                        name="server_error",
                        summary="Internal server error",
                        description="An error occurred while marking as IOC",
                        value={
                            "status": "error",
                            "message": "Error marking observable as IOC: Database error",
                            "code": 500
                        }
                    )
                ]
            )
        }
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
        summary="Reprocess observable through enrichment",
        description=(
            "Reprocess an observable through all compatible analyzer modules in SentinelVision. "
            "This endpoint triggers threat intelligence enrichment for the observable, checking "
            "various threat feeds, reputation services, and analysis engines. The processing occurs "
            "asynchronously via Celery tasks, and results will be stored in the observable's enrichment_data. "
            "This is useful when new analyzers are added or when you need fresh intelligence on an indicator."
        ),
        responses={
            200: OpenApiResponse(
                description="Enrichment queued successfully",
                examples=[
                    OpenApiExample(
                        name="success_queued",
                        summary="Successfully queued for enrichment",
                        description="The observable was successfully queued for enrichment",
                        value={
                            "status": "success",
                            "message": "Observable 3fa85f64-5717-4562-b3fc-2c963f66afa6 has been queued for reprocessing"
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="User lacks permission",
                        description="The user doesn't have permission to reprocess observables",
                        value={
                            "status": "error",
                            "message": "You do not have permission to perform this action.",
                            "code": 403
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Server error",
                examples=[
                    OpenApiExample(
                        name="task_error",
                        summary="Task scheduling error",
                        description="An error occurred while scheduling the enrichment task",
                        value={
                            "status": "error",
                            "message": "Error scheduling enrichment task: Celery broker unavailable",
                            "code": 500
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[HasEntityPermission])
    def reprocess(self, request, pk=None):
        """
        Reprocess an observable through all compatible analyzers.
        """
        observable = self.get_object()
        
        try:
            # Schedule the enrichment task
            enrich_observable.delay(
                str(observable.id),
                company_id=str(observable.company.id),
                user_id=str(request.user.id)
            )
            
            logger.info(f"Observable {observable.id} ({observable.type}: {observable.value}) queued for reprocessing by {request.user.username}")
            
            return success_response(
                message=f"Observable {observable.id} has been queued for reprocessing"
            )
        except Exception as e:
            logger.error(f"Error scheduling enrichment for observable {observable.id}: {str(e)}")
            return error_response(
                message=f"Error scheduling enrichment task: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get observable history",
        description=(
            "Retrieves the complete history of an observable, including enrichment executions and "
            "audit logs. This endpoint provides a comprehensive audit trail for security investigations, "
            "showing all actions, enrichments, and modifications performed on the observable over time. "
            "The history is sorted chronologically with the most recent events first, providing visibility "
            "into the observable's lifecycle and intelligence gathering process."
        ),
        responses={
            200: OpenApiResponse(
                description="Observable history retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="history_response",
                        summary="History with enrichment and audit events",
                        description="Combined history of enrichment executions and audit logs",
                        value={
                            "status": "success",
                            "message": "Retrieved observable history",
                            "data": [
                                {
                                    "timestamp": "2023-07-15T14:22:18.456789Z",
                                    "source": "Analyzer Execution",
                                    "action": "Executed VirusTotal",
                                    "user": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                                    "changes": None
                                },
                                {
                                    "timestamp": "2023-07-15T14:20:05.123456Z",
                                    "source": "Audit Log",
                                    "action": "mark_as_ioc",
                                    "user": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                                    "changes": {
                                        "is_ioc": {
                                            "old": False,
                                            "new": True
                                        }
                                    }
                                },
                                {
                                    "timestamp": "2023-07-15T13:45:32.654321Z",
                                    "source": "Audit Log",
                                    "action": "create",
                                    "user": "5fa85f64-5717-4562-b3fc-2c963f66def9",
                                    "changes": None
                                }
                            ],
                            "metadata": {
                                "total_entries": 3
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="User lacks permission",
                        description="The user doesn't have permission to view this observable's history",
                        value={
                            "status": "error",
                            "message": "You do not have permission to perform this action.",
                            "code": 403
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Server error",
                examples=[
                    OpenApiExample(
                        name="server_error",
                        summary="Internal server error",
                        description="An error occurred while retrieving history",
                        value={
                            "status": "error",
                            "message": "Error retrieving observable history: Database error",
                            "code": 500
                        }
                    )
                ]
            )
        }
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
        summary="Search Elasticsearch for observables",
        description=(
            "Provides powerful multi-criteria search capabilities for security observables using Elasticsearch. "
            "This endpoint enables security analysts to quickly search for indicators across the entire "
            "platform with tenant isolation ensuring data segregation. Results include observables with "
            "their metadata, tags, and enrichment information. This is particularly useful for threat hunting, "
            "incident correlation, and discovering related observables during an investigation."
        ),
        parameters=[
            OpenApiParameter(
                name="q", 
                description="Search query string (required) - supports Elasticsearch query syntax",
                required=True, 
                type=str,
                examples=[
                    OpenApiExample(
                        name="ip_search",
                        summary="Search for IP",
                        value="192.168.1.100"
                    ),
                    OpenApiExample(
                        name="domain_search",
                        summary="Search for domain",
                        value="malicious-domain.com"
                    ),
                    OpenApiExample(
                        name="hash_search",
                        summary="Search for file hash",
                        value="44d88612fea8a8f36de82e1278abb02f"
                    )
                ]
            ),
            OpenApiParameter(
                name="type", 
                description="Observable type filter",
                required=False, 
                type=str,
                examples=[
                    OpenApiExample(
                        name="ip_type",
                        summary="IP type filter",
                        value="ip"
                    ),
                    OpenApiExample(
                        name="domain_type",
                        summary="Domain type filter",
                        value="domain"
                    ),
                    OpenApiExample(
                        name="file_hash_type",
                        summary="File hash type filter",
                        value="file_hash"
                    ),
                    OpenApiExample(
                        name="email_type",
                        summary="Email type filter",
                        value="email"
                    )
                ]
            ),
            OpenApiParameter(
                name="is_ioc", 
                description="Filter by IOC status",
                required=False, 
                type=bool,
                examples=[
                    OpenApiExample(
                        name="ioc_true",
                        summary="Only IOCs",
                        value="true"
                    ),
                    OpenApiExample(
                        name="ioc_false",
                        summary="Non-IOCs",
                        value="false"
                    )
                ]
            ),
            OpenApiParameter(
                name="limit", 
                description="Maximum number of results (default: 50)",
                required=False, 
                type=int,
                examples=[
                    OpenApiExample(
                        name="limit_10",
                        summary="Small result set",
                        value="10"
                    ),
                    OpenApiExample(
                        name="limit_50",
                        summary="Default result set",
                        value="50"
                    ),
                    OpenApiExample(
                        name="limit_100",
                        summary="Large result set",
                        value="100"
                    )
                ]
            ),
            OpenApiParameter(
                name="days", 
                description="How many days back to search (default: 90)",
                required=False, 
                type=int,
                examples=[
                    OpenApiExample(
                        name="days_30",
                        summary="Last month",
                        value="30"
                    ),
                    OpenApiExample(
                        name="days_90",
                        summary="Last quarter",
                        value="90"
                    ),
                    OpenApiExample(
                        name="days_365",
                        summary="Last year",
                        value="365"
                    )
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Search results returned successfully",
                examples=[
                    OpenApiExample(
                        name="search_results",
                        summary="Successful search response",
                        description="Results for an IP address search",
                        value={
                            "status": "success",
                            "message": "Search results",
                            "data": [
                                {
                                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                    "type": "ip",
                                    "value": "192.168.1.100",
                                    "is_ioc": True,
                                    "tags": ["lateral-movement", "internal"],
                                    "first_seen": "2023-07-10T15:38:12.456Z",
                                    "last_seen": "2023-07-15T09:12:45.789Z",
                                    "enrichment": {
                                        "source": "VirusTotal",
                                        "malicious": 4,
                                        "suspicious": 2,
                                        "harmless": 60
                                    },
                                    "related_incidents": 2,
                                    "related_alerts": 3
                                },
                                {
                                    "id": "4fa85f64-5717-4562-b3fc-2c963f66afb7",
                                    "type": "ip",
                                    "value": "192.168.1.101",
                                    "is_ioc": False,
                                    "tags": ["internal"],
                                    "first_seen": "2023-07-12T10:24:36.123Z",
                                    "last_seen": "2023-07-14T08:45:22.567Z",
                                    "enrichment": {},
                                    "related_incidents": 1,
                                    "related_alerts": 1
                                }
                            ],
                            "metadata": {
                                "total": 2,
                                "query": "192.168.1",
                                "filters": {
                                    "type": "ip"
                                }
                            }
                        }
                    ),
                    OpenApiExample(
                        name="empty_results",
                        summary="Empty search results",
                        description="No results found for the search query",
                        value={
                            "status": "success",
                            "message": "Search results",
                            "data": [],
                            "metadata": {
                                "total": 0,
                                "query": "nonexistent-domain.com",
                                "filters": {}
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid search parameters",
                examples=[
                    OpenApiExample(
                        name="missing_query",
                        summary="Missing query parameter",
                        description="The required 'q' parameter is missing",
                        value={
                            "status": "error",
                            "message": "Search query parameter 'q' is required",
                            "code": 400
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        name="permission_denied",
                        summary="Permission error",
                        description="User doesn't have permission to search",
                        value={
                            "status": "error",
                            "message": "You do not have permission to perform this action.",
                            "code": 403
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Search error",
                examples=[
                    OpenApiExample(
                        name="elasticsearch_error",
                        summary="Elasticsearch error",
                        description="Error while performing Elasticsearch search",
                        value={
                            "status": "error",
                            "message": "Error searching Elasticsearch: Connection refused",
                            "code": 500
                        }
                    )
                ]
            )
        }
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