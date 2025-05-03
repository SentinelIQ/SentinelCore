from rest_framework.mixins import RetrieveModelMixin
from drf_spectacular.utils import extend_schema
from notifications.models import UserNotificationPreference
from notifications.serializers import UserNotificationPreferenceSerializer
from notifications.permissions import ManageNotificationPreferencesPermission
from api.core.responses import StandardResponse

class UserNotificationPreferenceDetailView(RetrieveModelMixin):
    """
    View for retrieving user notification preferences.
    Users can view their own preferences, and administrators with
    manage_notifications permission can view any user's preferences
    within their company.
    """
    serializer_class = UserNotificationPreferenceSerializer
    permission_classes = [ManageNotificationPreferencesPermission]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'
    
    @extend_schema(
        tags=['Notifications'],
        summary="Get user notification preferences",
        description="Retrieves notification preferences for a specific user. "
                    "Users can view their own preferences, and administrators with "
                    "manage_notifications permission can view any user's preferences "
                    "within their company.",
        responses={
            200: UserNotificationPreferenceSerializer,
            404: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve notification preferences for a user"""
        return super().retrieve(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get user notification preferences.
        Users can view their own preferences, and administrators with
        manage_notifications permission can view any user's preferences
        within their company.
        """
        user = self.request.user
        user_id = self.kwargs.get('user_id')
        
        # Convert user_id to int if it's a string
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass
        
        # If viewing own preferences
        if user_id == user.id or str(user_id) == str(user.id):
            # Get or create preferences for the user
            prefs, _ = UserNotificationPreference.objects.get_or_create(user=user)
            return UserNotificationPreference.objects.filter(id=prefs.id)
        
        # Administrators can view preferences for users in their company
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