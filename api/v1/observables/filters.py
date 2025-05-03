from django_filters import rest_framework as filters
from observables.models import Observable
from api.v1.observables.enums import ObservableTypeEnum, ObservableCategoryEnum, ObservableTLPEnum
from api.core.utils.enum_utils import enum_to_choices


class ObservableFilter(filters.FilterSet):
    """
    Filters for the Observable model.
    """
    # Text filters
    value = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    source = filters.CharFilter(lookup_expr='icontains')
    
    # Exact filters
    type = filters.ChoiceFilter(choices=enum_to_choices(ObservableTypeEnum))
    category = filters.ChoiceFilter(choices=enum_to_choices(ObservableCategoryEnum))
    tlp = filters.NumberFilter()
    
    # Tag filters
    has_tag = filters.CharFilter(field_name='tags', method='filter_has_tag')
    
    # Boolean filters
    is_ioc = filters.BooleanFilter()
    is_false_positive = filters.BooleanFilter()
    
    # Range filters
    confidence_min = filters.NumberFilter(field_name='confidence', lookup_expr='gte')
    confidence_max = filters.NumberFilter(field_name='confidence', lookup_expr='lte')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Relationship filters
    has_alert = filters.BooleanFilter(method='filter_has_alert')
    has_incident = filters.BooleanFilter(method='filter_has_incident')
    
    class Meta:
        model = Observable
        fields = [
            'value', 'description', 'type', 'category', 'tlp', 'source',
            'is_ioc', 'is_false_positive', 'has_tag', 'confidence_min', 
            'confidence_max', 'created_after', 'created_before', 
            'updated_after', 'updated_before', 'has_alert', 'has_incident'
        ]
    
    def filter_has_tag(self, queryset, name, value):
        """
        Filters observables that contain the specified tag.
        """
        return queryset.filter(tags__contains=[value])
    
    def filter_has_alert(self, queryset, name, value):
        """
        Filters observables that are linked to an alert.
        """
        if value:
            return queryset.filter(alert__isnull=False)
        else:
            return queryset.filter(alert__isnull=True)
    
    def filter_has_incident(self, queryset, name, value):
        """
        Filters observables that are linked to an incident.
        """
        if value:
            return queryset.filter(incident__isnull=False)
        else:
            return queryset.filter(incident__isnull=True) 