from django.contrib import admin
from .models import NotificationChannel, Notification, UserNotificationPreference, NotificationDeliveryStatus, NotificationRule

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_type', 'company', 'is_enabled', 'created_at')
    list_filter = ('channel_type', 'is_enabled', 'company')
    search_fields = ('name', 'company__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'channel_type', 'is_enabled', 'company')
        }),
        ('Configuration', {
            'fields': ('config',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'company', 'is_active', 'created_at')
    list_filter = ('event_type', 'is_active', 'company', 'created_at')
    search_fields = ('name', 'description', 'company__name')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('channels',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'event_type', 'is_active', 'company')
        }),
        ('Configuration', {
            'fields': ('conditions', 'message_template', 'channels')
        }),
        ('Custom Event', {
            'fields': ('custom_event_id',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'priority', 'company', 'is_company_wide', 'created_at')
    list_filter = ('category', 'priority', 'company', 'is_company_wide')
    search_fields = ('title', 'message', 'company__name')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('recipients',)
    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'category', 'priority', 'company', 'is_company_wide')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id', 'triggered_by_rule'),
            'classes': ('collapse',),
        }),
        ('Recipients', {
            'fields': ('recipients',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_alerts', 'in_app_alerts', 'slack_alerts', 'mattermost_alerts', 'daily_digest', 'weekly_digest')
    list_filter = ('email_alerts', 'in_app_alerts', 'slack_alerts', 'mattermost_alerts', 'daily_digest', 'weekly_digest')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Email Preferences', {
            'fields': ('email_alerts', 'email_incidents', 'email_tasks', 'email_reports'),
        }),
        ('In-App Preferences', {
            'fields': ('in_app_alerts', 'in_app_incidents', 'in_app_tasks', 'in_app_reports'),
        }),
        ('Slack Preferences', {
            'fields': ('slack_alerts', 'slack_incidents', 'slack_tasks', 'slack_critical_only'),
        }),
        ('Mattermost Preferences', {
            'fields': ('mattermost_alerts', 'mattermost_incidents', 'mattermost_tasks', 'mattermost_critical_only'),
        }),
        ('SMS Preferences', {
            'fields': ('sms_critical_only',),
        }),
        ('Digest Preferences', {
            'fields': ('daily_digest', 'weekly_digest'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(NotificationDeliveryStatus)
class NotificationDeliveryStatusAdmin(admin.ModelAdmin):
    list_display = ('notification', 'channel', 'recipient', 'status', 'sent_at', 'delivered_at', 'read_at')
    list_filter = ('status', 'channel', 'sent_at')
    search_fields = ('notification__title', 'recipient__email', 'channel__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('notification', 'channel', 'recipient', 'status')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'delivered_at', 'read_at'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
