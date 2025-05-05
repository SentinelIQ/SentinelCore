# Guia de Migração de Tarefas Celery

Este documento descreve o processo de migração das tarefas Celery para a nova estrutura centralizada.

## 1. Visão Geral

Estamos migrando todas as tarefas Celery do SentinelIQ para uma estrutura centralizada dentro de `sentineliq/tasks/`. Esta nova estrutura proporciona:

- Organização mais limpa e modular das tarefas
- Configuração padrão para tarefas do mesmo tipo
- Melhor separação por domínio de aplicação
- Registro centralizado de tarefas
- Configuração consistente de filas e comportamento de retry
- Melhor monitoramento e observabilidade

## 2. Nova Estrutura de Diretórios

```
sentineliq/
└── tasks/
    ├── __init__.py                # Registro centralizado de tarefas
    ├── base.py                    # Classes base e decoradores
    ├── alerts/                    # Tarefas de alertas
    │   ├── __init__.py
    │   └── alert_tasks.py
    ├── incidents/                 # Tarefas de incidentes
    │   ├── __init__.py
    │   └── incident_tasks.py
    ├── mitre/                     # Tarefas relacionadas ao MITRE
    │   ├── __init__.py
    │   └── mitre_tasks.py
    ├── notifications/             # Tarefas de notificações
    │   ├── __init__.py
    │   └── notification_tasks.py
    ├── observables/               # Tarefas de observáveis
    │   ├── __init__.py
    │   └── observable_tasks.py
    ├── reporting/                 # Tarefas de relatórios
    │   ├── __init__.py
    │   └── report_tasks.py
    ├── scheduled/                 # Tarefas agendadas
    │   ├── __init__.py
    │   └── periodic_tasks.py
    ├── sentinelvision/            # Tarefas do SentinelVision
    │   ├── __init__.py
    │   ├── feed_tasks.py
    │   ├── enrichment_tasks.py
    │   └── feed_dispatcher.py
    └── system/                    # Tarefas de sistema
        ├── __init__.py
        └── system_tasks.py
```

## 3. Passos para Migração

Para cada arquivo de tarefas (`tasks.py`) no projeto, siga os passos abaixo:

### 3.1. Criar a estrutura de diretórios

```bash
mkdir -p sentineliq/tasks/nome_do_app
```

### 3.2. Criar arquivo __init__.py

Criar um arquivo `__init__.py` no diretório de tarefas que importa todas as tarefas do arquivo principal:

```python
"""
Descrição do módulo de tarefas.
"""

from .nome_do_arquivo_de_tarefas import *

__all__ = [
    'nome_da_tarefa_1',
    'nome_da_tarefa_2',
    # ...
]
```

### 3.3. Criar o arquivo de tarefas

Criar um arquivo para as tarefas específicas do domínio, usando o novo padrão:

```python
"""
Descrição detalhada das tarefas.
"""

import logging
from sentineliq.tasks.base import register_task, BaseTask, DataProcessingTask

# Configurar logger
logger = logging.getLogger('sentineliq.tasks.nome_do_app')


@register_task(
    name='sentineliq.tasks.nome_do_app.nome_da_tarefa',
    queue='sentineliq_soar_setup',  # Escolher a fila apropriada
    base=BaseTask  # Ou outra classe base apropriada
)
def nome_da_tarefa(self, param1, param2=None, **kwargs):
    """
    Descrição da tarefa.
    
    Args:
        param1: Descrição do parâmetro 1
        param2: Descrição do parâmetro 2
        **kwargs: Outros parâmetros
        
    Returns:
        dict: Resultados da tarefa
    """
    # Importar modelos e dependências aqui para evitar importações circulares
    from app.models import Model
    
    logger.info(f"Iniciando tarefa com parâmetros: {param1}, {param2}")
    
    try:
        # Implementação da tarefa
        
        return {
            'status': 'success',
            'resultado': resultado
        }
    except Exception as e:
        logger.exception(f"Erro durante execução da tarefa: {str(e)}")
        
        return {
            'status': 'error',
            'error': str(e)
        }
```

### 3.4. Registrar no arquivo sentineliq/tasks/__init__.py

Abra o arquivo `sentineliq/tasks/__init__.py` e adicione o novo módulo de tarefas ao registro:

```python
TASK_MODULES = [
    # Módulos existentes...
    'sentineliq.tasks.nome_do_app.nome_do_arquivo_de_tarefas',
]
```

### 3.5. Atualizar chamadas de tarefas

Atualize todas as chamadas para a tarefa para usar o novo caminho:

```python
# Antes
from app.tasks import nome_da_tarefa
nome_da_tarefa.delay(param1, param2)

# Depois
from sentineliq.tasks.nome_do_app import nome_da_tarefa
nome_da_tarefa.delay(param1, param2)
```

## 4. Filas Disponíveis

Use a fila apropriada para o tipo de tarefa:

- `sentineliq_soar_setup`: Inicialização, migrações, configuração
- `sentineliq_soar_vision_feed`: Processamento de feeds de inteligência
- `sentineliq_soar_vision_enrichment`: Enriquecimento de contexto
- `sentineliq_soar_vision_analyzer`: Tarefas de análise
- `sentineliq_soar_vision_responder`: Ações de resposta
- `sentineliq_soar_notification`: Notificações e alertas

## 5. Classes Base Disponíveis

Escolha a classe base mais apropriada para o tipo de tarefa:

- `BaseTask`: Classe base genérica para todas as tarefas
- `DataProcessingTask`: Para tarefas que processam dados
- `PeriodicTask`: Para tarefas agendadas periodicamente
- `MaintenanceTask`: Para tarefas de manutenção do sistema

## 6. Módulos Pendentes de Migração

Os seguintes módulos ainda precisam ser migrados:

- [ ] `api/core/tasks.py` → `sentineliq/tasks/core/core_tasks.py`
- [ ] `api/v1/misp_sync/tasks.py` → `sentineliq/tasks/misp_sync/misp_sync_tasks.py`
- [ ] `sentinelvision/tasks.py` → `sentineliq/tasks/sentinelvision/vision_tasks.py`
- [ ] `sentinelvision/tasks/feed_tasks.py` → `sentineliq/tasks/sentinelvision/feed_tasks.py`
- [ ] `sentinelvision/tasks/enrichment_tasks.py` → `sentineliq/tasks/sentinelvision/enrichment_tasks.py`
- [ ] `sentinelvision/tasks/feed_dispatcher.py` → `sentineliq/tasks/sentinelvision/feed_dispatcher.py`
- [ ] `sentinelvision/tasks/task_exports.py` → `sentineliq/tasks/sentinelvision/task_exports.py`

## 7. Módulos Já Migrados

Os seguintes módulos já foram migrados:

- [x] `alerts/tasks.py` → `sentineliq/tasks/alerts/alert_tasks.py`
- [x] `notifications/tasks.py` → `sentineliq/tasks/notifications/notification_tasks.py`
- [x] `mitre/tasks.py` → `sentineliq/tasks/mitre/mitre_tasks.py`

## 8. Testes

Após a migração de cada tarefa, teste-a exaustivamente:

```python
# Via shell do Django
from sentineliq.tasks.nome_do_app import nome_da_tarefa
result = nome_da_tarefa.delay(param1, param2)
print(result.get(timeout=30))  # Obter resultado com timeout
```

## 9. Desativação do Código Antigo

Após a migração completa e testes bem-sucedidos de todas as tarefas, você pode:

1. Adicionar um aviso de descontinuação nas tarefas antigas que redireciona para as novas
2. Gradualmente remover as tarefas antigas em uma versão futura

```python
# Exemplo de aviso de descontinuação
@shared_task
def nome_da_tarefa(*args, **kwargs):
    """
    DEPRECATED: Use sentineliq.tasks.nome_do_app.nome_da_tarefa instead.
    This task will be removed in version X.Y.Z.
    """
    import warnings
    warnings.warn(
        "Task app.tasks.nome_da_tarefa is deprecated. "
        "Use sentineliq.tasks.nome_do_app.nome_da_tarefa instead.",
        DeprecationWarning, stacklevel=2
    )
    from sentineliq.tasks.nome_do_app import nome_da_tarefa
    return nome_da_tarefa.delay(*args, **kwargs)
``` 