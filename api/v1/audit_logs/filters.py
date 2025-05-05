"""
Filters for the audit logs module.
"""

import django_filters
from django_filters import rest_framework as filters
from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class AuditLogFilter(django_filters.FilterSet):
    """
    Filtro para logs de auditoria.
    
    Permite filtrar logs de auditoria por vários critérios, incluindo:
    - Tipo de entidade
    - Ação realizada
    - ID da entidade
    - Usuário
    - Período de tempo
    - Empresa
    """
    entity_type = filters.CharFilter(field_name='additional_data__entity_type')
    action = filters.NumberFilter(field_name='action')
    entity_id = filters.CharFilter(field_name='object_pk')
    username = filters.CharFilter(field_name='actor__username')
    company_id = filters.CharFilter(field_name='additional_data__company_id')
    
    # Filtros de data
    date_from = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    date_to = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    period = filters.CharFilter(method='filter_by_period')
    
    # Para facilitar a pesquisa
    search = filters.CharFilter(method='search_filter')
    
    class Meta:
        model = LogEntry
        fields = [
            'entity_type', 'action', 'entity_id', 'username', 
            'company_id', 'date_from', 'date_to', 'period'
        ]
    
    def filter_by_period(self, queryset, name, value):
        """
        Filtra logs por um período predefinido.
        
        Períodos suportados:
        - today: hoje
        - yesterday: ontem
        - week: últimos 7 dias
        - month: últimos 30 dias
        - year: últimos 365 dias
        
        Args:
            queryset: Queryset de logs
            name: Nome do campo
            value: Valor do período
            
        Returns:
            QuerySet: Logs filtrados pelo período
        """
        now = timezone.now()
        
        if value == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif value == 'yesterday':
            start_date = (now - relativedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(timestamp__gte=start_date, timestamp__lt=end_date)
        elif value == 'week':
            start_date = now - relativedelta(days=7)
        elif value == 'month':
            start_date = now - relativedelta(months=1)
        elif value == 'year':
            start_date = now - relativedelta(years=1)
        else:
            return queryset
            
        return queryset.filter(timestamp__gte=start_date)
    
    def search_filter(self, queryset, name, value):
        """
        Pesquisa em múltiplos campos.
        
        Busca em:
        - Nome de usuário
        - ID ou representação do objeto
        - Dados adicionais
        
        Args:
            queryset: Queryset de logs
            name: Nome do campo
            value: Termo de pesquisa
            
        Returns:
            QuerySet: Logs que correspondem à pesquisa
        """
        if not value:
            return queryset
            
        return queryset.filter(
            Q(actor__username__icontains=value) |
            Q(object_repr__icontains=value) |
            Q(object_pk__icontains=value) |
            Q(additional_data__icontains=value)
        )
    
    def filter_entity_type(self, queryset, name, value):
        """
        Filter by entity type.
        """
        # First try to filter by entity_type in additional_data
        filtered = queryset.filter(additional_data__entity_type=value)
        if filtered.exists():
            return filtered
        
        # If no results, try to filter by content_type model
        try:
            content_types = ContentType.objects.filter(model__iexact=value)
            if content_types.exists():
                return queryset.filter(content_type__in=content_types)
        except Exception:
            pass
            
        return queryset.none()
    
    def filter_company_id(self, queryset, name, value):
        """
        Filter by company ID.
        """
        # Filter by company_id in additional_data
        return queryset.filter(additional_data__company_id=value)
    
    def filter_company_name(self, queryset, name, value):
        """
        Filter by company name.
        """
        # Filter by company_name in additional_data
        return queryset.filter(additional_data__company_name__icontains=value) 