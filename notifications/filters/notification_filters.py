import django_filters
from notifications.models import Notification, NotificationChannel, UserNotificationPreference

class NotificationFilter(django_filters.FilterSet):
    """
    Filter for notifications with advanced filtering options.
    """
    # Date range filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Boolean filters
    read = django_filters.BooleanFilter(method='filter_read')
    
    # Related object filters
    related_to = django_filters.CharFilter(field_name='related_object_type')
    
    class Meta:
        model = Notification
        fields = {
            'category': ['exact', 'in'],
            'priority': ['exact', 'in'],
            'company': ['exact'],
            'is_company_wide': ['exact'],
        }
    
    def filter_read(self, queryset, name, value):
        """
        Filter notifications by read status.
        True = only read notifications
        False = only unread notifications
        """
        user = self.request.user
        
        if value:  # Read notifications
            return queryset.filter(
                delivery_statuses__recipient=user,
                delivery_statuses__read_at__isnull=False
            )
        else:  # Unread notifications
            return queryset.filter(
                delivery_statuses__recipient=user,
                delivery_statuses__read_at__isnull=True
            )

class NotificationChannelFilter(django_filters.FilterSet):
    """
    Filter for notification channels.
    """
    class Meta:
        model = NotificationChannel
        fields = {
            'name': ['exact', 'contains'],
            'channel_type': ['exact', 'in'],
            'is_enabled': ['exact'],
            'company': ['exact'],
        } 