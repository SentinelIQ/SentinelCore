# 🚀 Celery & Celery Beat: Guia Completo

Este documento fornece instruções detalhadas sobre como usar o Celery e o Celery Beat no projeto SentinelIQ, incluindo práticas recomendadas para criação de tarefas, troubleshooting e monitoramento.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura do Celery](#estrutura-do-celery)
3. [Criação de Tarefas](#criação-de-tarefas)
4. [Agendamento de Tarefas](#agendamento-de-tarefas)
5. [Monitoramento](#monitoramento)
6. [Solução de Problemas](#solução-de-problemas)

## 📝 Visão Geral

O SentinelIQ usa Celery e Celery Beat para:

- Executar tarefas assíncronas de longa duração
- Agendar tarefas periódicas
- Garantir que operações intensivas não bloqueiem solicitações API
- Processar feeds de inteligência de ameaças em segundo plano
- Executar sincronizações com o framework MITRE ATT&CK

## 🏗️ Estrutura do Celery

### Arquivos Principais

- `sentineliq/celery.py`: Configuração principal do aplicativo Celery
- `sentineliq/settings.py`: Configurações relacionadas ao Celery (CELERY_*)
- `api/core/tasks.py`: Tarefas centrais do sistema
- `[app]/tasks.py`: Tarefas específicas de cada aplicativo

### Filas

O sistema usa várias filas para diferentes tipos de tarefas:

- `default`: Tarefas gerais do sistema
- `feeds`: Processamento de feeds de inteligência
- `observables`: Enriquecimento de observáveis
- `notifications`: Envio de notificações

## 🛠️ Criação de Tarefas

### Template para Novas Tarefas

```python
from celery import shared_task
import logging

logger = logging.getLogger('app_name.tasks')

@shared_task(
    name="app_name.tasks.task_name",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    acks_late=True
)
def task_name(self, param1, param2=None):
    """Descrição da tarefa"""
    task_id = self.request.id
    logger.info(f"Iniciando tarefa {task_id}")
    
    try:
        # Implementação da tarefa
        result = "resultado"
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Erro na tarefa {task_id}: {str(e)}")
        raise
```

### Práticas Recomendadas

1. **Sempre use o decorador `@shared_task`** para garantir que a tarefa seja registrada corretamente
2. **Sempre defina um nome explícito** usando o formato `app_name.tasks.task_name`
3. **Use `bind=True`** para acessar informações de contexto da tarefa
4. **Configure retry automático** para falhas temporárias
5. **Use `acks_late=True`** para garantir que a tarefa só seja reconhecida após conclusão bem-sucedida
6. **Sempre registre o início e o fim** da tarefa usando o logger
7. **Retorne um dicionário com um status claro** e dados relevantes

## ⏰ Agendamento de Tarefas

### Via Settings.py

Para tarefas que fazem parte do código base e devem ser sempre agendadas:

```python
# Em settings.py
CELERY_BEAT_SCHEDULE = {
    'task-name': {
        'task': 'app_name.tasks.task_name',
        'schedule': timedelta(hours=1),
        'kwargs': {'param1': 'value1'},
        'options': {'queue': 'queue_name'}
    },
}
```

### Via Django Admin

Para tarefas que precisam ser configuradas dinamicamente:

1. Acesse o Django Admin em `/admin/django_celery_beat/`
2. Crie uma nova Tarefa Periódica (Periodic Task)
3. Selecione a tarefa registrada na lista suspensa
4. Configure o intervalo ou crontab para execução
5. Adicione argumentos como JSON se necessário

## 📊 Monitoramento

### Flower

O Flower está disponível em `http://localhost:5555` com credenciais:
- Usuário: admin
- Senha: admin

Recursos do Flower:
- Visualizar tarefas ativas, bem-sucedidas e com falha
- Inspecionar detalhes de tarefas específicas
- Monitorar workers e filas

### Logging

Os logs do Celery são armazenados em:
- `/logs/celery.log`: Logs específicos do Celery
- `/logs/api.log`: Logs de aplicação (incluindo execução de tarefas)
- `/logs/error.log`: Erros em todas as tarefas

## 🔧 Solução de Problemas

### Tarefa Não Executada

Verifique:
1. Se a tarefa está registrada: `docker compose exec celery_worker celery -A sentineliq inspect registered`
2. Se há workers disponíveis: `docker compose exec celery_worker celery -A sentineliq status`
3. Os logs para erros: `docker compose logs celery_worker`

### Tarefa Agendada Não Executada

Verifique:
1. Se o Celery Beat está em execução: `docker compose ps`
2. O status do agendador: `docker compose logs celery_beat`
3. Se a tarefa existe no banco de dados: `docker compose exec web python manage.py shell -c "from django_celery_beat.models import PeriodicTask; print(PeriodicTask.objects.all())"`

### Executar Uma Tarefa Manualmente

```bash
docker compose exec celery_worker celery -A sentineliq call app_name.tasks.task_name
```

### Reiniciar Serviços

```bash
docker compose restart celery_worker celery_beat
```

## ✅ Lista de Verificação para Novas Tarefas

- [ ] A tarefa usa o decorador `@shared_task`
- [ ] A tarefa tem um nome explícito (namespace)
- [ ] A tarefa tem configurações de retry
- [ ] A tarefa usa logging adequado
- [ ] A tarefa trata exceções corretamente
- [ ] A tarefa retorna um resultado estruturado
- [ ] A tarefa está documentada com docstrings
- [ ] A tarefa é isolada por inquilino (tenant) quando aplicável
- [ ] A tarefa implementa medidas de segurança (RBAC) quando aplicável 