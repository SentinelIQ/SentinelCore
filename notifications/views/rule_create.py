from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework import status

from api.core.responses import success_response, error_response
from api.core.utils import get_tenant_from_request
from notifications.models import NotificationRule
from notifications.permissions import ManageNotificationsPermission
from notifications.serializers import NotificationRuleSerializer

import logging

logger = logging.getLogger('api.notifications')

class NotificationRuleCreateView(CreateAPIView):
    """
    Create a new notification rule.
    """
    permission_classes = [IsAuthenticated, ManageNotificationsPermission]
    serializer_class = NotificationRuleSerializer
    
    @extend_schema(
        tags=['Notification System'],
        summary="Create notification rule",
        description="Create a new notification rule for triggering notifications on system events.",
        request=NotificationRuleSerializer,
        responses={201: NotificationRuleSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new notification rule.
        """
        return self.create(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """
        Custom create to handle tenant and creator assignment.
        """
        try:
            tenant = get_tenant_from_request(request)
            
            # Add tenant to the data
            data = request.data.copy()
            data['company'] = tenant.id
            data['created_by'] = request.user.id
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return success_response(
                data=serializer.data,
                message="Notification rule created successfully",
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error creating notification rule: {str(e)}")
            return error_response(
                message=f"Error creating notification rule: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def perform_create(self, serializer):
        """
        Save the rule and ensure proper tenant and creator assignment.
        """
        serializer.save() 