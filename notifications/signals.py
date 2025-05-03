import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.template import Template, Context
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from alerts.models import Alert
from incidents.models import Incident
from tasks.models import Task
from .models import NotificationRule, Notification
from .tasks import send_notification

logger = logging.getLogger('api.notifications')


def evaluate_conditions(conditions, obj):
    """
    Evaluate if all conditions are met for the object.
    
    Args:
        conditions (dict): Dictionary of field-value conditions
        obj: Object to evaluate against
        
    Returns:
        bool: True if all conditions are met, False otherwise
    """
    if not conditions:
        return True
        
    # Simple field-value equality checks
    for field, expected_value in conditions.items():
        if hasattr(obj, field):
            actual_value = getattr(obj, field)
            # Convert both to strings for comparison
            if str(actual_value) != str(expected_value):
                return False
        else:
            # Field doesn't exist on object
            return False
            
    return True


def render_template(template_str, context_dict):
    """
    Render a template string with a context dictionary.
    
    Args:
        template_str (str): Template string with {{ variables }}
        context_dict (dict): Context dictionary with values
        
    Returns:
        str: Rendered string
    """
    try:
        template = Template(template_str)
        context = Context(context_dict)
        return template.render(context)
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return template_str  # Return original as fallback


def get_notification_rules(event_type, company_id):
    """
    Get active notification rules for a given event type and company.
    
    Args:
        event_type (str): Event type identifier
        company_id: Company ID
        
    Returns:
        QuerySet: Matching notification rules
    """
    return NotificationRule.objects.filter(
        event_type=event_type,
        company_id=company_id,
        is_active=True
    )


def process_alert_notification(alert, event_type):
    """Process notification rules for alert events"""
    try:
        # Get matching rules
        rules = get_notification_rules(event_type, alert.company.id)
        
        for rule in rules:
            # Evaluate conditions
            if not evaluate_conditions(rule.conditions, alert):
                continue
                
            # Prepare context for template rendering
            context = {
                'alert': {
                    'id': alert.id,
                    'title': alert.title,
                    'description': getattr(alert, 'description', ''),
                    'severity': getattr(alert, 'severity', ''),
                    'status': getattr(alert, 'status', ''),
                    'created_at': alert.created_at,
                }
            }
            
            # Create notification
            title = render_template(rule.message_template.split('\n')[0], context)
            message = render_template(rule.message_template, context)
            
            notification = Notification.objects.create(
                title=title,
                message=message,
                category='alert',
                priority=getattr(alert, 'severity', 'medium'),
                related_object_type='alert',
                related_object_id=alert.id,
                triggered_by_rule=rule,
                company=alert.company,
                is_company_wide=False  # Default to specific recipients
            )
            
            # Queue notification delivery for each channel
            for channel in rule.channels.filter(is_enabled=True):
                # Determine recipients based on role/department/etc.
                recipients = []
                
                # Add alert assignee if any
                if hasattr(alert, 'assignee') and alert.assignee:
                    recipients.append(alert.assignee)
                
                # Add company admins
                admin_users = alert.company.user_set.filter(role__contains='admin')
                recipients.extend(admin_users)
                
                # Add recipients to notification
                for recipient in set(recipients):  # Use set to deduplicate
                    notification.recipients.add(recipient)
                    
                    # Queue async task to send notification
                    send_notification.delay(
                        notification_id=notification.id,
                        channel_id=channel.id,
                        recipient_id=recipient.id
                    )
                    
    except Exception as e:
        logger.error(f"Error processing alert notification: {str(e)}")


def process_incident_notification(incident, event_type):
    """Process notification rules for incident events"""
    try:
        # Get matching rules
        rules = get_notification_rules(event_type, incident.company.id)
        
        for rule in rules:
            # Evaluate conditions
            if not evaluate_conditions(rule.conditions, incident):
                continue
                
            # Prepare context for template rendering
            context = {
                'incident': {
                    'id': incident.id,
                    'title': incident.title,
                    'description': getattr(incident, 'description', ''),
                    'severity': getattr(incident, 'severity', ''),
                    'status': getattr(incident, 'status', ''),
                    'created_at': incident.created_at,
                }
            }
            
            # Create notification
            title = render_template(rule.message_template.split('\n')[0], context)
            message = render_template(rule.message_template, context)
            
            notification = Notification.objects.create(
                title=title,
                message=message,
                category='incident',
                priority=getattr(incident, 'severity', 'medium'),
                related_object_type='incident',
                related_object_id=incident.id,
                triggered_by_rule=rule,
                company=incident.company,
                is_company_wide=False
            )
            
            # Queue notification delivery for each channel
            for channel in rule.channels.filter(is_enabled=True):
                # Determine recipients
                recipients = []
                
                # Add incident assignee if any
                if hasattr(incident, 'assignee') and incident.assignee:
                    recipients.append(incident.assignee)
                
                # Add company admins and security analysts
                admin_users = incident.company.user_set.filter(
                    Q(role__contains='admin') | Q(role__contains='analyst')
                )
                recipients.extend(admin_users)
                
                # Add recipients to notification
                for recipient in set(recipients):
                    notification.recipients.add(recipient)
                    
                    # Queue async task to send notification
                    send_notification.delay(
                        notification_id=notification.id,
                        channel_id=channel.id,
                        recipient_id=recipient.id
                    )
                    
    except Exception as e:
        logger.error(f"Error processing incident notification: {str(e)}")


def process_task_notification(task, event_type):
    """Process notification rules for task events"""
    try:
        # Get matching rules
        rules = get_notification_rules(event_type, task.company.id)
        
        for rule in rules:
            # Evaluate conditions
            if not evaluate_conditions(rule.conditions, task):
                continue
                
            # Prepare context for template rendering
            context = {
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'description': getattr(task, 'description', ''),
                    'priority': getattr(task, 'priority', ''),
                    'status': getattr(task, 'status', ''),
                    'created_at': task.created_at,
                    'due_date': getattr(task, 'due_date', ''),
                }
            }
            
            # Add incident context if available
            if hasattr(task, 'incident') and task.incident:
                context['incident'] = {
                    'id': task.incident.id,
                    'title': task.incident.title
                }
            
            # Create notification
            title = render_template(rule.message_template.split('\n')[0], context)
            message = render_template(rule.message_template, context)
            
            notification = Notification.objects.create(
                title=title,
                message=message,
                category='task',
                priority=getattr(task, 'priority', 'medium'),
                related_object_type='task',
                related_object_id=task.id,
                triggered_by_rule=rule,
                company=task.company,
                is_company_wide=False
            )
            
            # Queue notification delivery for each channel
            for channel in rule.channels.filter(is_enabled=True):
                # Determine recipients
                recipients = []
                
                # Add task assignee if any
                if hasattr(task, 'assignee') and task.assignee:
                    recipients.append(task.assignee)
                
                # Add incident owner if this task is part of an incident
                if hasattr(task, 'incident') and task.incident and hasattr(task.incident, 'owner') and task.incident.owner:
                    recipients.append(task.incident.owner)
                
                # Add recipients to notification
                for recipient in set(recipients):
                    notification.recipients.add(recipient)
                    
                    # Queue async task to send notification
                    send_notification.delay(
                        notification_id=notification.id,
                        channel_id=channel.id,
                        recipient_id=recipient.id
                    )
                    
    except Exception as e:
        logger.error(f"Error processing task notification: {str(e)}")


@receiver(post_save, sender=Alert)
def alert_event_handler(sender, instance, created, **kwargs):
    """Handle alert events for notifications"""
    try:
        if created:
            # New alert created
            process_alert_notification(instance, 'alert_created')
        else:
            # Alert updated
            process_alert_notification(instance, 'alert_updated')
            
            # Check if alert was just escalated to an incident
            if instance.incidents.exists() and not instance.tracker.previous('incidents'):
                process_alert_notification(instance, 'alert_escalated')
                
    except Exception as e:
        logger.error(f"Error in alert event handler: {str(e)}")


@receiver(post_save, sender=Incident)
def incident_event_handler(sender, instance, created, **kwargs):
    """Handle incident events for notifications"""
    try:
        if created:
            # New incident created
            process_incident_notification(instance, 'incident_created')
        else:
            # Incident updated
            process_incident_notification(instance, 'incident_updated')
            
            # Check if incident was just closed
            if instance.status == 'closed' and instance.tracker.previous('status') != 'closed':
                process_incident_notification(instance, 'incident_closed')
                
    except Exception as e:
        logger.error(f"Error in incident event handler: {str(e)}")


@receiver(post_save, sender=Task)
def task_event_handler(sender, instance, created, **kwargs):
    """Handle task events for notifications"""
    try:
        if created:
            # New task created
            process_task_notification(instance, 'task_created')
        else:
            # Task updated
            process_task_notification(instance, 'task_updated')
            
            # Check if task was just completed
            if instance.status == 'completed' and instance.tracker.previous('status') != 'completed':
                process_task_notification(instance, 'task_completed')
                
    except Exception as e:
        logger.error(f"Error in task event handler: {str(e)}") 