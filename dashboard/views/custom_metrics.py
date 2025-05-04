import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.core.responses import success_response, error_response
from ..permissions import CanViewDashboard
from ..utils import calculate_date_range, get_alert_metrics, get_incident_metrics, get_task_metrics
from ..serializers import DateRangeFilterSerializer

logger = logging.getLogger('api.dashboard')


class CustomMetricsView(APIView):
    """
    Get custom metrics based on filters.
    """
    permission_classes = [IsAuthenticated, CanViewDashboard]
    
    @extend_schema(
        tags=['System Monitoring & Operations'],
        parameters=[
            OpenApiParameter(name='metric_type', type=str, 
                            description='Type of metric (alerts, incidents, tasks)'),
            OpenApiParameter(name='start_date', type=str, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=str, description='End date (YYYY-MM-DD)'),
            OpenApiParameter(name='days', type=int, description='Number of days to include, used if dates not provided')
        ],
        responses={200: None}  # Use generic response format
    )
    def get(self, request):
        """
        Get custom metrics based on the specified filters.
        
        Use the metric_type parameter to specify which metrics to retrieve:
        - alerts: Alert metrics (by severity, trend)
        - incidents: Incident metrics (by status, MTTR)
        - tasks: Task metrics (completion rate, by priority)
        
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
            
            # Get metric type
            metric_type = request.query_params.get('metric_type', 'alerts')
            if metric_type not in ['alerts', 'incidents', 'tasks']:
                return error_response(
                    message="Invalid metric type. Must be one of: alerts, incidents, tasks",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # If dates not provided, calculate from days
            if not start_date or not end_date:
                start_date, end_date = calculate_date_range(days)
            
            # Get company for the current user
            company = request.user.company
            
            # Get metrics based on type
            if metric_type == 'alerts':
                metrics = get_alert_metrics(company, start_date, end_date, days)
                message = "Alert metrics retrieved successfully"
            elif metric_type == 'incidents':
                metrics = get_incident_metrics(company, start_date, end_date, days)
                message = "Incident metrics retrieved successfully"
            else:  # tasks
                metrics = get_task_metrics(company, start_date, end_date, days)
                message = "Task metrics retrieved successfully"
            
            return success_response(
                data={
                    'metric_type': metric_type,
                    'timeframe': {
                        'start_date': start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date,
                        'end_date': end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else end_date,
                        'days': days
                    },
                    'metrics': metrics
                },
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error retrieving custom metrics: {str(e)}")
            return error_response(
                message=f"Error retrieving custom metrics: {str(e)}"
            ) 