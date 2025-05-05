import django_filters
from django.db.models import Q
from api.v1.misp_sync.models import MISPObject
from api.core.filters import get_array_field_filter_overrides


class MISPObjectFilter(django_filters.FilterSet):
    """
    Filter for MISP Object models.
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    meta_category = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    comment = django_filters.CharFilter(lookup_expr='icontains')
    deleted = django_filters.BooleanFilter()
    timestamp_after = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    event_info = django_filters.CharFilter(field_name='event__info', lookup_expr='icontains')
    event_id = django_filters.NumberFilter(field_name='event__id')
    
    class Meta:
        model = MISPObject
        fields = [
            'name', 
            'meta_category', 
            'deleted', 
            'event',
            'event__company',
            'company',
            'misp_id'
        ] 