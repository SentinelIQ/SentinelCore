import django_filters
from django.db.models import Q
from api.v1.misp_sync.models import MISPEvent
from api.core.filters import get_array_field_filter_overrides


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
    has_alert = django_filters.BooleanFilter(field_name='alert', lookup_expr='isnull', exclude=True)
    has_incident = django_filters.BooleanFilter(field_name='incident', lookup_expr='isnull', exclude=True)
    
    def filter_tag(self, queryset, name, value):
        """
        Filter events by tag (case-insensitive).
        """
        return queryset.filter(tags__icontains=value)
    
    class Meta:
        model = MISPEvent
        fields = [
            'info', 
            'org_name', 
            'orgc_name', 
            'threat_level_id', 
            'analysis', 
            'distribution', 
            'published',
            'misp_server', 
            'company',
            'misp_id'
        ]
        filter_overrides = get_array_field_filter_overrides() 