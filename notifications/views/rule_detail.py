from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404

from api.core.responses import success_response, error_response
from api.core.utils import get_tenant_from_request
from notifications.models import NotificationRule
from notifications.permissions import ManageNotificationsPermission
from notifications.serializers import NotificationRuleSerializer

import logging

logger = logging.getLogger('api.notifications')

class NotificationRuleDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a notification rule.
    """
    permission_classes = [IsAuthenticated, ManageNotificationsPermission]
    serializer_class = NotificationRuleSerializer
    
    @extend_schema(
        tags=['Notification System'],
        summary="Get notification rule details",
        description="Retrieves details of a specific notification rule.",
        responses={200: NotificationRuleSerializer}
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a specific notification rule.
        """
        return self.retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Notification System'],
        summary="Update notification rule",
        description="Update an existing notification rule.",
        request=NotificationRuleSerializer,
        responses={200: NotificationRuleSerializer}
    )
    def put(self, request, *args, **kwargs):
        """
        Update a notification rule completely.
        """
        return self.update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Notification System'],
        summary="Partially update notification rule",
        description="Partially update an existing notification rule.",
        request=NotificationRuleSerializer,
        responses={200: NotificationRuleSerializer}
    )
    def patch(self, request, *args, **kwargs):
        """
        Update a notification rule partially.
        """
        return self.partial_update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Notification System'],
        summary="Delete notification rule",
        description="Delete an existing notification rule.",
        responses={204: None}
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a notification rule.
        """
        return self.destroy(request, *args, **kwargs)
    
    def get_object(self):
        """
        Get the notification rule and check tenant ownership.
        """
        tenant = get_tenant_from_request(self.request)
        rule_id = self.kwargs.get('pk')
        
        return get_object_or_404(
            NotificationRule,
            id=rule_id,
            company=tenant
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Custom retrieve to use standard response format.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return success_response(
                data=serializer.data,
                message="Notification rule retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving notification rule: {str(e)}")
            return error_response(message=f"Error retrieving notification rule: {str(e)}")
    
    def update(self, request, *args, **kwargs):
        """
        Custom update to use standard response format.
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return success_response(
                data=serializer.data,
                message="Notification rule updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error updating notification rule: {str(e)}")
            return error_response(message=f"Error updating notification rule: {str(e)}")
    
    def destroy(self, request, *args, **kwargs):
        """
        Custom destroy to use standard response format.
        """
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            
            return success_response(
                data=None,
                message="Notification rule deleted successfully"
            )
            
        except Exception as e:
            logger.error(f"Error deleting notification rule: {str(e)}")
            return error_response(message=f"Error deleting notification rule: {str(e)}") 