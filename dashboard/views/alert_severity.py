import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
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
        parameters=[
            OpenApiParameter(name='start_date', type=str, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=str, description='End date (YYYY-MM-DD)'),
            OpenApiParameter(name='days', type=int, description='Number of days to include, used if dates not provided')
        ],
        responses={200: None}  # Use generic response format
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