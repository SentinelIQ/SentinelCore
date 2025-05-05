import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from api.core.responses import success_response, error_response
from ..permissions import CanViewDashboard
from ..utils import get_incident_metrics, calculate_date_range
from ..serializers import DateRangeFilterSerializer

logger = logging.getLogger('api.dashboard')


class IncidentTrendsView(APIView):
    """
    Get incident trends and metrics.
    """
    permission_classes = [IsAuthenticated, CanViewDashboard]
    
    @extend_schema(
        tags=['System Monitoring & Operations'],
        summary="Get incident trend analytics",
        description=(
            "Provides time-series analytics on security incidents for trend analysis and performance monitoring. "
            "This endpoint delivers visualization data tracking incident volume, resolution times, and escalation patterns "
            "over time. Security operations managers rely on this data to identify operational trends, measure effectiveness "
            "of incident response processes, and optimize security team performance. The metrics include incident status "
            "distribution, MTTR (Mean Time to Resolution), escalation rates, and temporal pattern analysis. This endpoint "
            "supports configurable time range filtering essential for both real-time operational awareness and long-term "
            "security planning."
        ),
        parameters=[
            OpenApiParameter(name='start_date', type=str, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=str, description='End date (YYYY-MM-DD)'),
            OpenApiParameter(name='days', type=int, description='Number of days to include, used if dates not provided')
        ],
        responses={
            200: OpenApiResponse(
                description="Incident trends retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="incident_trends",
                        summary="Incident trend metrics",
                        description="Example of incident trend data showing status, MTTR, and temporal patterns",
                        value={
                            "status": "success",
                            "message": "Incident trends retrieved successfully",
                            "data": {
                                "total": 25,
                                "open": 8,
                                "in_progress": 5,
                                "closed": 12,
                                "mttr_hours": 8.4,
                                "mtta_hours": 2.1,
                                "escalation_rate": 32.5,
                                "by_severity": {
                                    "low": 6,
                                    "medium": 10,
                                    "high": 7,
                                    "critical": 2
                                },
                                "by_category": {
                                    "malware": 9,
                                    "phishing": 6,
                                    "data_breach": 3,
                                    "ransomware": 1,
                                    "other": 6
                                },
                                "trend": {
                                    "dates": ["2023-05-01", "2023-05-08", "2023-05-15", "2023-05-22", "2023-05-29"],
                                    "created": [4, 6, 8, 5, 2],
                                    "closed": [3, 5, 7, 4, 3],
                                    "mttr_by_week": [9.2, 8.5, 7.9, 8.3, 8.1]
                                },
                                "period": {
                                    "start_date": "2023-05-01",
                                    "end_date": "2023-05-31",
                                    "days": 30
                                }
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid input parameters",
                examples=[
                    OpenApiExample(
                        name="invalid_parameters",
                        summary="Invalid date parameters",
                        description="Example of error when date parameters are invalid",
                        value={
                            "status": "error",
                            "message": "Invalid filter parameters",
                            "errors": {
                                "start_date": ["Enter a valid date in YYYY-MM-DD format."],
                                "days": ["Ensure this value is less than or equal to 365."]
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
                        summary="Access permission denied",
                        description="Example of error when user lacks dashboard viewing permissions",
                        value={
                            "status": "error",
                            "message": "You do not have permission to view the dashboard",
                            "data": None
                        }
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Server error",
                examples=[
                    OpenApiExample(
                        name="server_error",
                        summary="Server processing error",
                        description="Example of server error during trends retrieval",
                        value={
                            "status": "error",
                            "message": "Error retrieving incident trends: Database timeout"
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        """
        Get incident trends and metrics over time.
        
        Includes:
        - Incidents by status (open, in progress, closed)
        - Mean Time to Resolve (MTTR)
        - Incident creation trend over time
        - Escalation rate
        
        Can be filtered by a date range.
        """
        try:
            # Validate filters
            serializer = DateRangeFilterSerializer(data=request.query_params)
            if not serializer.is_valid():
                return error_response(
                    message="Invalid filter parameters", 
                    errors=serializer.errors
                )
            
            # Get filter parameters
            days = serializer.validated_data.get('days', 30)
            start_date = serializer.validated_data.get('start_date')
            end_date = serializer.validated_data.get('end_date')
            
            # If dates not provided, calculate from days
            if not start_date or not end_date:
                start_date, end_date = calculate_date_range(days)
            
            # Get company for the current user
            company = request.user.company
            
            # Get metrics
            metrics = get_incident_metrics(company, start_date, end_date, days)
            
            return success_response(
                data=metrics,
                message="Incident trends retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving incident trends: {str(e)}")
            return error_response(
                message=f"Error retrieving incident trends: {str(e)}"
            ) 