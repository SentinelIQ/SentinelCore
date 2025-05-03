from django_filters import rest_framework as filters
from incidents.models import Incident
from api.v1.incidents.enums import IncidentSeverityEnum, IncidentStatusEnum, IncidentTLPEnum, IncidentPAPEnum
from api.core.utils.enum_utils import enum_to_choices


class IncidentFilter(filters.FilterSet):
    """
    Filters for the Incident model.
    """
    # Text filters
    title = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    
    # Exact filters
    severity = filters.ChoiceFilter(choices=enum_to_choices(IncidentSeverityEnum))
    status = filters.ChoiceFilter(choices=enum_to_choices(IncidentStatusEnum))
    tlp = filters.NumberFilter()
    pap = filters.NumberFilter()
    
    # Tag filters
    has_tag = filters.CharFilter(field_name='tags', method='filter_has_tag')
    
    # Filter for related alerts
    has_alerts = filters.BooleanFilter(method='filter_has_alerts')
    
    # Range filters
    start_date_after = filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    start_date_before = filters.DateTimeFilter(field_name='start_date', lookup_expr='lte')
    end_date_after = filters.DateTimeFilter(field_name='end_date', lookup_expr='gte')
    end_date_before = filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    class Meta:
        model = Incident
        fields = [
            'title', 'description', 'severity', 'status', 'tlp', 'pap',
            'has_tag', 'has_alerts', 'start_date_after', 'start_date_before',
            'end_date_after', 'end_date_before', 'created_after', 
            'created_before', 'updated_after', 'updated_before'
        ]
    
    def filter_has_alerts(self, queryset, name, value):
        """
        Filters incidents that have or don't have related alerts.
        """
        if value:
            return queryset.filter(related_alerts__isnull=False).distinct()
        else:
            return queryset.filter(related_alerts__isnull=True)
    
    def filter_has_tag(self, queryset, name, value):
        """
        Filters incidents that contain the specified tag.
        """
        return queryset.filter(tags__contains=[value]) 