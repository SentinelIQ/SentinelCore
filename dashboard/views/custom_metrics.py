import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
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
        summary="Get custom filtered security metrics",
        description=(
            "Provides configurable access to specific security metrics based on metric type and time range. "
            "This endpoint acts as a flexible analytics engine allowing security operations teams to retrieve "
            "targeted data about alerts, incidents, or tasks within customizable date ranges. The response "
            "structure adapts dynamically based on the requested metric type. Organizations can use this endpoint "
            "for focused dashboard widgets, custom reporting, and targeted performance analysis. The data "
            "respects tenant boundaries, ensuring organizations only see metrics related to their environment."
        ),
        parameters=[
            OpenApiParameter(
                name='metric_type', 
                type=str, 
                description='Type of metric to retrieve',
                examples=[
                    OpenApiExample(name="alerts", value="alerts"),
                    OpenApiExample(name="incidents", value="incidents"),
                    OpenApiExample(name="tasks", value="tasks")
                ]
            ),
            OpenApiParameter(name='start_date', type=str, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=str, description='End date (YYYY-MM-DD)'),
            OpenApiParameter(name='days', type=int, description='Number of days to include, used if dates not provided')
        ],
        responses={
            200: OpenApiResponse(
                description="Custom metrics retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="alert_metrics",
                        summary="Alert metrics response",
                        description="Example of alert metrics response",
                        value={
                            "status": "success",
                            "message": "Alert metrics retrieved successfully",
                            "data": {
                                "metric_type": "alerts",
                                "timeframe": {
                                    "start_date": "2023-05-01",
                                    "end_date": "2023-05-31",
                                    "days": 30
                                },
                                "metrics": {
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
                                        "dates": ["2023-05-01", "2023-05-08", "2023-05-15", "2023-05-22", "2023-05-29"],
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
                                    }
                                }
                            }
                        }
                    ),
                    OpenApiExample(
                        name="incident_metrics",
                        summary="Incident metrics response",
                        description="Example of incident metrics response",
                        value={
                            "status": "success",
                            "message": "Incident metrics retrieved successfully",
                            "data": {
                                "metric_type": "incidents",
                                "timeframe": {
                                    "start_date": "2023-05-01",
                                    "end_date": "2023-05-31",
                                    "days": 30
                                },
                                "metrics": {
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
                                    }
                                }
                            }
                        }
                    ),
                    OpenApiExample(
                        name="task_metrics",
                        summary="Task metrics response",
                        description="Example of task metrics response",
                        value={
                            "status": "success",
                            "message": "Task metrics retrieved successfully",
                            "data": {
                                "metric_type": "tasks",
                                "timeframe": {
                                    "start_date": "2023-05-01",
                                    "end_date": "2023-05-31",
                                    "days": 30
                                },
                                "metrics": {
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
                                    },
                                    "trend": {
                                        "dates": ["2023-05-01", "2023-05-08", "2023-05-15", "2023-05-22", "2023-05-29"],
                                        "created": [15, 18, 17, 16, 12],
                                        "completed": [12, 14, 15, 13, 8]
                                    }
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
                        name="invalid_metric_type",
                        summary="Invalid metric type parameter",
                        description="Example of error when an unsupported metric type is requested",
                        value={
                            "status": "error",
                            "message": "Invalid metric type. Must be one of: alerts, incidents, tasks"
                        }
                    ),
                    OpenApiExample(
                        name="invalid_date_parameters",
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
                            "message": "Error retrieving custom metrics: Database timeout"
                        }
                    )
                ]
            )
        }
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