"""
Notification tasks for SentinelIQ.

This module contains background tasks for sending notifications
through various channels including email, Slack, and in-app notifications.
"""

import logging
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple, Optional, Dict, Any

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from sentineliq.tasks.base import register_task, BaseTask

# Configure logger
logger = logging.getLogger('sentineliq.tasks.notifications')
User = get_user_model()


@register_task(
    name='sentineliq.tasks.notifications.send_notification',
    queue='sentineliq_soar_notification',
    base=BaseTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    acks_late=True
)
def send_notification(self, notification_id, channel_id, recipient_id=None):
    """
    Send a notification through a specific channel to a recipient.
    
    Args:
        notification_id: ID of the notification to send
        channel_id: ID of the channel to use for delivery
        recipient_id: ID of the recipient user (optional)
        
    Returns:
        dict: Result of the notification delivery
    """
    from notifications.models import NotificationChannel, Notification, NotificationDeliveryStatus
    
    logger.info(f"Sending notification {notification_id} via channel {channel_id}")
    
    try:
        # Get the notification, channel and recipient
        notification = Notification.objects.get(id=notification_id)
        channel = NotificationChannel.objects.get(id=channel_id)
        recipient = User.objects.get(id=recipient_id) if recipient_id else None
        
        # If no recipient specified and notification is company-wide,
        # Send to all users in the company
        if not recipient and notification.is_company_wide:
            company_users = User.objects.filter(company=notification.company)
            
            # Create batch notification task instead of individual tasks
            user_ids = list(company_users.values_list('id', flat=True))
            if user_ids:
                send_batch_notification.apply_async(
                    kwargs={
                        'notification_id': notification_id,
                        'channel_id': channel_id,
                        'recipient_ids': user_ids
                    }
                )
                
            return {
                'status': 'success',
                'message': f"Scheduled batch notification for {len(user_ids)} recipients",
                'notification_id': notification_id,
                'channel_id': channel_id
            }
        
        if not recipient:
            logger.error(f"No recipient specified for notification {notification_id}")
            return {
                'status': 'error',
                'error': 'recipient_not_specified',
                'notification_id': notification_id
            }
        
        # Create or get delivery status
        delivery_status, created = NotificationDeliveryStatus.objects.get_or_create(
            notification=notification,
            channel=channel,
            recipient=recipient,
            defaults={'status': 'pending'}
        )
        
        # Send based on channel type
        success = False
        error_message = None
        
        if channel.channel_type == 'email':
            success, error_message = _send_email_notification(channel, notification, recipient)
        elif channel.channel_type == 'slack':
            success, error_message = _send_slack_notification(channel, notification, recipient)
        elif channel.channel_type == 'mattermost':
            success, error_message = _send_mattermost_notification(channel, notification, recipient)
        elif channel.channel_type == 'webhook':
            success, error_message = _send_webhook_notification(channel, notification, recipient)
        elif channel.channel_type == 'in_app':
            # In-app notifications are already created in the database,
            # so we just mark them as delivered
            success = True
        else:
            error_message = f"Unsupported channel type: {channel.channel_type}"
            
        # Update delivery status
        if success:
            delivery_status.status = 'delivered'
            delivery_status.delivered_at = timezone.now()
        else:
            delivery_status.status = 'failed'
            delivery_status.error_message = error_message
            
        delivery_status.sent_at = timezone.now()
        delivery_status.save()
        
        logger.info(
            f"Notification {notification_id} sent to {recipient.email} via {channel.channel_type}: "
            f"{'Success' if success else 'Failed'}"
        )
        
        return {
            'status': 'success' if success else 'error',
            'notification_id': notification_id,
            'channel_id': channel_id,
            'recipient_id': recipient_id,
            'error': error_message if not success else None
        }
        
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {str(e)}")
        
        # Re-raise for Celery retry mechanism
        raise


@register_task(
    name='sentineliq.tasks.notifications.send_batch_notification',
    queue='sentineliq_soar_notification',
    base=BaseTask
)
def send_batch_notification(self, notification_id, channel_id, recipient_ids):
    """
    Send a notification to multiple recipients efficiently.
    
    Args:
        notification_id: ID of the notification to send
        channel_id: ID of the channel to use for delivery
        recipient_ids: List of recipient user IDs
        
    Returns:
        dict: Batch delivery results
    """
    from notifications.models import NotificationChannel, Notification, NotificationDeliveryStatus
    
    logger.info(f"Sending batch notification {notification_id} to {len(recipient_ids)} recipients")
    
    try:
        notification = Notification.objects.get(id=notification_id)
        channel = NotificationChannel.objects.get(id=channel_id)
        
        results = {
            'total': len(recipient_ids),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # For some notification types, we can do bulk delivery
        if channel.channel_type == 'webhook':
            # Example: Customize for webhook bulk delivery
            pass
        else:
            # Default: individual processing
            for recipient_id in recipient_ids:
                try:
                    # Create individual delivery record
                    recipient = User.objects.get(id=recipient_id)
                    
                    # Get or create delivery status
                    delivery_status, _ = NotificationDeliveryStatus.objects.get_or_create(
                        notification=notification,
                        channel=channel,
                        recipient=recipient,
                        defaults={'status': 'pending'}
                    )
                    
                    # Send notification
                    success, error = False, None
                    
                    if channel.channel_type == 'email':
                        success, error = _send_email_notification(channel, notification, recipient)
                    elif channel.channel_type == 'slack':
                        success, error = _send_slack_notification(channel, notification, recipient)
                    elif channel.channel_type == 'mattermost':
                        success, error = _send_mattermost_notification(channel, notification, recipient)
                    elif channel.channel_type == 'webhook':
                        success, error = _send_webhook_notification(channel, notification, recipient)
                    elif channel.channel_type == 'in_app':
                        success = True
                    
                    # Update delivery status
                    if success:
                        delivery_status.status = 'delivered'
                        delivery_status.delivered_at = timezone.now()
                        results['successful'] += 1
                    else:
                        delivery_status.status = 'failed'
                        delivery_status.error_message = error
                        results['failed'] += 1
                        results['errors'].append({
                            'recipient_id': recipient_id,
                            'error': error
                        })
                        
                    delivery_status.sent_at = timezone.now()
                    delivery_status.save()
                    
                except User.DoesNotExist:
                    results['failed'] += 1
                    results['errors'].append({
                        'recipient_id': recipient_id,
                        'error': 'User not found'
                    })
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'recipient_id': recipient_id,
                        'error': str(e)
                    })
        
        return {
            'status': 'success',
            'notification_id': notification_id,
            'channel_id': channel_id,
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Error processing batch notification: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'notification_id': notification_id,
            'channel_id': channel_id
        }


# Helper functions for sending through different channels

def _send_email_notification(channel, notification, recipient) -> Tuple[bool, Optional[str]]:
    """
    Send notification via email.
    
    Args:
        channel: NotificationChannel instance
        notification: Notification instance
        recipient: User instance
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        config = channel.config
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = config.get('from_email', settings.DEFAULT_FROM_EMAIL)
        msg['To'] = recipient.email
        msg['Subject'] = notification.title
        
        # Add message body
        msg.attach(MIMEText(notification.message, 'plain'))
        
        # Connect to SMTP server
        with smtplib.SMTP(config.get('smtp_host', 'smtp.gmail.com'), 
                          config.get('smtp_port', 587)) as server:
            server.starttls()
            server.login(
                config.get('smtp_username'), 
                config.get('smtp_password')
            )
            server.send_message(msg)
            
        return True, None
        
    except Exception as e:
        return False, str(e)


def _send_slack_notification(channel, notification, recipient) -> Tuple[bool, Optional[str]]:
    """
    Send notification via Slack.
    
    Args:
        channel: NotificationChannel instance
        notification: Notification instance
        recipient: User instance
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        config = channel.config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            return False, "No webhook URL configured for Slack channel"
            
        # Prepare payload
        payload = {
            "text": f"*{notification.title}*\n{notification.message}",
            "username": config.get('username', 'SentinelIQ Bot'),
            "icon_emoji": config.get('icon_emoji', ':robot_face:')
        }
        
        # Send to Slack
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 200:
            return True, None
        else:
            return False, f"Slack API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, str(e)


def _send_mattermost_notification(channel, notification, recipient) -> Tuple[bool, Optional[str]]:
    """
    Send notification via Mattermost.
    
    Args:
        channel: NotificationChannel instance
        notification: Notification instance
        recipient: User instance
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        config = channel.config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            return False, "No webhook URL configured for Mattermost channel"
        
        # Get recipient notification preferences if available
        try:
            preferences = recipient.notification_preferences
            
            # Check if recipient wants to receive this type of notification
            if notification.category == 'alert' and not preferences.mattermost_alerts:
                return True, "Skipped: Recipient has disabled Mattermost alerts"
            elif notification.category == 'incident' and not preferences.mattermost_incidents:
                return True, "Skipped: Recipient has disabled Mattermost incidents"
            elif notification.category == 'task' and not preferences.mattermost_tasks:
                return True, "Skipped: Recipient has disabled Mattermost tasks"
                
            # Check for critical-only setting
            if preferences.mattermost_critical_only and notification.priority != 'critical':
                return True, "Skipped: Recipient only wants critical notifications"
                
        except (AttributeError, Exception):
            # If preferences don't exist, proceed with default behavior
            pass
            
        # Determine color based on priority
        if notification.priority == 'critical':
            color = 'danger'  # Red
        elif notification.priority == 'high':
            color = 'warning'  # Yellow
        else:
            color = 'good'  # Green
            
        # Create payload
        payload = {
            "username": config.get('username', 'SentinelIQ'),
            "icon_url": config.get('icon_url', ''),
            "attachments": [{
                "fallback": notification.title,
                "color": color,
                "pretext": config.get('pretext', ''),
                "title": notification.title,
                "text": notification.message,
                "footer": "SentinelIQ Security Platform"
            }]
        }
        
        # Send to Mattermost
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 200:
            return True, None
        else:
            return False, f"Mattermost API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, str(e)


def _send_webhook_notification(channel, notification, recipient) -> Tuple[bool, Optional[str]]:
    """
    Send notification via custom webhook.
    
    Args:
        channel: NotificationChannel instance
        notification: Notification instance
        recipient: User instance
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        config = channel.config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            return False, "No webhook URL configured"
            
        # Prepare payload
        payload = {
            "notification": {
                "id": str(notification.id),
                "title": notification.title,
                "message": notification.message,
                "category": notification.category,
                "priority": notification.priority,
                "created_at": notification.created_at.isoformat() if notification.created_at else None
            },
            "recipient": {
                "id": str(recipient.id),
                "email": recipient.email,
                "username": recipient.username
            },
            "sender": "SentinelIQ",
            "timestamp": timezone.now().isoformat()
        }
        
        # Add custom HTTP headers if specified
        headers = config.get('headers', {})
        
        # Set default content type if not provided
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
            
        # Send webhook request
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        if response.status_code >= 200 and response.status_code < 300:
            return True, None
        else:
            return False, f"Webhook API error: {response.status_code} - {response.text[:100]}"
            
    except Exception as e:
        return False, str(e)
