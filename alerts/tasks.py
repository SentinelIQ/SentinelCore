"""
Tarefas Celery para processar alertas de forma assíncrona.
"""

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from alerts.models import Alert
from api.core.audit import audit_task
import logging

logger = logging.getLogger('alerts')


@shared_task
@audit_task(entity_type='alert')
def process_new_alert(alert_id, **kwargs):
    """
    Processa um novo alerta recebido no sistema.
    
    Esta tarefa executa:
    1. Enriquecimento de dados
    2. Correlação com alertas existentes
    3. Atualização de severidade se necessário
    4. Notificações relevantes
    
    Args:
        alert_id: ID do alerta a processar
        **kwargs: Parâmetros adicionais
        
    Returns:
        dict: Resultado do processamento com status
    """
    logger.info(f"Processando alerta: {alert_id}")
    
    try:
        with transaction.atomic():
            # Obter o alerta do banco de dados
            alert = Alert.objects.get(id=alert_id)
            
            # Registrar início do processamento
            alert.processing_status = 'processing'
            alert.save(update_fields=['processing_status'])
            
            # ETAPA 1: Enriquecimento de dados
            # (implementação a ser feita)
            
            # ETAPA 2: Correlação
            # (implementação a ser feita)
            
            # ETAPA 3: Atualização de severidade
            # (implementação a ser feita)
            
            # ETAPA 4: Gerar notificações
            # (implementação a ser feita)
            
            # Marcar como processado
            alert.processing_status = 'processed'
            alert.processed_at = timezone.now()
            alert.save(update_fields=['processing_status', 'processed_at'])
            
            logger.info(f"Alerta {alert_id} processado com sucesso")
            return {
                'status': 'success',
                'alert_id': alert_id,
                'severity': alert.severity,
                'processing_time': (timezone.now() - alert.created_at).total_seconds(),
            }
            
    except Alert.DoesNotExist:
        logger.error(f"Alerta {alert_id} não encontrado")
        return {
            'status': 'error',
            'alert_id': alert_id,
            'error': 'alert_not_found',
        }
        
    except Exception as e:
        logger.exception(f"Erro ao processar alerta {alert_id}: {str(e)}")
        
        # Em caso de erro, atualizar status
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.processing_status = 'error'
            alert.save(update_fields=['processing_status'])
        except:
            pass
            
        return {
            'status': 'error',
            'alert_id': alert_id,
            'error': str(e),
        }


@shared_task
@audit_task(entity_type='alert')
def bulk_recalculate_severity(alert_ids=None, company_id=None, **kwargs):
    """
    Recalcula a severidade de um grupo de alertas.
    
    Útil após mudanças nas regras de severidade ou
    quando novos dados de inteligência são recebidos.
    
    Args:
        alert_ids: Lista de IDs de alertas para recalcular
        company_id: ID da empresa para filtrar alertas
        **kwargs: Parâmetros adicionais
        
    Returns:
        dict: Estatísticas do recálculo
    """
    logger.info(f"Iniciando recálculo de severidade em lote para {len(alert_ids) if alert_ids else 'todos'} alertas")
    
    # Preparar queryset
    alerts = Alert.objects.filter(processing_status='processed')
    
    # Filtrar por IDs específicos se fornecidos
    if alert_ids:
        alerts = alerts.filter(id__in=alert_ids)
        
    # Filtrar por empresa se especificada
    if company_id:
        alerts = alerts.filter(company_id=company_id)
    
    # Inicializar contadores
    total = alerts.count()
    updated = 0
    errors = 0
    
    # Processar cada alerta
    for alert in alerts:
        try:
            # Recalcular severidade
            old_severity = alert.severity
            
            # Lógica de recálculo vai aqui
            # alert.recalculate_severity()
            
            # Se a severidade mudou, contar como atualizado
            if old_severity != alert.severity:
                updated += 1
                
        except Exception as e:
            logger.error(f"Erro ao recalcular severidade do alerta {alert.id}: {str(e)}")
            errors += 1
    
    logger.info(f"Recálculo de severidade concluído. Total: {total}, Atualizados: {updated}, Erros: {errors}")
    
    # Retornar estatísticas
    return {
        'status': 'success',
        'total': total,
        'updated': updated,
        'errors': errors,
    }


@shared_task
@audit_task(entity_type='alert')
def cleanup_old_alerts(days=30, status=None, **kwargs):
    """
    Arquiva ou remove alertas antigos com base em critérios.
    
    Args:
        days: Número de dias para considerar um alerta antigo
        status: Status específico a filtrar ('resolved', 'closed', etc)
        **kwargs: Parâmetros adicionais
        
    Returns:
        dict: Estatísticas da limpeza
    """
    logger.info(f"Iniciando limpeza de alertas com mais de {days} dias")
    
    # Calcular data limite
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # Preparar queryset
    alerts = Alert.objects.filter(created_at__lt=cutoff_date)
    
    # Filtrar por status específico se fornecido
    if status:
        alerts = alerts.filter(status=status)
        
    # Contar alertas afetados
    total = alerts.count()
    
    # Arquivar ou excluir os alertas
    # Na implementação real, você pode querer arquivar em vez de excluir
    # ou fazer algum tipo de backup antes
    try:
        # Exemplo: marcar como arquivado
        alerts.update(
            is_archived=True,
            archived_at=timezone.now(),
            archived_reason='automated_cleanup'
        )
        
        logger.info(f"Limpeza concluída. {total} alertas arquivados.")
        
        return {
            'status': 'success',
            'total_archived': total,
            'cutoff_date': cutoff_date.isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro durante limpeza de alertas: {str(e)}")
        
        return {
            'status': 'error',
            'error': str(e),
        } 