from django_filters import rest_framework as filters
from companies.models import Company


class CompanyFilter(filters.FilterSet):
    """
    Filtros para o modelo Company.
    """
    # Filtros básicos
    name = filters.CharFilter(lookup_expr='icontains')
    
    # Filtros com faixa de valores
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    class Meta:
        model = Company
        fields = [
            'name',
            'created_after', 'created_before',
            'updated_after', 'updated_before'
        ] 