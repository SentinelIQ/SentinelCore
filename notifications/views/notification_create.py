from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from notifications.models import Notification
from notifications.serializers import NotificationCreateSerializer, NotificationSerializer
from notifications.permissions import ManageNotificationsPermission
from api.core.responses import StandardResponse, created_response
from api.core.utils import get_tenant_from_request

class NotificationCreateView(CreateModelMixin):
    """
    View for creating new notifications.
    Only users with manage_notifications permission can create notifications.
    """
    serializer_class = NotificationCreateSerializer
    permission_classes = [ManageNotificationsPermission]
    
    @extend_schema(
        tags=['Notification System'],
        summary="Create a new notification",
        description="Creates a new notification to be sent to users. "
                    "Requires manage_notifications permission. "
                    "The notification can be sent to specific users or company-wide.",
        request=NotificationCreateSerializer,
        responses={
            201: NotificationSerializer,
            400: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}},
            403: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new notification"""
        # Copy the request data
        data = request.data.copy()
        
        # Ensure company is set if not provided
        if 'company' not in data:
            # Try to get from tenant utils, but fallback to user's company
            tenant = get_tenant_from_request(request)
            if tenant:
                data['company'] = tenant.id
            elif request.user and hasattr(request.user, 'company') and request.user.company:
                data['company'] = request.user.company.id
            else:
                # For tests, add a more specific error
                error_msg = "Company ID is required and could not be inferred from tenant or user"
                return Response(
                    {"status": "error", "message": error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        # Print for debugging in tests
        print(f"Creating notification with company ID: {data.get('company')}")
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Save the notification
        notification = serializer.save()
        
        # Return the full notification data
        response_serializer = NotificationSerializer(notification)
        return created_response(data=response_serializer.data) 