from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from notifications.models import UserNotificationPreference
from notifications.serializers import UserNotificationPreferenceSerializer
from notifications.permissions import ManageNotificationPreferencesPermission
from api.core.responses import success_response

class UserNotificationPreferenceUpdateView(UpdateModelMixin):
    """
    View for updating user notification preferences.
    Users can update their own preferences, and administrators with
    manage_notifications permission can update any user's preferences
    within their company.
    """
    serializer_class = UserNotificationPreferenceSerializer
    permission_classes = [ManageNotificationPreferencesPermission]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'
    
    @extend_schema(
        tags=['Notification System'],
        summary="Update user notification preferences",
        description="Updates notification preferences for a specific user. "
                    "Users can update their own preferences, and administrators with "
                    "manage_notifications permission can update any user's preferences "
                    "within their company.",
        request=UserNotificationPreferenceSerializer,
        responses={
            200: UserNotificationPreferenceSerializer,
            400: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}},
            404: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}
        }
    )
    def update(self, request, *args, **kwargs):
        """Update notification preferences for a user"""
        # Get the preference object
        instance = self.get_object()
        
        # Update the preference object
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return the updated preference object
        return success_response(
            data=serializer.data,
            message="Notification preferences updated successfully"
        )
    
    def get_queryset(self):
        """
        Get user notification preferences.
        Users can update their own preferences, and administrators with
        manage_notifications permission can update any user's preferences
        within their company.
        """
        user = self.request.user
        user_id = self.kwargs.get('user_id')
        
        # Convert user_id to int if it's a string
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass
        
        # If updating own preferences
        if user_id == user.id or str(user_id) == str(user.id):
            # Get or create preferences for the user
            prefs, _ = UserNotificationPreference.objects.get_or_create(user=user)
            return UserNotificationPreference.objects.filter(id=prefs.id)
        
        # Administrators can update preferences for users in their company
        from api.core.rbac import has_permission
        if has_permission(user, 'manage_notifications'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                target_user = User.objects.get(id=user_id, company=user.company)
                # Get or create preferences for the target user
                prefs, _ = UserNotificationPreference.objects.get_or_create(user=target_user)
                return UserNotificationPreference.objects.filter(id=prefs.id)
            except User.DoesNotExist:
                return UserNotificationPreference.objects.none()
            
        # Default empty queryset
        return UserNotificationPreference.objects.none() 