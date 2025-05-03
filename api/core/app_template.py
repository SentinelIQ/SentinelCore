"""
Template de código para tasks.py em novos apps Django

Este arquivo serve como um template para implementação de tarefas Celery
em módulos Django seguindo os padrões da aplicação SentinelIQ.

Copie e adapte esse código para novos apps.
"""

import logging
from celery import shared_task
from django.conf import settings

# Sempre use um logger específico para o app
logger = logging.getLogger('nome_do_app.tasks')


@shared_task(
    # Sempre use um nome específico e consistente para a tarefa
    name="nome_do_app.tasks.nome_da_tarefa",
    # Vincule a tarefa para ter acesso a informações de contexto
    bind=True,
    # Configure retry automático para exceções específicas
    autoretry_for=(Exception,),
    # Configuração de retry: máximo de tentativas e tempo entre tentativas
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    # Só confirma a tarefa após execução bem-sucedida
    acks_late=True,
    # Rastreia quando a tarefa começou (útil para monitoramento)
    track_started=True,
    # Rate limit opcional por tarefa
    rate_limit='10/m'
)
def exemplo_tarefa(self, param1, param2=None):
    """
    Exemplo de tarefa Celery com boas práticas.
    
    Args:
        self: Referência à tarefa (disponível por causa de bind=True)
        param1: Parâmetro obrigatório
        param2: Parâmetro opcional
        
    Returns:
        dict: Dicionário com resultados da tarefa
        
    Raises:
        Exception: Se a tarefa falhar, permitindo retry automático
    """
    # Sempre use logging detalhado em tarefas
    task_id = self.request.id
    logger.info(f"Iniciando tarefa {self.name} (ID: {task_id}) com parâmetros: param1={param1}, param2={param2}")
    
    try:
        # Implemente a lógica da tarefa aqui
        resultado = f"Processado: {param1}"
        
        # Sempre registre o resultado
        logger.info(f"Tarefa {task_id} concluída com sucesso: {resultado}")
        
        # Sempre retorne um dicionário com informações úteis
        return {
            "status": "success",
            "task_id": task_id,
            "result": resultado,
            "params": {
                "param1": param1,
                "param2": param2
            }
        }
        
    except Exception as e:
        # Capture e registre exceções, mas propague-as para permitir retry
        logger.error(f"Erro na tarefa {task_id}: {str(e)}")
        
        # Se quiser tentar novamente com outros parâmetros em retry:
        # raise self.retry(exc=e, countdown=60, kwargs={'param1': 'novo_valor'})
        
        # Ou simplesmente propague a exceção para usar o retry padrão
        raise 