import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
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
        responses={200: DashboardPreferenceSerializer}
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
        request=DashboardPreferenceSerializer,
        responses={200: DashboardPreferenceSerializer}
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