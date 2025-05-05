"""
Endpoint de teste para logs de auditoria.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from api.core.responses import success_response
from auditlog.models import LogEntry


@extend_schema(
    tags=['Authentication'],
    description='Endpoint de teste para criar um log de auditoria.',
    responses={200: {'type': 'object', 'description': 'Log de auditoria criado com sucesso'}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_audit_log(request):
    """
    Endpoint de teste para criar um log de auditoria.
    
    Cria um log de auditoria para o usuário atual.
    Útil para testar se o sistema de auditoria está funcionando corretamente.
    """
    user = request.user
    
    # Criar log usando django-auditlog diretamente
    LogEntry.objects.log_create(
        None,  # instance
        action=LogEntry.Action.UPDATE,
        changes={
            'test': 'Teste de log de auditoria',
            'method': request.method,
            'path': request.path
        },
        additional_data={
            'entity_type': 'user',
            'entity_name': f'Test audit log for {user.username}',
            'response_status': 200
        }
    )
    
    return success_response(
        message='Audit log created successfully',
        data={'username': user.username}
    ) 