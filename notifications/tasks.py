import logging
from datetime import datetime
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from .models import NotificationChannel, Notification, NotificationDeliveryStatus

User = get_user_model()
logger = logging.getLogger('api.notifications')


@shared_task(
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    acks_late=True
)
def send_notification(notification_id, channel_id, recipient_id=None):
    """
    Celery task to send a notification through a specific channel to a recipient.
    
    Args:
        notification_id: ID of the notification to send
        channel_id: ID of the channel to use for delivery
        recipient_id: ID of the recipient user (optional)
    """
    try:
        # Get the notification, channel and recipient
        notification = Notification.objects.get(id=notification_id)
        channel = NotificationChannel.objects.get(id=channel_id)
        recipient = User.objects.get(id=recipient_id) if recipient_id else None
        
        # If no recipient specified and notification is company-wide,
        # Send to all users in the company
        if not recipient and notification.is_company_wide:
            company_users = User.objects.filter(company=notification.company)
            for user in company_users:
                # Create separate delivery status for each user
                send_notification.delay(notification_id, channel_id, user.id)
            return
        
        if not recipient:
            logger.error(f"No recipient specified for notification {notification_id}")
            return
        
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
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {str(e)}")
        raise  # Re-raise for Celery retry mechanism


@shared_task
def send_test_notification(channel_id, message="This is a test notification from SentinelIQ."):
    """
    Send a test notification through a specific channel.
    
    Args:
        channel_id: ID of the channel to test
        message: Custom test message
    """
    try:
        channel = NotificationChannel.objects.get(id=channel_id)
        
        # Create a test notification object temporarily (won't be saved)
        test_notification = Notification(
            title="Test Notification",
            message=message,
            category="system",
            priority="medium",
            company=channel.company
        )
        
        success = False
        error_message = None
        
        # Get first admin user from the company for testing
        test_recipient = User.objects.filter(
            company=channel.company, 
            is_active=True
        ).first()
        
        if not test_recipient:
            return False, "No active users found for testing"
        
        if channel.channel_type == 'email':
            success, error_message = _send_email_notification(channel, test_notification, test_recipient)
        elif channel.channel_type == 'slack':
            success, error_message = _send_slack_notification(channel, test_notification, test_recipient)
        elif channel.channel_type == 'mattermost':
            success, error_message = _send_mattermost_notification(channel, test_notification, test_recipient)
        elif channel.channel_type == 'webhook':
            success, error_message = _send_webhook_notification(channel, test_notification, test_recipient)
        elif channel.channel_type == 'in_app':
            # No actual sending for in-app test
            success = True
        else:
            error_message = f"Unsupported channel type: {channel.channel_type}"
            
        logger.info(
            f"Test notification sent via {channel.name} ({channel.channel_type}): "
            f"{'Success' if success else f'Failed: {error_message}'}"
        )
        
        return success, error_message
        
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return False, str(e)


def _send_email_notification(channel, notification, recipient):
    """Send notification via email"""
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


def _send_slack_notification(channel, notification, recipient):
    """Send notification via Slack"""
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


def _send_mattermost_notification(channel, notification, recipient):
    """Send notification via Mattermost"""
    try:
        config = channel.config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            return False, "No webhook URL configured for Mattermost channel"
        
        # Get recipient notification preferences (if available)
        try:
            preferences = recipient.notification_preferences
            
            # Check if recipient wants to receive this type of notification via Mattermost
            if notification.category == 'alert' and not preferences.mattermost_alerts:
                return True, "Skipped: Recipient has disabled Mattermost alerts"
            elif notification.category == 'incident' and not preferences.mattermost_incidents:
                return True, "Skipped: Recipient has disabled Mattermost incidents"
            elif notification.category == 'task' and not preferences.mattermost_tasks:
                return True, "Skipped: Recipient has disabled Mattermost tasks"
                
            # Check for critical-only setting
            if preferences.mattermost_critical_only and notification.priority != 'critical':
                return True, "Skipped: Recipient only wants critical notifications via Mattermost"
                
        except ObjectDoesNotExist:
            # If preferences don't exist, proceed with default behavior
            pass
            
        # Determine color based on priority
        color = _get_color_for_priority(notification.priority)
            
        # Prepare payload with rich formatting
        payload = {
            "text": f"### {notification.title}",
            "username": config.get('username', 'SentinelIQ Bot'),
            "icon_url": config.get('icon_url'),
            "channel": config.get('channel'),
            "props": {
                "attachments": [{
                    "pretext": f"New {notification.category.title()}: {notification.title}",
                    "text": notification.message,
                    "color": color,
                    "fields": [
                        {
                            "short": True,
                            "title": "Priority",
                            "value": notification.priority.title()
                        },
                        {
                            "short": True,
                            "title": "Category",
                            "value": notification.category.title()
                        }
                    ]
                }]
            }
        }
        
        # Add related object info if available
        if notification.related_object_type and notification.related_object_id:
            object_type = notification.related_object_type.title()
            object_id = notification.related_object_id
            
            # Add field for related object
            payload["props"]["attachments"][0]["fields"].append({
                "short": True,
                "title": f"{object_type} ID",
                "value": str(object_id)
            })
            
            # Add action button if configured
            if config.get('include_actions', True):
                base_url = config.get('app_base_url')
                if base_url:
                    object_url = f"{base_url.rstrip('/')}/{notification.related_object_type}s/{object_id}"
                    
                    payload["props"]["attachments"][0]["actions"] = [{
                        "name": f"View {object_type}",
                        "integration": {
                            "url": object_url,
                            "context": {
                                "action": "view"
                            }
                        }
                    }]
        
        # Send to Mattermost
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add custom headers if specified
        if 'headers' in config:
            headers.update(config['headers'])
            
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        if response.status_code in range(200, 300):
            return True, None
        else:
            return False, f"Mattermost API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, str(e)


def _send_webhook_notification(channel, notification, recipient):
    """Send notification via webhook"""
    try:
        config = channel.config
        webhook_url = config.get('url')
        
        if not webhook_url:
            return False, "No URL configured for webhook channel"
            
        # Prepare payload
        payload = {
            "title": notification.title,
            "message": notification.message,
            "category": notification.category,
            "priority": notification.priority,
            "timestamp": timezone.now().isoformat(),
            "recipient": {
                "id": str(recipient.id),
                "email": recipient.email,
                "username": recipient.username
            }
        }
        
        # Add additional fields if configured
        if config.get('include_company', False) and hasattr(notification, 'company'):
            payload["company"] = {
                "id": str(notification.company.id),
                "name": notification.company.name
            }
            
        # Add headers if configured
        headers = {}
        if 'headers' in config:
            headers.update(config['headers'])
            
        # Send webhook
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        # Check response
        if response.status_code >= 200 and response.status_code < 300:
            return True, None
        else:
            return False, f"HTTP error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, str(e)


def _get_color_for_priority(priority):
    """Get color code based on notification priority"""
    color_map = {
        'low': '#CCCCCC',       # Gray
        'medium': '#FFCC00',    # Yellow
        'high': '#FF9900',      # Orange
        'critical': '#CC0000',  # Red
    }
    return color_map.get(priority, '#3366FF')  # Default blue 