"""
Middleware para registro automático de operações críticas no sistema de auditoria.
"""

import logging
import json
import re
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import AuditLog

logger = logging.getLogger('audit')


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware para registro automático de operações críticas no sistema de auditoria.
    
    Este middleware captura todas as requisições que correspondem aos padrões críticos
    e registra as informações no sistema de auditoria.
    """
    
    # Lista de padrões de URLs que devem ser auditadas automaticamente
    AUDIT_PATTERNS = [
        # Alert endpoints
        r'^/api/v1/alerts/(?P<id>[^/]+)/escalate/$',  # Escalation
        r'^/api/v1/alerts/ingest/$',                  # Ingestion
        
        # Incident endpoints
        r'^/api/v1/incidents/(?P<id>[^/]+)/assign/$',         # Assignment
        r'^/api/v1/incidents/(?P<id>[^/]+)/close-incident/$', # Closing
        
        # Task endpoints
        r'^/api/v1/tasks/(?P<id>[^/]+)/complete/$',   # Task completion
        
        # Observable endpoints
        r'^/api/v1/observables/(?P<id>[^/]+)/mark-as-ioc/$', # Mark as IOC
        
        # Company management
        r'^/api/v1/companies/(?P<id>[^/]+)/deactivate-users/$', # User deactivation
        
        # Authentication
        r'^/api/v1/auth/token/$',      # Login
        r'^/api/token/$',              # Login (legacy)
    ]
    
    # Mapeamento entre patterns e ações
    PATTERN_TO_ACTION = {
        r'escalate': 'escalate',
        r'ingest': 'ingest',
        r'assign': 'assign',
        r'close-incident': 'close',
        r'complete': 'complete',
        r'mark-as-ioc': 'mark_as_ioc',
        r'deactivate-users': 'deactivate_users',
        r'token': 'login'
    }
    
    # Mapeamento entre patterns e tipos de entidade
    PATTERN_TO_ENTITY = {
        r'^/api/v1/alerts/': 'alert',
        r'^/api/v1/incidents/': 'incident',
        r'^/api/v1/tasks/': 'task',
        r'^/api/v1/observables/': 'observable',
        r'^/api/v1/companies/': 'company',
        r'^/api/v1/auth/': 'user',
        r'^/api/token/': 'user'
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Processamento antes de enviar a request para a view
        
        # Adicionamos algumas informações à request para usar depois
        request.audit_log_start_time = None
        request.audit_log_should_log = False
        request.audit_log_entity_type = None
        request.audit_log_entity_id = None
        request.audit_log_action = None
        
        # Verificar se essa URL deve ser auditada
        path = request.path
        
        for pattern in self.AUDIT_PATTERNS:
            match = re.match(pattern, path)
            if match:
                request.audit_log_should_log = True
                
                # Extrair entity_id se disponível
                if 'id' in match.groupdict():
                    request.audit_log_entity_id = match.groupdict()['id']
                
                # Determinar ação
                for action_pattern, action in self.PATTERN_TO_ACTION.items():
                    if re.search(action_pattern, path):
                        request.audit_log_action = action
                        break
                
                # Determinar tipo de entidade
                for entity_pattern, entity_type in self.PATTERN_TO_ENTITY.items():
                    if re.match(entity_pattern, path):
                        request.audit_log_entity_type = entity_type
                        break
                
                break
        
        # Se for um POST, PUT ou PATCH em qualquer endpoint da API, também auditamos
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and path.startswith('/api/v1/'):
            request.audit_log_should_log = True
            
            # Se ainda não temos ação, determinamos pelo método HTTP
            if not request.audit_log_action:
                if request.method == 'POST':
                    request.audit_log_action = 'create'
                elif request.method in ['PUT', 'PATCH']:
                    request.audit_log_action = 'update'
                elif request.method == 'DELETE':
                    request.audit_log_action = 'delete'
            
            # Se ainda não temos tipo de entidade, tentamos determinar pela URL
            if not request.audit_log_entity_type:
                url_parts = path.strip('/').split('/')
                if len(url_parts) >= 3:
                    # '/api/v1/alerts/' -> 'alert'
                    entity_part = url_parts[2]
                    if entity_part.endswith('s'):
                        entity_part = entity_part[:-1]  # Remove o 's' do plural
                    request.audit_log_entity_type = entity_part
        
        # Enviamos a request para as views
        response = self.get_response(request)
        
        # Processamento após a resposta das views
        if request.audit_log_should_log:
            try:
                # Determinamos se a ação foi um sucesso
                is_success = 200 <= response.status_code < 400
                
                # Extraímos o nome da entidade se possível
                entity_name = None
                if hasattr(response, 'data') and isinstance(response.data, dict):
                    if 'data' in response.data and isinstance(response.data['data'], dict):
                        if 'title' in response.data['data']:
                            entity_name = response.data['data']['title']
                        elif 'name' in response.data['data']:
                            entity_name = response.data['data']['name']
                
                # Extraímos qualquer mensagem de erro
                error_message = None
                if not is_success and hasattr(response, 'data') and isinstance(response.data, dict):
                    if 'message' in response.data:
                        error_message = response.data['message']
                
                # Registramos no log de auditoria
                user = request.user if hasattr(request, 'user') else None
                
                AuditLog.log_action(
                    user=user,
                    action=request.audit_log_action or 'other',
                    entity_type=request.audit_log_entity_type or 'other',
                    entity_id=request.audit_log_entity_id,
                    entity_name=entity_name,
                    request=request,
                    response_status=response.status_code,
                    is_success=is_success,
                    error_message=error_message
                )
                
            except Exception as e:
                # Não deixamos que erros no registro de auditoria impeçam a resposta
                logger.error(f"Error in audit logging: {str(e)}")
        
        return response 