from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from api.v1.misp_sync.models import MISPServer, MISPEvent, MISPAttribute
from api.v1.audit_logs.enums import EntityTypeEnum, ActionTypeEnum
import logging

logger = logging.getLogger('api')


@receiver(post_save, sender=MISPServer)
def misp_server_post_save(sender, instance, created, **kwargs):
    """
    Handler for post-save signal on MISPServer model.
    Logs the creation or update of a MISP server.
    """
    if created:
        logger.info(f"MISP server created: {instance.name} (ID: {instance.id})")
    else:
        logger.info(f"MISP server updated: {instance.name} (ID: {instance.id})")
        
    # Additional actions could be taken here, such as:
    # - Schedule initial sync for new servers
    # - Notify admins of changes to server configuration


@receiver(post_save, sender=MISPEvent)
def misp_event_post_save(sender, instance, created, **kwargs):
    """
    Handler for post-save signal on MISPEvent model.
    Logs the creation or update of a MISP event.
    """
    if created:
        logger.info(f"MISP event imported: {instance.info} (ID: {instance.id})")
        
        # In a real implementation, we might want to:
        # - Generate an alert automatically
        # - Notify relevant users about new threat intelligence
        # - Correlate with existing observables
    else:
        logger.info(f"MISP event updated: {instance.info} (ID: {instance.id})")


@receiver(post_save, sender=MISPAttribute)
def misp_attribute_post_save(sender, instance, created, **kwargs):
    """
    Handler for post-save signal on MISPAttribute model.
    Logs the creation or update of a MISP attribute.
    """
    if created:
        logger.info(f"MISP attribute imported: {instance.type}:{instance.value} (ID: {instance.id})")
        
        # In a real implementation, we might want to:
        # - Convert to an Observable automatically
        # - Check for matches in existing data
    else:
        logger.info(f"MISP attribute updated: {instance.type}:{instance.value} (ID: {instance.id})")


@receiver(post_delete, sender=MISPServer)
def misp_server_post_delete(sender, instance, **kwargs):
    """
    Handler for post-delete signal on MISPServer model.
    Logs the deletion of a MISP server.
    """
    logger.info(f"MISP server deleted: {instance.name} (ID: {instance.id})") 