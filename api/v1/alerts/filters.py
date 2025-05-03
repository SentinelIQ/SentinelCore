from django_filters import rest_framework as filters
from alerts.models import Alert
from api.v1.alerts.enums import AlertSeverityEnum, AlertStatusEnum, AlertTLPEnum, AlertPAPEnum
from api.core.utils.enum_utils import enum_to_choices


class AlertFilter(filters.FilterSet):
    """
    Filters for the Alert model.
    """
    # Text filters
    title = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    source = filters.CharFilter(lookup_expr='icontains')
    source_ref = filters.CharFilter(lookup_expr='icontains')
    
    # Exact filters
    severity = filters.ChoiceFilter(choices=enum_to_choices(AlertSeverityEnum))
    status = filters.ChoiceFilter(choices=enum_to_choices(AlertStatusEnum))
    tlp = filters.NumberFilter()
    pap = filters.NumberFilter()
    
    # Tag filters
    has_tag = filters.CharFilter(field_name='tags', method='filter_has_tag')
    
    # Range filters
    date_after = filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_before = filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    class Meta:
        model = Alert
        fields = [
            'title', 'description', 'severity', 'source', 'source_ref', 'status',
            'tlp', 'pap', 'has_tag', 'date_after', 'date_before',
            'created_after', 'created_before', 'updated_after', 'updated_before'
        ]
    
    def filter_has_tag(self, queryset, name, value):
        """
        Filters alerts that contain the specified tag.
        """
        return queryset.filter(tags__contains=[value]) 