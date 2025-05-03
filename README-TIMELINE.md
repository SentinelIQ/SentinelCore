# Sistema de Timeline para Incidentes

Este sistema foi implementado para registrar todas as ações e alterações que ocorrem em um incidente, proporcionando um histórico completo e auditável.

## Overview

A Timeline de um incidente captura automaticamente:

- Criação e atualização de incidentes
- Mudanças de status, severidade e atribuição
- Adição, atualização e remoção de observáveis
- Criação, atualização e conclusão de tarefas
- Vinculação de alertas

## Componentes Principais

### 1. Modelo TimelineEvent

O modelo `TimelineEvent` armazena cada evento individual e contém:

- Referência ao incidente
- Tipo de evento (criação, atualização, mudança de status, etc.)
- Título e mensagem descritiva
- Metadados estruturados em JSON
- Usuário que realizou a ação
- Timestamp

### 2. Signals

O sistema utiliza sinais Django para capturar automaticamente as alterações:

- `track_incident_field_changes`: Monitora alterações nos campos do incidente
- `sync_timeline_to_events`: Sincroniza entradas manuais da timeline com o modelo TimelineEvent
- `observable_added_timeline_event`: Registra adição de observáveis
- `observable_updated_timeline_event`: Registra atualizações em observáveis
- `observable_removed_timeline_event`: Registra remoção de observáveis
- `task_created_or_updated_timeline_event`: Registra criação e atualização de tarefas
- `task_deleted_timeline_event`: Registra exclusão de tarefas
- `alert_linked_timeline_event`: Registra vinculação de alertas

### 3. Interface Administrativa

A timeline é exibida na interface administrativa como:

- Um inline no formulário de detalhes do incidente
- Uma visualização dedicada com filtros e pesquisa

## Tipos de Eventos

O sistema suporta os seguintes tipos de eventos:

- `CREATED`: Criação de incidente
- `UPDATED`: Atualização de campos gerais
- `STATUS_CHANGED`: Mudança de status do incidente
- `ASSIGNED`: Atribuição do incidente ou tarefa
- `ALERT_LINKED`: Vinculação de alertas
- `TASK_ADDED`: Adição de tarefas
- `TASK_COMPLETED`: Conclusão de tarefas
- `NOTE`: Notas manuais
- `ACTION`: Ações realizadas
- `SYSTEM`: Eventos gerados pelo sistema
- `CLOSED`: Fechamento do incidente
- `OTHER`: Outros tipos de eventos

## Metadados

Cada evento armazena metadados estruturados em JSON, que podem incluir:

- Campo alterado
- Valores antigos e novos
- IDs de entidades relacionadas
- Detalhes adicionais específicos do evento

## Uso Manual

Além do registro automático, é possível adicionar entradas manualmente:

```python
incident.add_timeline_entry(
    title="Análise realizada",
    content="Resultados da análise forense do evento",
    event_type="action",
    created_by=current_user
)
```

## Testes

O sistema inclui testes abrangentes que verificam todos os aspectos do registro de eventos:

- Criação e atualização de incidentes
- Operações CRUD em observáveis
- Operações CRUD em tarefas
- Entradas manuais da timeline 