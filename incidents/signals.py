import logging
import json
from django.db.models.signals import post_save, m2m_changed, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.forms.models import model_to_dict
from .models import Incident, TimelineEvent, IncidentObservable, IncidentTask

User = get_user_model()
logger = logging.getLogger('api.incidents')


@receiver(pre_save, sender=Incident)
def track_incident_field_changes(sender, instance, **kwargs):
    """
    Tracks changes in incident fields and creates timeline events for significant changes.
    """
    # Skip for new incidents as they'll get the CREATED event instead
    if not instance.pk:
        return
    
    try:
        # Get the incident as it exists in the database
        old_incident = Incident.objects.get(pk=instance.pk)
        
        # Track changes to description
        if old_incident.description != instance.description:
            TimelineEvent.objects.create(
                incident=instance,
                type=TimelineEvent.EventType.UPDATED,
                title="Description updated",
                message=f"Incident description was updated",
                company=instance.company,
                metadata={
                    'field': 'description',
                    'old_value_length': len(old_incident.description),
                    'new_value_length': len(instance.description)
                }
            )
        
        # Track status changes
        if old_incident.status != instance.status:
            TimelineEvent.objects.create(
                incident=instance,
                type=TimelineEvent.EventType.STATUS_CHANGED,
                title=f"Status changed: {old_incident.get_status_display()} → {instance.get_status_display()}",
                message=f"Incident status was changed from {old_incident.get_status_display()} to {instance.get_status_display()}",
                company=instance.company,
                metadata={
                    'field': 'status',
                    'old_value': old_incident.status,
                    'new_value': instance.status
                }
            )
        
        # Track severity changes
        if old_incident.severity != instance.severity:
            TimelineEvent.objects.create(
                incident=instance,
                type=TimelineEvent.EventType.UPDATED,
                title=f"Severity changed: {old_incident.get_severity_display()} → {instance.get_severity_display()}",
                message=f"Incident severity was changed from {old_incident.get_severity_display()} to {instance.get_severity_display()}",
                company=instance.company,
                metadata={
                    'field': 'severity',
                    'old_value': old_incident.severity,
                    'new_value': instance.severity
                }
            )
        
        # Track assignee changes
        if old_incident.assignee != instance.assignee:
            old_assignee = old_incident.assignee.get_full_name() if old_incident.assignee else "Unassigned"
            new_assignee = instance.assignee.get_full_name() if instance.assignee else "Unassigned"
            
            TimelineEvent.objects.create(
                incident=instance,
                type=TimelineEvent.EventType.ASSIGNED,
                title=f"Assignee changed: {old_assignee} → {new_assignee}",
                message=f"Incident assignee was changed from {old_assignee} to {new_assignee}",
                company=instance.company,
                metadata={
                    'field': 'assignee',
                    'old_value': str(old_incident.assignee.id) if old_incident.assignee else None,
                    'new_value': str(instance.assignee.id) if instance.assignee else None
                }
            )
            
        # Track TLP/PAP changes
        if old_incident.tlp != instance.tlp:
            TimelineEvent.objects.create(
                incident=instance,
                type=TimelineEvent.EventType.UPDATED,
                title=f"TLP changed: {old_incident.get_tlp_display()} → {instance.get_tlp_display()}",
                message=f"Incident TLP level was changed from {old_incident.get_tlp_display()} to {instance.get_tlp_display()}",
                company=instance.company,
                metadata={
                    'field': 'tlp',
                    'old_value': old_incident.tlp,
                    'new_value': instance.tlp
                }
            )
            
        if old_incident.pap != instance.pap:
            TimelineEvent.objects.create(
                incident=instance,
                type=TimelineEvent.EventType.UPDATED,
                title=f"PAP changed: {old_incident.get_pap_display()} → {instance.get_pap_display()}",
                message=f"Incident PAP level was changed from {old_incident.get_pap_display()} to {instance.get_pap_display()}",
                company=instance.company,
                metadata={
                    'field': 'pap',
                    'old_value': old_incident.pap,
                    'new_value': instance.pap
                }
            )
    
    except Incident.DoesNotExist:
        # This shouldn't happen, but just in case
        logger.warning(f"Could not find incident with ID {instance.pk} to track changes")
    except Exception as e:
        logger.error(f"Error tracking incident field changes for {instance.pk}: {str(e)}")


@receiver(post_save, sender=Incident)
def sync_timeline_to_events(sender, instance, created, **kwargs):
    """
    Syncs the timeline JSONField entries to TimelineEvent model instances.
    Only creates new entries that don't yet exist in the database.
    """
    if created:
        # If a new incident is created, add a "created" event
        try:
            TimelineEvent.objects.create(
                incident=instance,
                type=TimelineEvent.EventType.CREATED,
                title="Incident created",
                message=f"Incident '{instance.title}' was created",
                user=instance.created_by,
                company=instance.company,
                timestamp=instance.created_at
            )
        except Exception as e:
            logger.error(f"Error creating timeline event for new incident {instance.id}: {str(e)}")
    
    # Skip if no timeline data
    if not instance.timeline or not isinstance(instance.timeline, list):
        return
    
    # Track which timeline entries we've already processed
    try:
        # Get IDs of existing timeline events in the database
        existing_event_ids = set(TimelineEvent.objects.filter(
            incident=instance,
            metadata__timeline_entry_id__isnull=False
        ).values_list('metadata__timeline_entry_id', flat=True))
        
        # Process each entry in the timeline JSONField
        for entry in instance.timeline:
            entry_id = entry.get('id')
            
            # Skip if we've already processed this entry
            if not entry_id or entry_id in existing_event_ids:
                continue
            
            # Map timeline entry to event type
            entry_type = entry.get('type', 'note')
            event_type = TimelineEvent.EventType.NOTE
            
            # Map common types
            if entry_type == 'note':
                event_type = TimelineEvent.EventType.NOTE
            elif entry_type == 'assignment':
                event_type = TimelineEvent.EventType.ASSIGNED
            elif entry_type == 'status_change':
                event_type = TimelineEvent.EventType.STATUS_CHANGED
            elif entry_type == 'alert_link':
                event_type = TimelineEvent.EventType.ALERT_LINKED
            elif entry_type == 'task_update':
                event_type = TimelineEvent.EventType.TASK_ADDED
            elif entry_type == 'action':
                event_type = TimelineEvent.EventType.ACTION
            elif entry_type == 'system':
                event_type = TimelineEvent.EventType.SYSTEM
            
            # Get user if available
            user = None
            created_by_id = entry.get('created_by')
            if created_by_id:
                try:
                    user = User.objects.get(id=created_by_id)
                except User.DoesNotExist:
                    logger.warning(f"User {created_by_id} referenced in timeline entry not found")
            
            # Prepare timestamp
            entry_timestamp = entry.get('timestamp')
            if not entry_timestamp:
                entry_timestamp = timezone.now()
            
            # Create timeline event
            TimelineEvent.objects.create(
                incident=instance,
                type=event_type,
                title=entry.get('title', 'Event'),
                message=entry.get('content', ''),
                user=user,
                company=instance.company,
                timestamp=entry_timestamp,
                metadata={
                    'timeline_entry_id': entry_id,
                    'original_entry': entry
                }
            )
            
            # Add to processed set
            existing_event_ids.add(entry_id)
            
    except Exception as e:
        logger.error(f"Error syncing timeline entries for incident {instance.id}: {str(e)}")


# Observable related signals
@receiver(post_save, sender=IncidentObservable)
def observable_added_timeline_event(sender, instance, created, **kwargs):
    """
    Creates a timeline event when an observable is added to an incident.
    """
    if created:
        try:
            TimelineEvent.objects.create(
                incident=instance.incident,
                type=TimelineEvent.EventType.UPDATED,
                title=f"Observable added: {instance.observable.get_type_display()}",
                message=f"Observable {instance.observable.get_type_display()}: {instance.observable.value} added to incident",
                company=instance.incident.company,
                metadata={
                    'observable_id': str(instance.observable.id),
                    'observable_type': instance.observable.type,
                    'observable_value': instance.observable.value,
                    'is_ioc': instance.is_ioc
                }
            )
        except Exception as e:
            logger.error(f"Error creating timeline event for observable addition: {str(e)}")


@receiver(pre_save, sender=IncidentObservable)
def observable_updated_timeline_event(sender, instance, **kwargs):
    """
    Creates a timeline event when an observable's metadata is updated (like marking as IOC).
    """
    if not instance.pk:
        return  # Skip for new instances
        
    try:
        old_instance = IncidentObservable.objects.get(pk=instance.pk)
        
        # Check if IOC status changed
        if old_instance.is_ioc != instance.is_ioc:
            status = "marked as IOC" if instance.is_ioc else "unmarked as IOC"
            TimelineEvent.objects.create(
                incident=instance.incident,
                type=TimelineEvent.EventType.UPDATED,
                title=f"Observable {status}",
                message=f"Observable {instance.observable.get_type_display()}: {instance.observable.value} {status}",
                company=instance.incident.company,
                metadata={
                    'observable_id': str(instance.observable.id),
                    'field': 'is_ioc',
                    'old_value': old_instance.is_ioc,
                    'new_value': instance.is_ioc
                }
            )
    except Exception as e:
        logger.error(f"Error creating timeline event for observable update: {str(e)}")


@receiver(post_delete, sender=IncidentObservable)
def observable_removed_timeline_event(sender, instance, **kwargs):
    """
    Creates a timeline event when an observable is removed from an incident.
    """
    try:
        TimelineEvent.objects.create(
            incident=instance.incident,
            type=TimelineEvent.EventType.UPDATED,
            title=f"Observable removed: {instance.observable.get_type_display()}",
            message=f"Observable {instance.observable.get_type_display()}: {instance.observable.value} removed from incident",
            company=instance.incident.company,
            metadata={
                'observable_id': str(instance.observable.id),
                'observable_type': instance.observable.type,
                'observable_value': instance.observable.value
            }
        )
    except Exception as e:
        logger.error(f"Error creating timeline event for observable removal: {str(e)}")


# Task related signals
@receiver(post_save, sender=IncidentTask)
def task_created_or_updated_timeline_event(sender, instance, created, **kwargs):
    """
    Creates a timeline event when a task is created or updated.
    """
    if created:
        try:
            TimelineEvent.objects.create(
                incident=instance.incident,
                type=TimelineEvent.EventType.TASK_ADDED,
                title=f"Task created: {instance.title}",
                message=f"Task '{instance.title}' created with {instance.get_status_display()} status",
                user=instance.created_by,
                company=instance.incident.company,
                metadata={
                    'task_id': str(instance.id),
                    'title': instance.title,
                    'status': instance.status,
                    'priority': instance.priority,
                    'assignee': str(instance.assignee.id) if instance.assignee else None
                }
            )
        except Exception as e:
            logger.error(f"Error creating timeline event for task creation: {str(e)}")
    else:
        # Task was updated
        try:
            old_instance = IncidentTask.objects.get(pk=instance.pk)
            
            # Check if status changed
            if old_instance.status != instance.status:
                # Special case for task completion
                if instance.status == IncidentTask.Status.COMPLETED and old_instance.status != IncidentTask.Status.COMPLETED:
                    TimelineEvent.objects.create(
                        incident=instance.incident,
                        type=TimelineEvent.EventType.TASK_COMPLETED,
                        title=f"Task completed: {instance.title}",
                        message=f"Task '{instance.title}' marked as completed",
                        user=instance.assignee,  # Use assignee if available
                        company=instance.incident.company,
                        metadata={
                            'task_id': str(instance.id),
                            'title': instance.title,
                            'old_status': old_instance.status,
                            'new_status': instance.status,
                            'completion_time': instance.completed_at.isoformat() if instance.completed_at else timezone.now().isoformat()
                        }
                    )
                else:
                    TimelineEvent.objects.create(
                        incident=instance.incident,
                        type=TimelineEvent.EventType.UPDATED,
                        title=f"Task status changed: {instance.title}",
                        message=f"Task '{instance.title}' status changed from {old_instance.get_status_display()} to {instance.get_status_display()}",
                        company=instance.incident.company,
                        metadata={
                            'task_id': str(instance.id),
                            'field': 'status',
                            'old_value': old_instance.status,
                            'new_value': instance.status
                        }
                    )
            
            # Check if assignee changed
            if old_instance.assignee != instance.assignee:
                old_assignee = old_instance.assignee.get_full_name() if old_instance.assignee else "Unassigned"
                new_assignee = instance.assignee.get_full_name() if instance.assignee else "Unassigned"
                
                TimelineEvent.objects.create(
                    incident=instance.incident,
                    type=TimelineEvent.EventType.ASSIGNED,
                    title=f"Task assignee changed: {instance.title}",
                    message=f"Task '{instance.title}' assignee changed from {old_assignee} to {new_assignee}",
                    company=instance.incident.company,
                    metadata={
                        'task_id': str(instance.id),
                        'field': 'assignee',
                        'old_value': str(old_instance.assignee.id) if old_instance.assignee else None,
                        'new_value': str(instance.assignee.id) if instance.assignee else None
                    }
                )
                
            # Check if due date changed
            if old_instance.due_date != instance.due_date:
                old_due = old_instance.due_date.isoformat() if old_instance.due_date else "None"
                new_due = instance.due_date.isoformat() if instance.due_date else "None"
                
                TimelineEvent.objects.create(
                    incident=instance.incident,
                    type=TimelineEvent.EventType.UPDATED,
                    title=f"Task due date changed: {instance.title}",
                    message=f"Task '{instance.title}' due date updated",
                    company=instance.incident.company,
                    metadata={
                        'task_id': str(instance.id),
                        'field': 'due_date',
                        'old_value': old_due,
                        'new_value': new_due
                    }
                )
                
        except Exception as e:
            logger.error(f"Error creating timeline event for task update: {str(e)}")


@receiver(post_delete, sender=IncidentTask)
def task_deleted_timeline_event(sender, instance, **kwargs):
    """
    Creates a timeline event when a task is deleted.
    """
    try:
        TimelineEvent.objects.create(
            incident=instance.incident,
            type=TimelineEvent.EventType.UPDATED,
            title=f"Task deleted: {instance.title}",
            message=f"Task '{instance.title}' was deleted from incident",
            company=instance.incident.company,
            metadata={
                'task_id': str(instance.id),
                'title': instance.title,
                'status': instance.status
            }
        )
    except Exception as e:
        logger.error(f"Error creating timeline event for task deletion: {str(e)}")


@receiver(m2m_changed, sender=Incident.related_alerts.through)
def alert_linked_timeline_event(sender, instance, action, pk_set, **kwargs):
    """
    Creates a timeline event when an alert is linked to an incident.
    """
    if action == 'post_add' and pk_set:
        try:
            # Get the alert IDs and convert UUIDs to strings
            alert_ids = [str(aid) for aid in pk_set]
            
            # Get the count
            count = len(alert_ids)
            
            # Create a timeline event
            TimelineEvent.objects.create(
                incident=instance,
                type=TimelineEvent.EventType.ALERT_LINKED,
                title=f"{count} alert{'s' if count > 1 else ''} linked to incident",
                message=f"Alert{'s' if count > 1 else ''} with ID{'' if count == 1 else 's'} {', '.join(alert_ids)} linked to this incident",
                company=instance.company,
                user=instance.assignee,  # We don't know who linked it, could add user context in the future
                metadata={
                    'alert_ids': alert_ids,
                    'count': count
                }
            )
        except Exception as e:
            logger.error(f"Error creating timeline event for alert linking in incident {instance.id}: {str(e)}") 