import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from sentinelvision.models import (
    FeedModule, AnalyzerModule, ResponderModule,
    FeedRegistry, ExecutionRecord
)
from sentinelvision.logging import get_structured_logger
from incidents.models import Incident
from api.v1.sentinelvision.enums import ExecutionStatusEnum

logger = get_structured_logger(__name__)


@receiver(pre_save, sender=FeedModule)
def validate_feed_module(sender, instance, **kwargs):
    """Validate feed module configuration before saving."""
    try:
        instance.validate_configuration()
    except Exception as e:
        logger.error(
            "Feed module validation failed",
            extra={
                "module_name": instance.name,
                "error": str(e)
            }
        )
        raise

@receiver(pre_save, sender=AnalyzerModule)
def validate_analyzer_module(sender, instance, **kwargs):
    """Validate analyzer module configuration before saving."""
    try:
        instance.validate_configuration()
    except Exception as e:
        logger.error(
            "Analyzer module validation failed",
            extra={
                "module_name": instance.name,
                "error": str(e)
            }
        )
        raise

@receiver(pre_save, sender=ResponderModule)
def validate_responder_module(sender, instance, **kwargs):
    """Validate responder module configuration before saving."""
    try:
        instance.validate_configuration()
    except Exception as e:
        logger.error(
            "Responder module validation failed",
            extra={
                "module_name": instance.name,
                "error": str(e)
            }
        )
        raise

@receiver(post_save, sender=FeedModule)
def create_feed_registry(sender, instance, created, **kwargs):
    """Create or update feed registry when a feed module is saved."""
    if created:
        FeedRegistry.objects.create(
            name=instance.name,
            feed_type=instance.module_type,
            company=instance.company,
            source_url=instance.feed_url,
            description=instance.description,
            sync_interval_hours=instance.interval_hours,
            enabled=instance.is_active
        )
        logger.info(
            "Created feed registry",
            extra={
                "module_name": instance.name,
                "feed_type": instance.module_type
            }
        )

@receiver(post_save, sender=ExecutionRecord)
def log_execution_record(sender, instance, created, **kwargs):
    """Log execution record status changes."""
    if instance.status == ExecutionStatusEnum.SUCCESS.value:
        logger.info(
            "Module execution completed successfully",
            extra={
                "module_name": instance.module_name,
                "module_type": instance.module_type,
                "duration_seconds": instance.duration_seconds,
                "result_count": instance.result_count
            }
        )
    elif instance.status == ExecutionStatusEnum.ERROR.value:
        logger.error(
            "Module execution failed",
            extra={
                "module_name": instance.module_name,
                "module_type": instance.module_type,
                "error": instance.error_message
            }
        )

@receiver(post_save, sender=Incident)
def handle_incident_severity_change(sender, instance, **kwargs):
    """
    Signal handler for incident severity changes.
    Potentially triggers automated analysis of associated observables when severity is elevated.
    
    Args:
        sender: The model class (Incident)
        instance: The Incident instance that was saved
        **kwargs: Additional arguments
    """
    # Check if this is an existing incident and severity has been changed
    if not kwargs.get('created', False) and instance.tracker.has_changed('severity'):
        old_severity = instance.tracker.previous('severity')
        new_severity = instance.severity
        
        # Only act on severity increases
        if new_severity > old_severity:
            logger.info(f"Incident #{instance.id} severity increased from {old_severity} to {new_severity}")
            
            # Logic to trigger automated analysis would go here 