import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from api.core.responses import success_response, error_response
from ..permissions import CanViewDashboard
from ..utils import get_dashboard_summary
from ..serializers import DateRangeFilterSerializer

logger = logging.getLogger('api.dashboard')


class DashboardSummaryView(APIView):
    """
    Get a summary of key metrics for the dashboard.
    """
    permission_classes = [IsAuthenticated, CanViewDashboard]
    
    @extend_schema(
        tags=['Dashboard'],
        operation_id='dashboard_summary',
        description="""
        Get a comprehensive dashboard summary including alerts, incidents, and tasks.
        
        Includes metrics:
        - Total alerts (open/closed)
        - Incidents by status
        - MTTR (Mean Time to Respond)
        - Escalation rate
        - Task completion rate
        
        Can be filtered by time range (days parameter).
        """,
        parameters=[
            OpenApiParameter(
                name='days', 
                type=int, 
                description='Number of days to include in metrics', 
                default=30,
                required=False
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Dashboard summary generated successfully",
                response=dict,
                examples=[
                    OpenApiExample(
                        name="Example Response",
                        value={
                            "status": "success",
                            "message": "Dashboard summary generated successfully",
                            "data": {
                                "alert_metrics": {
                                    "total": 158,
                                    "open": 47,
                                    "closed": 111,
                                    "by_severity": {"low": 42, "medium": 65, "high": 38, "critical": 13}
                                },
                                "incident_metrics": {
                                    "total": 25,
                                    "open": 8,
                                    "closed": 17,
                                    "mttr_hours": 8.4,
                                    "by_severity": {"low": 6, "medium": 10, "high": 7, "critical": 2}
                                },
                                "task_metrics": {
                                    "total": 78,
                                    "completed": 62,
                                    "pending": 16,
                                    "completion_rate": 79.5
                                },
                                "period_days": 30
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid input parameters",
                response=dict,
                examples=[
                    OpenApiExample(
                        name="Invalid Filter Parameters",
                        value={
                            "status": "error",
                            "message": "Invalid filter parameters",
                            "errors": {
                                "days": ["Ensure this value is less than or equal to 365."]
                            }
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Server error",
                response=dict,
                examples=[
                    OpenApiExample(
                        name="Server Error",
                        value={
                            "status": "error",
                            "message": "Error generating dashboard summary: Database timeout"
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        """
        Get a comprehensive dashboard summary including alerts, incidents, and tasks.
        
        Includes metrics:
        - Total alerts (open/closed)
        - Incidents by status
        - MTTR (Mean Time to Respond)
        - Escalation rate
        - Task completion rate
        
        Can be filtered by time range (days parameter).
        """
        try:
            # Validate filters
            serializer = DateRangeFilterSerializer(data=request.query_params)
            if not serializer.is_valid():
                return error_response(
                    message="Invalid filter parameters", 
                    errors=serializer.errors
                )
            
            # Get days parameter (default to 30 if not provided)
            days = serializer.validated_data.get('days', 30)
            
            # Get company for the current user
            company = request.user.company
            
            # Generate summary
            summary_data = get_dashboard_summary(company, days)
            
            return success_response(
                data=summary_data,
                message="Dashboard summary generated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {str(e)}", exc_info=True)
            return error_response(
                message=f"Error generating dashboard summary: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 