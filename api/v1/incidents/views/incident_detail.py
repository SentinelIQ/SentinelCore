import logging
from rest_framework import status
from rest_framework.response import Response
from incidents.models import Incident
from alerts.models import Alert

logger = logging.getLogger('api.incidents')


class IncidentDetailMixin:
    """
    Mixin for incident detail and update operations
    """
    def perform_update(self, serializer):
        """
        Updates an incident with appropriate logging.
        """
        user = self.request.user
        instance = serializer.save()
        
        # Log the update
        logger.info(f"Incident updated: {instance.title} ({instance.get_status_display()}) by {user.username}")
        
        # Check if alerts were added or removed
        if hasattr(serializer, 'validated_data') and ('add_alert_ids' in serializer.validated_data or 'remove_alert_ids' in serializer.validated_data):
            logger.info(f"Alerts updated for incident {instance.id} - Total: {instance.related_alerts.count()}")
    
    def perform_destroy(self, instance):
        """
        Removes an incident with appropriate logging and restores alert statuses.
        """
        title = instance.title
        severity = instance.get_severity_display()
        status = instance.get_status_display()
        user = self.request.user
        
        # Get related alerts before deletion
        related_alerts = list(instance.related_alerts.all())
        
        # Remove the incident
        instance.delete()
        
        # Log the removal
        logger.info(f"Incident removed: {title} ({severity}, {status}) by {user.username}")
        
        # Restore alert statuses to "under_investigation"
        for alert in related_alerts:
            alert.status = Alert.Status.UNDER_INVESTIGATION
            alert.save(update_fields=['status'])
            logger.info(f"Alert status {alert.id} restored after incident removal") 