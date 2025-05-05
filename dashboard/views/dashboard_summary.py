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
        tags=['System Monitoring & Operations'],
        operation_id='dashboard_summary',
        summary="Retrieve security operations dashboard summary",
        description=(
            "Provides a comprehensive operational overview of the security posture across the SOAR platform, "
            "essential for security leadership and analyst teams to monitor incident response effectiveness. "
            "This endpoint delivers consolidated metrics about security alerts, incidents, and response activities "
            "with multi-tenant isolation ensuring data segregation between different organizations. "
            "The dashboard data is used to evaluate security team performance, track key metrics such as mean time "
            "to respond (MTTR), alert-to-incident escalation rates, and task completion efficiency. This endpoint "
            "supports informed decision-making for SOC managers and provides visibility into security operations "
            "trends over customizable time periods. The response includes detailed breakdowns by severity levels, "
            "allowing teams to focus on high-priority threats and operational bottlenecks."
        ),
        parameters=[
            OpenApiParameter(
                name='days', 
                type=int, 
                description='Number of days to include in the metrics calculation window', 
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
                        name="Comprehensive Summary",
                        summary="Complete security operations dashboard",
                        description="Example of a comprehensive dashboard with alert, incident, and task metrics",
                        value={
                            "status": "success",
                            "message": "Dashboard summary generated successfully",
                            "data": {
                                "alert_metrics": {
                                    "total": 158,
                                    "open": 47,
                                    "closed": 111,
                                    "by_severity": {"low": 42, "medium": 65, "high": 38, "critical": 13},
                                    "by_source": {
                                        "siem": 84,
                                        "edr": 37,
                                        "firewall": 21,
                                        "manual": 16
                                    },
                                    "trend": {
                                        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                                        "data": [42, 36, 45, 35]
                                    }
                                },
                                "incident_metrics": {
                                    "total": 25,
                                    "open": 8,
                                    "closed": 17,
                                    "mttr_hours": 8.4,
                                    "mtta_hours": 2.1,
                                    "by_severity": {"low": 6, "medium": 10, "high": 7, "critical": 2},
                                    "by_category": {
                                        "malware": 9,
                                        "phishing": 6,
                                        "data_breach": 3,
                                        "ransomware": 1,
                                        "other": 6
                                    },
                                    "trend": {
                                        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                                        "data": [7, 5, 8, 5]
                                    }
                                },
                                "task_metrics": {
                                    "total": 78,
                                    "completed": 62,
                                    "pending": 16,
                                    "overdue": 8,
                                    "completion_rate": 79.5,
                                    "avg_completion_time_hours": 6.2,
                                    "by_priority": {
                                        "low": {"total": 24, "completed": 22},
                                        "medium": {"total": 32, "completed": 25},
                                        "high": {"total": 22, "completed": 15}
                                    }
                                },
                                "analyst_metrics": {
                                    "total_analysts": 12,
                                    "active_analysts": 8,
                                    "avg_incidents_per_analyst": 3.1,
                                    "avg_tasks_per_analyst": 6.5
                                },
                                "mitre_coverage": {
                                    "top_techniques": [
                                        {"id": "T1566", "name": "Phishing", "count": 18},
                                        {"id": "T1078", "name": "Valid Accounts", "count": 12},
                                        {"id": "T1486", "name": "Data Encrypted for Impact", "count": 9}
                                    ],
                                    "coverage_percentage": 67.8
                                },
                                "period_days": 30,
                                "last_updated": "2023-05-15T08:30:15Z"
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
                        summary="Invalid days parameter",
                        description="Example of response when days parameter is invalid",
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
            403: OpenApiResponse(
                description="Permission denied",
                response=dict,
                examples=[
                    OpenApiExample(
                        name="Permission Denied",
                        summary="User lacks dashboard access permission",
                        description="Example response when user doesn't have dashboard viewing permission",
                        value={
                            "status": "error",
                            "message": "You do not have permission to view the dashboard",
                            "data": null
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
                        summary="Dashboard generation failure",
                        description="Example of response when dashboard calculation fails",
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