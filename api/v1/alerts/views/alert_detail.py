import logging
from rest_framework import status
from api.core.responses import success_response, error_response
from alerts.models import Alert
from api.v1.alerts.enums import AlertStatusEnum

logger = logging.getLogger('api.alerts')


class AlertDetailMixin:
    """
    Mixin for alert detail and update operations
    """
    def perform_update(self, serializer):
        """
        Updates an alert with proper logging.
        """
        user = self.request.user
        instance = serializer.save()
        logger.info(f"Alert updated: {instance.title} ({instance.get_status_display()}) by {user.username}")
    
    def perform_destroy(self, instance):
        """
        Removes an alert with proper logging.
        """
        title = instance.title
        severity = instance.get_severity_display()
        status_display = instance.get_status_display()
        user = self.request.user
        
        # Check if the alert has been escalated
        if instance.status == AlertStatusEnum.ESCALATED.value:
            logger.warning(f"Attempt to remove escalated alert: {title} by {user.username}")
            return error_response(
                message="Cannot remove an alert that has been escalated to an incident.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        instance.delete()
        logger.info(f"Alert removed: {title} ({severity}, {status_display}) by {user.username}") 