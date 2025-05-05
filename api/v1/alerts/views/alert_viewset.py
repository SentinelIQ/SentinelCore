from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.core.pagination import StandardResultsSetPagination
from api.core.responses import success_response, error_response
from api.core.rbac import HasEntityPermission
from api.core.audit import AuditLogMixin
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from alerts.models import Alert
from api.v1.alerts.serializers import (
    AlertSerializer,
    AlertListSerializer,
    AlertCreateSerializer,
    AlertUpdateSerializer
)
from api.v1.alerts.filters import AlertFilter


class AlertViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """
    API endpoints para gerenciamento de alertas.
    
    Permite criar, atualizar, listar e excluir alertas, além de
    executar ações específicas como escalação e resolução.
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, HasEntityPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AlertFilter
    search_fields = ['title', 'description', 'source', 'severity']
    ordering_fields = ['created_at', 'updated_at', 'severity', 'status']
    ordering = ['-created_at']
    
    # Definir entity_type para RBAC e auditoria
    entity_type = 'alert'
    
    def get_serializer_class(self):
        """
        Retorna o serializer apropriado:
        - AlertCreateSerializer para criação
        - AlertUpdateSerializer para atualização
        - AlertListSerializer para listagem
        - AlertSerializer para outros casos
        """
        if self.action == 'create':
            return AlertCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AlertUpdateSerializer
        elif self.action == 'list':
            return AlertListSerializer
        return AlertSerializer
    
    def get_queryset(self):
        """
        Filtra queryset pelo contexto da requisição:
        - Administradores veem todos os alertas
        - Usuários regulares veem apenas alertas de sua empresa
        """
        queryset = super().get_queryset()
        
        # Filtragem por empresa
        user = self.request.user
        if not user.is_superuser and hasattr(user, 'company') and user.company:
            queryset = queryset.filter(company=user.company)
            
        return queryset
    
    def get_additional_log_data(self, request, obj=None, action=None):
        """
        Personaliza os dados do log de auditoria para alertas,
        incluindo severidade, status e outras informações relevantes.
        """
        # Obter dados base do método pai
        data = super().get_additional_log_data(request, obj, action)
        
        # Adicionar dados específicos de alerta
        if obj:
            data.update({
                'alert_severity': getattr(obj, 'severity', None),
                'alert_status': getattr(obj, 'status', None),
                'alert_source': getattr(obj, 'source', None),
                'company_id': str(obj.company.id) if getattr(obj, 'company', None) else None,
                'company_name': obj.company.name if getattr(obj, 'company', None) else None,
            })
            
        return data
    
    def perform_create(self, serializer):
        """
        Implementa lógica específica para criação de alerta,
        associando automaticamente a empresa do usuário.
        """
        # Associar empresa ao alerta
        if hasattr(self.request.user, 'company') and self.request.user.company:
            serializer.save(company=self.request.user.company)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """
        Escalação do alerta para um incidente.
        
        Esta ação converte um alerta em incidente, 
        preservando todas as informações e observáveis.
        """
        alert = self.get_object()
        
        try:
            # Lógica de escalação (a ser implementada)
            incident = alert.escalate_to_incident()
            
            # Log de auditoria para ação customizada
            LogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(alert.__class__),
                object_pk=str(alert.pk),
                object_repr=str(alert),
                action=LogEntry.Action.UPDATE,
                actor=request.user,
                additional_data={
                    'entity_type': 'alert',
                    'action_type': 'escalate',
                    'alert_severity': alert.severity,
                    'alert_status': alert.status,
                    'incident_id': str(incident.pk) if incident else None,
                    'client_ip': self._get_client_ip(request),
                    'request_method': request.method,
                    'request_path': request.path,
                    'company_id': str(alert.company.id) if alert.company else None,
                    'company_name': alert.company.name if alert.company else None,
                }
            )
            
            return success_response(
                data={'incident_id': incident.id},
                message="Alerta escalado com sucesso para incidente",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return error_response(
                message=f"Falha ao escalar alerta: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Resolução de um alerta.
        
        Esta ação marca o alerta como resolvido e
        registra informações sobre a resolução.
        """
        alert = self.get_object()
        
        try:
            # Lógica de resolução
            resolution_notes = request.data.get('resolution_notes', '')
            alert.resolve(resolution_notes=resolution_notes)
            
            # Log de auditoria para ação customizada
            LogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(alert.__class__),
                object_pk=str(alert.pk),
                object_repr=str(alert),
                action=LogEntry.Action.UPDATE,
                actor=request.user,
                additional_data={
                    'entity_type': 'alert',
                    'action_type': 'resolve',
                    'alert_severity': alert.severity,
                    'alert_status': alert.status,
                    'resolution_notes': resolution_notes,
                    'client_ip': self._get_client_ip(request),
                    'request_method': request.method,
                    'request_path': request.path,
                    'company_id': str(alert.company.id) if alert.company else None,
                    'company_name': alert.company.name if alert.company else None,
                }
            )
            
            return success_response(
                data=AlertSerializer(alert).data,
                message="Alerta resolvido com sucesso",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return error_response(
                message=f"Falha ao resolver alerta: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Atribuição de alerta a um usuário.
        
        Esta ação associa o alerta a um usuário específico
        para análise e tratamento.
        """
        alert = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            # Lógica de atribuição
            alert.assign_to_user(user_id)
            
            # Log de auditoria para ação customizada
            LogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(alert.__class__),
                object_pk=str(alert.pk),
                object_repr=str(alert),
                action=LogEntry.Action.UPDATE,
                actor=request.user,
                additional_data={
                    'entity_type': 'alert',
                    'action_type': 'assign',
                    'alert_severity': alert.severity,
                    'alert_status': alert.status,
                    'assigned_user_id': user_id,
                    'client_ip': self._get_client_ip(request),
                    'request_method': request.method,
                    'request_path': request.path,
                    'company_id': str(alert.company.id) if alert.company else None,
                    'company_name': alert.company.name if alert.company else None,
                }
            )
            
            return success_response(
                data=AlertSerializer(alert).data,
                message="Alerta atribuído com sucesso",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return error_response(
                message=f"Falha ao atribuir alerta: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            ) 