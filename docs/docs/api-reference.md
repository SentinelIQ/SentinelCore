---
title: Referência da API
sidebar_position: 3
---

# Referência da API

O SentinelIQ fornece uma API RESTful completa para integração com sua pilha de segurança. Esta seção descreve os endpoints disponíveis, formatos de requisição/resposta, e exemplos de uso.

## Autenticação

Todas as requisições à API devem incluir um token JWT válido no cabeçalho `Authorization`:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE2MTQ...
```

### Obter Token

```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "email": "usuario@empresa.com",
  "password": "senha_segura"
}
```

Resposta:

```json
{
  "status": "success",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "usuario@empresa.com",
      "company": {
        "id": 1,
        "name": "Empresa ABC"
      },
      "role": "admin"
    }
  }
}
```

### Renovar Token

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Formato de Resposta Padrão

Todas as respostas da API seguem um formato padrão:

```json
{
  "status": "success",
  "data": {
    // Dados específicos do endpoint
  },
  "page_info": {
    // Informações de paginação (quando aplicável)
    "total_items": 100,
    "page": 1,
    "page_size": 50,
    "total_pages": 2
  }
}
```

Em caso de erro:

```json
{
  "status": "error",
  "error": {
    "code": "permission_denied",
    "message": "Você não tem permissão para realizar esta ação",
    "details": {
      // Detalhes adicionais do erro (quando disponíveis)
    }
  }
}
```

## Endpoints Principais

### Empresas

#### Listar Empresas

```http
GET /api/v1/companies/
```

#### Detalhes da Empresa

```http
GET /api/v1/companies/{id}/
```

#### Criar Empresa

```http
POST /api/v1/companies/
Content-Type: application/json

{
  "name": "Nova Empresa",
  "domain": "empresa.com",
  "address": "Av. Principal, 123",
  "status": "active"
}
```

### Usuários

#### Listar Usuários

```http
GET /api/v1/users/
```

#### Detalhes do Usuário

```http
GET /api/v1/users/{id}/
```

#### Criar Usuário

```http
POST /api/v1/users/
Content-Type: application/json

{
  "email": "novo.usuario@empresa.com",
  "first_name": "Novo",
  "last_name": "Usuário",
  "company_id": 1,
  "role": "analyst",
  "status": "active"
}
```

### Alertas

#### Listar Alertas

```http
GET /api/v1/alerts/
```

Parâmetros de filtro:

- `status` - Status dos alertas (open, in_progress, closed)
- `severity` - Severidade (low, medium, high, critical)
- `source` - Fonte do alerta
- `created_after` - Data de criação (início)
- `created_before` - Data de criação (fim)

#### Detalhes do Alerta

```http
GET /api/v1/alerts/{id}/
```

#### Criar Alerta

```http
POST /api/v1/alerts/
Content-Type: application/json

{
  "title": "Atividade Suspeita Detectada",
  "description": "Multiple failed login attempts detected",
  "severity": "high",
  "source": "firewall",
  "raw_data": {
    "ip": "192.168.1.1",
    "attempts": 5,
    "timestamp": "2023-08-15T14:30:00Z"
  }
}
```

### Incidentes

#### Listar Incidentes

```http
GET /api/v1/incidents/
```

#### Detalhes do Incidente

```http
GET /api/v1/incidents/{id}/
```

#### Criar Incidente

```http
POST /api/v1/incidents/
Content-Type: application/json

{
  "title": "Potential Data Breach",
  "description": "Suspicious outbound data transfer",
  "severity": "critical",
  "status": "open",
  "assigned_to": 5,
  "alert_ids": [123, 124, 125]
}
```

## Códigos de Status HTTP

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 201 | Recurso criado com sucesso |
| 204 | Operação concluída sem conteúdo para retornar |
| 400 | Requisição inválida ou dados mal-formatados |
| 401 | Não autenticado |
| 403 | Não autorizado |
| 404 | Recurso não encontrado |
| 409 | Conflito (ex: violação de unicidade) |
| 422 | Erro de validação |
| 500 | Erro interno do servidor |

## Paginação

Endpoints que retornam listas de objetos são paginados por padrão com 50 itens por página. Você pode controlar a paginação com os seguintes parâmetros:

- `page` - Número da página (começa em 1)
- `page_size` - Itens por página (10, 25, 50, 100)

Exemplo:

```http
GET /api/v1/alerts/?page=2&page_size=25
```

## Ordenação

Use o parâmetro `order_by` para controlar a ordenação, prefixando com `-` para ordem descendente:

```http
GET /api/v1/alerts/?order_by=-created_at
```

## Rate Limiting

A API aplica limites de taxa para prevenir sobrecarga:

- 60 requisições por minuto para usuários autenticados
- 20 requisições por minuto para usuários não autenticados

O limite restante é retornado nos cabeçalhos:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1615471140
``` 