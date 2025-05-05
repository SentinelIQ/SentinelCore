import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from api.core.responses import success_response, error_response
from ..permissions import CanViewDashboard
from ..models import DashboardPreference
from ..serializers import DashboardPreferenceSerializer

logger = logging.getLogger('api.dashboard')


class DashboardPreferenceView(APIView):
    """
    Manage dashboard preferences for the current user.
    """
    permission_classes = [IsAuthenticated, CanViewDashboard]
    
    @extend_schema(
        tags=['System Monitoring & Operations'],
        summary="Retrieve user dashboard preferences",
        description=(
            "Retrieves personalized dashboard configuration settings for the current user. "
            "This endpoint provides access to the user's saved dashboard layout, widget arrangements, "
            "default time range, and other customization settings. If no preferences exist for the "
            "current user, default settings will be automatically created. This endpoint enables "
            "persistent dashboard customization across user sessions and devices."
        ),
        responses={
            200: OpenApiResponse(
                response=DashboardPreferenceSerializer,
                description="Dashboard preferences retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="default_preferences",
                        summary="Default dashboard preferences",
                        description="Example of default dashboard preferences for a new user",
                        value={
                            "status": "success",
                            "message": "Dashboard preferences retrieved successfully",
                            "data": {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "user": {
                                    "id": "7c4f1223-9542-4168-b2d3-3d38a3810e91",
                                    "username": "analyst1",
                                    "email": "analyst1@example.com"
                                },
                                "default_time_range": 30,
                                "layout": {
                                    "alerts_widget": {"x": 0, "y": 0, "w": 6, "h": 4},
                                    "incidents_widget": {"x": 6, "y": 0, "w": 6, "h": 4},
                                    "tasks_widget": {"x": 0, "y": 4, "w": 12, "h": 4}
                                },
                                "widget_preferences": {
                                    "alerts_widget": {"visible": true, "chart_type": "pie"},
                                    "incidents_widget": {"visible": true, "chart_type": "bar"},
                                    "tasks_widget": {"visible": true, "chart_type": "line"}
                                },
                                "created_at": "2023-05-15T10:30:45Z",
                                "updated_at": "2023-05-15T10:30:45Z"
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
                        description="Example of server error during preference retrieval",
                        value={
                            "status": "error",
                            "message": "Error retrieving dashboard preferences: Database timeout"
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        """
        Get dashboard preferences for the current user.
        
        Creates default preferences if none exist.
        """
        try:
            # Get or create preferences for the current user
            preferences, created = DashboardPreference.objects.get_or_create(
                user=request.user,
                company=request.user.company,
                defaults={
                    'default_time_range': 30,
                    'layout': {},
                    'widget_preferences': {}
                }
            )
            
            serializer = DashboardPreferenceSerializer(preferences)
            
            return success_response(
                data=serializer.data,
                message="Dashboard preferences retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving dashboard preferences: {str(e)}")
            return error_response(
                message=f"Error retrieving dashboard preferences: {str(e)}"
            )
    
    @extend_schema(
        tags=['System Monitoring & Operations'],
        summary="Update user dashboard preferences",
        description=(
            "Updates personalized dashboard configuration settings for the current user. "
            "This endpoint allows users to save changes to their dashboard layout, widget visibility, "
            "chart types, and default time ranges. The customization data will persist across user "
            "sessions and devices. If no preferences exist for the current user, default settings will "
            "be created and then updated with the provided values. This endpoint supports partial updates, "
            "allowing users to modify specific aspects of their dashboard preferences without affecting "
            "other settings."
        ),
        request=DashboardPreferenceSerializer,
        responses={
            200: OpenApiResponse(
                response=DashboardPreferenceSerializer,
                description="Dashboard preferences updated successfully",
                examples=[
                    OpenApiExample(
                        name="updated_preferences",
                        summary="Updated dashboard preferences",
                        description="Example of successfully updated dashboard preferences",
                        value={
                            "status": "success",
                            "message": "Dashboard preferences updated successfully",
                            "data": {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "user": {
                                    "id": "7c4f1223-9542-4168-b2d3-3d38a3810e91",
                                    "username": "analyst1",
                                    "email": "analyst1@example.com"
                                },
                                "default_time_range": 14,
                                "layout": {
                                    "alerts_widget": {"x": 0, "y": 0, "w": 12, "h": 4},
                                    "incidents_widget": {"x": 0, "y": 4, "w": 6, "h": 4},
                                    "tasks_widget": {"x": 6, "y": 4, "w": 6, "h": 4},
                                    "mitre_widget": {"x": 0, "y": 8, "w": 12, "h": 4}
                                },
                                "widget_preferences": {
                                    "alerts_widget": {"visible": true, "chart_type": "bar"},
                                    "incidents_widget": {"visible": true, "chart_type": "line"},
                                    "tasks_widget": {"visible": true, "chart_type": "pie"},
                                    "mitre_widget": {"visible": true, "chart_type": "heatmap"}
                                },
                                "created_at": "2023-05-15T10:30:45Z",
                                "updated_at": "2023-05-16T14:22:18Z"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid input data",
                examples=[
                    OpenApiExample(
                        name="invalid_data",
                        summary="Invalid preference data",
                        description="Example of error when submitted preferences data is invalid",
                        value={
                            "status": "error",
                            "message": "Invalid data for dashboard preferences",
                            "errors": {
                                "default_time_range": ["Ensure this value is less than or equal to 365."],
                                "layout": ["Layout configuration must be a valid JSON object."]
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
                        description="Example of error when user lacks dashboard access permissions",
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
                        description="Example of server error during preference update",
                        value={
                            "status": "error",
                            "message": "Error updating dashboard preferences: Database timeout"
                        }
                    )
                ]
            )
        }
    )
    def put(self, request):
        """
        Update dashboard preferences for the current user.
        
        Creates preferences if none exist.
        """
        try:
            # Get or create preferences for the current user
            preferences, created = DashboardPreference.objects.get_or_create(
                user=request.user,
                company=request.user.company,
                defaults={
                    'default_time_range': 30,
                    'layout': {},
                    'widget_preferences': {}
                }
            )
            
            # Update with new data
            serializer = DashboardPreferenceSerializer(
                preferences, 
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return success_response(
                    data=serializer.data,
                    message="Dashboard preferences updated successfully"
                )
            else:
                return error_response(
                    message="Invalid data for dashboard preferences",
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error updating dashboard preferences: {str(e)}")
            return error_response(
                message=f"Error updating dashboard preferences: {str(e)}"
            ) 