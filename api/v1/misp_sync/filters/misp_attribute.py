import django_filters
from django.db.models import Q
from api.v1.misp_sync.models import MISPAttribute
from api.core.filters import get_array_field_filter_overrides


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
    event_id = django_filters.NumberFilter(field_name='event__id')
    
    def filter_tag(self, queryset, name, value):
        """
        Filter attributes by tag (case-insensitive).
        """
        return queryset.filter(tags__icontains=value)
    
    class Meta:
        model = MISPAttribute
        fields = [
            'type', 
            'category', 
            'value', 
            'to_ids', 
            'distribution', 
            'event',
            'event__company',
            'company'
        ]
        filter_overrides = get_array_field_filter_overrides() 