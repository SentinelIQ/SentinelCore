import django_filters
from django.db.models import Q
from api.v1.misp_sync.models import MISPServer, MISPEvent, MISPAttribute
from api.core.filters import get_array_field_filter_overrides


class MISPServerFilter(django_filters.FilterSet):
    """
    Filter for MISP Server models.
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    url = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    last_sync_after = django_filters.DateTimeFilter(field_name='last_sync', lookup_expr='gte')
    last_sync_before = django_filters.DateTimeFilter(field_name='last_sync', lookup_expr='lte')
    
    class Meta:
        model = MISPServer
        fields = ['name', 'url', 'is_active', 'company']


class MISPEventFilter(django_filters.FilterSet):
    """
    Filter for MISP Event models with support for tag filtering.
    """
    info = django_filters.CharFilter(lookup_expr='icontains')
    org_name = django_filters.CharFilter(lookup_expr='icontains')
    orgc_name = django_filters.CharFilter(lookup_expr='icontains')
    date_after = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_before = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    timestamp_after = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    tag = django_filters.CharFilter(method='filter_tag')
    threat_level_id = django_filters.NumberFilter()
    analysis = django_filters.NumberFilter()
    distribution = django_filters.NumberFilter()
    published = django_filters.BooleanFilter()
    
    def filter_tag(self, queryset, name, value):
        """
        Filter events by tag (case-insensitive).
        """
        return queryset.filter(tags__icontains=value)
    
    class Meta:
        model = MISPEvent
        fields = [
            'info', 'org_name', 'orgc_name', 
            'threat_level_id', 'analysis', 'distribution', 'published',
            'misp_server', 'company'
        ]
        filter_overrides = get_array_field_filter_overrides()


class MISPAttributeFilter(django_filters.FilterSet):
    """
    Filter for MISP Attribute models with support for tag and value filtering.
    """
    type = django_filters.CharFilter(lookup_expr='exact')
    category = django_filters.CharFilter(lookup_expr='exact')
    value = django_filters.CharFilter(lookup_expr='icontains')
    value_exact = django_filters.CharFilter(field_name='value', lookup_expr='exact')
    comment = django_filters.CharFilter(lookup_expr='icontains')
    tag = django_filters.CharFilter(method='filter_tag')
    to_ids = django_filters.BooleanFilter()
    distribution = django_filters.NumberFilter()
    timestamp_after = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    event_info = django_filters.CharFilter(field_name='event__info', lookup_expr='icontains')
    
    def filter_tag(self, queryset, name, value):
        """
        Filter attributes by tag (case-insensitive).
        """
        return queryset.filter(tags__icontains=value)
    
    class Meta:
        model = MISPAttribute
        fields = [
            'type', 'category', 'value', 'to_ids', 
            'distribution', 'event', 'event__company'
        ]
        filter_overrides = get_array_field_filter_overrides() 