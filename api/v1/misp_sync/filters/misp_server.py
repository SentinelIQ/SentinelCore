import django_filters
from django.db.models import Q
from api.v1.misp_sync.models import MISPServer


class MISPServerFilter(django_filters.FilterSet):
    """
    Filter for MISP Server models.
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    url = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    last_sync_after = django_filters.DateTimeFilter(field_name='last_sync', lookup_expr='gte')
    last_sync_before = django_filters.DateTimeFilter(field_name='last_sync', lookup_expr='lte')
    
    class Meta:
        model = MISPServer
        fields = [
            'name', 
            'url', 
            'is_active',
            'company',
            'sync_interval_hours',
            'created_by'
        ] 