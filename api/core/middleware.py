import time
import json
import logging
from django.utils import timezone
import uuid
from django.conf import settings


logger = logging.getLogger('api.requests')


class RequestLoggingMiddleware:
    """
    Middleware para log detalhado de requisições e respostas da API.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Apenas processar logs para requisições à API
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        start_time = time.time()
        
        # Registrar dados básicos da requisição
        request_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET.items()),
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
        }
        
        # Executar a requisição
        response = self.get_response(request)
        
        # Registrar dados da resposta
        duration = time.time() - start_time
        status_code = getattr(response, 'status_code', 0)
        
        log_data = {
            **request_data,
            'status_code': status_code,
            'duration': f"{duration:.3f}s",
            'success': 200 <= status_code < 400,
        }
        
        # Log de diferentes níveis baseado no status da resposta
        if status_code >= 500:
            logger.error(json.dumps(log_data))
        elif status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
        
        return response


class TenantContextMiddleware:
    """
    Middleware para adicionar o contexto de tenant (company) à requisição.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Adicionar company_id ao request se o usuário estiver autenticado
        # e tiver uma company associada
        if request.user.is_authenticated and hasattr(request.user, 'company') and request.user.company:
            request.company_id = request.user.company.id
            request.company = request.user.company
        else:
            request.company_id = None
            request.company = None
        
        return self.get_response(request)


# Adicione um middleware para integrar o Sentry com o contexto da requisição
class SentryContextMiddleware:
    """
    Middleware que adiciona informações de contexto para o Sentry.
    Captura dados do usuário atual, empresa do tenant e outros metadados.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Inicializar Sentry somente se estiver configurado
        try:
            from sentineliq.sentry import set_user, set_context, set_transaction
            
            # Definir o ID da transação
            transaction_id = str(uuid.uuid4())
            request.transaction_id = transaction_id
            
            # Adicionar informações do usuário
            if request.user and request.user.is_authenticated:
                # Incluir informações de usuário relevantes no Sentry
                set_user({
                    'id': str(request.user.id),
                    'username': request.user.username,
                    'email': request.user.email,
                    'ip_address': self.get_client_ip(request),
                })
                
                # Adicionar informações da empresa (tenant)
                if hasattr(request.user, 'company') and request.user.company:
                    set_context("tenant", {
                        "company_id": str(request.user.company.id),
                        "company_name": request.user.company.name,
                    })
            
            # Definir nome da transação com base na URL
            path = request.path_info.strip('/')
            if path:
                set_transaction(f"{request.method} {path}")
            
            # Adicionar detalhes da requisição
            set_context("request_details", {
                "transaction_id": transaction_id,
                "method": request.method,
                "path": request.path,
                "query_string": request.META.get('QUERY_STRING', ''),
                "user_agent": request.META.get('HTTP_USER_AGENT', 'Unknown'),
                "referer": request.META.get('HTTP_REFERER', ''),
            })
        except ImportError:
            # Sentry não está disponível, ignorar silenciosamente
            pass
        
        # Continuar com a requisição normal
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Extrair o IP real do cliente, considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Pegar o primeiro IP da lista (IP original do cliente)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip 