import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from api.core.responses import success_response, error_response
from ..permissions import CanViewDashboard
from ..utils import get_alert_metrics, calculate_date_range
from ..serializers import DateRangeFilterSerializer

logger = logging.getLogger('api.dashboard')


class AlertSeverityView(APIView):
    """
    Get alert metrics broken down by severity.
    """
    permission_classes = [IsAuthenticated, CanViewDashboard]
    
    @extend_schema(
        tags=['System Monitoring & Operations'],
        summary="Get alert severity distribution metrics",
        description=(
            "Provides detailed analytics on security alerts categorized by severity levels. "
            "This endpoint delivers critical visualization data for security managers to assess "
            "alert distribution and identify trends in security events. The metrics include "
            "counts for each severity level (low, medium, high, critical), open vs. closed alerts, "
            "and time-series data for trend analysis. All data respects tenant boundaries, ensuring "
            "organizations only see their own alert metrics. This endpoint supports various time range "
            "filtering options to allow for historical analysis and comparison."
        ),
        parameters=[
            OpenApiParameter(name='start_date', type=str, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=str, description='End date (YYYY-MM-DD)'),
            OpenApiParameter(name='days', type=int, description='Number of days to include, used if dates not provided')
        ],
        responses={
            200: OpenApiResponse(
                description="Alert severity metrics retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="severity_metrics",
                        summary="Alert severity distribution",
                        description="Example showing alert distribution by severity with trends",
                        value={
                            "status": "success",
                            "message": "Alert severity metrics retrieved successfully",
                            "data": {
                                "by_severity": {
                                    "low": 42,
                                    "medium": 65,
                                    "high": 38,
                                    "critical": 13
                                },
                                "total": 158,
                                "open": 47,
                                "closed": 111,
                                "trend": {
                                    "dates": ["2023-05-01", "2023-05-02", "2023-05-03", "2023-05-04", "2023-05-05"],
                                    "by_severity": {
                                        "low": [8, 10, 7, 9, 8],
                                        "medium": [12, 14, 13, 15, 11],
                                        "high": [7, 8, 9, 7, 7],
                                        "critical": [2, 3, 2, 3, 3]
                                    },
                                    "total": [29, 35, 31, 34, 29]
                                },
                                "by_source": {
                                    "siem": 84,
                                    "edr": 37,
                                    "firewall": 21,
                                    "manual": 16
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
                        description="Example of server error during metrics retrieval",
                        value={
                            "status": "error",
                            "message": "Error retrieving alert severity metrics: Database timeout"
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        """
        Get alert metrics broken down by severity.
        
        Includes:
        - Alerts by severity (low, medium, high, critical)
        - Total open and closed alerts
        - Alert trend over time
        
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
            metrics = get_alert_metrics(company, start_date, end_date, days)
            
            return success_response(
                data=metrics,
                message="Alert severity metrics retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving alert severity metrics: {str(e)}")
            return error_response(
                message=f"Error retrieving alert severity metrics: {str(e)}"
            ) 