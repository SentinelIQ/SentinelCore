from django.db import models
from django.conf import settings
from companies.models import Company
from api.core.models import CoreModel

class NotificationChannel(CoreModel):
    """
    Represents a notification delivery channel such as email, Slack, webhooks, etc.
    """
    CHANNEL_TYPE_CHOICES = (
        ('email', 'Email'),
        ('slack', 'Slack'),
        ('mattermost', 'Mattermost'),
        ('webhook', 'Webhook'),
        ('in_app', 'In-App'),
        ('sms', 'SMS'),
    )
    
    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPE_CHOICES)
    is_enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='notification_channels')
    
    class Meta:
        verbose_name = 'Notification Channel'
        verbose_name_plural = 'Notification Channels'
        unique_together = ['name', 'company']
        
    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"


class NotificationRule(CoreModel):
    """
    Rules for triggering notifications based on system events.
    """
    EVENT_TYPE_CHOICES = (
        ('alert_created', 'Alert Created'),
        ('alert_updated', 'Alert Updated'),
        ('alert_escalated', 'Alert Escalated to Incident'),
        ('incident_created', 'Incident Created'),
        ('incident_updated', 'Incident Updated'),
        ('incident_closed', 'Incident Closed'),
        ('task_created', 'Task Created'),
        ('task_updated', 'Task Updated'),
        ('task_completed', 'Task Completed'),
        ('custom', 'Custom Event'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    
    # Conditions for rule to trigger (stored as JSON)
    conditions = models.JSONField(default=dict, blank=True, help_text="Conditions that must be met for the rule to trigger")
    
    # Action details
    channels = models.ManyToManyField(NotificationChannel, related_name='rules')
    message_template = models.TextField(help_text="Template for notification message. Use {{variables}} for dynamic content.")
    
    # For custom events
    custom_event_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID for custom event types")
    
    # Multi-tenancy
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='notification_rules')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, related_name='created_notification_rules')
    
    class Meta:
        verbose_name = 'Notification Rule'
        verbose_name_plural = 'Notification Rules'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()})"


class Notification(CoreModel):
    """
    Represents a notification sent to users.
    """
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    CATEGORY_CHOICES = (
        ('alert', 'Alert'),
        ('incident', 'Incident'),
        ('task', 'Task'),
        ('system', 'System'),
        ('report', 'Report'),
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Optional related objects
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.IntegerField(blank=True, null=True)
    
    # Optional reference to the rule that triggered this notification
    triggered_by_rule = models.ForeignKey(NotificationRule, on_delete=models.SET_NULL, 
                                         null=True, blank=True, related_name='triggered_notifications')
    
    # Multi-tenancy
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='notifications')
    
    # Recipients - can be sent to specific users or all users in a company
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='notifications', blank=True)
    is_company_wide = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title


class UserNotificationPreference(CoreModel):
    """
    User preferences for receiving notifications through different channels.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email notification preferences
    email_alerts = models.BooleanField(default=True)
    email_incidents = models.BooleanField(default=True)
    email_tasks = models.BooleanField(default=True)
    email_reports = models.BooleanField(default=True)
    
    # In-app notification preferences
    in_app_alerts = models.BooleanField(default=True)
    in_app_incidents = models.BooleanField(default=True)
    in_app_tasks = models.BooleanField(default=True)
    in_app_reports = models.BooleanField(default=True)
    
    # Slack notification preferences (if enabled)
    slack_alerts = models.BooleanField(default=False)
    slack_incidents = models.BooleanField(default=False)
    slack_tasks = models.BooleanField(default=False)
    slack_critical_only = models.BooleanField(default=True)
    
    # Mattermost notification preferences (if enabled)
    mattermost_alerts = models.BooleanField(default=False)
    mattermost_incidents = models.BooleanField(default=False)
    mattermost_tasks = models.BooleanField(default=False)
    mattermost_critical_only = models.BooleanField(default=True)
    
    # SMS notification preferences (if enabled)
    sms_critical_only = models.BooleanField(default=True)
    
    # Notification digests
    daily_digest = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'User Notification Preference'
        verbose_name_plural = 'User Notification Preferences'
        
    def __str__(self):
        return f"Notification preferences for {self.user.email}"


class NotificationDeliveryStatus(CoreModel):
    """
    Tracks the delivery status of notifications through various channels.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    )
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='delivery_statuses')
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE, related_name='delivery_statuses')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_deliveries')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    # Tracking timestamps
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Notification Delivery Status'
        verbose_name_plural = 'Notification Delivery Statuses'
        unique_together = ['notification', 'channel', 'recipient']
        
    def __str__(self):
        return f"Notification to {self.recipient.email} via {self.channel.name}: {self.status}"
