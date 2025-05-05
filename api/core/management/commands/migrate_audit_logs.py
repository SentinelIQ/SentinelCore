"""
Comando para migrar logs de auditoria do sistema antigo para django-auditlog.
"""

import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger('api')
User = get_user_model()


class Command(BaseCommand):
    help = 'Migra logs de auditoria do sistema antigo para django-auditlog'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', 
            type=int, 
            default=500,
            help='Número de registros a processar por lote'
        )
        parser.add_argument(
            '--start-id', 
            type=int, 
            default=0,
            help='ID de início para a migração'
        )
        parser.add_argument(
            '--max-records', 
            type=int, 
            default=None,
            help='Número máximo de registros a migrar (None = todos)'
        )
        parser.add_argument(
            '--dry-run', 
            action='store_true',
            help='Executar sem fazer alterações no banco de dados'
        )
        
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        start_id = options['start_id']
        max_records = options['max_records']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS(f"Iniciando migração de logs de auditoria"))
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY RUN - Nenhuma alteração será salva"))
        
        # Verificar se existe a tabela antiga de logs
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM audit_logs_auditlog LIMIT 1")
        except Exception as e:
            raise CommandError(f"Tabela antiga de logs não encontrada: {str(e)}")
            
        try:
            # Contar registros a migrar
            with connection.cursor() as cursor:
                count_sql = "SELECT COUNT(*) FROM audit_logs_auditlog WHERE id >= %s"
                params = [start_id]
                
                if max_records:
                    count_sql += " LIMIT %s"
                    params.append(max_records)
                    
                cursor.execute(count_sql, params)
                total_records = cursor.fetchone()[0]
                
            self.stdout.write(f"Total de {total_records} logs a migrar")
            
            # Preparar variáveis de controle
            processed = 0
            migrated = 0
            skipped = 0
            errors = 0
            
            # Processar em lotes para não sobrecarregar a memória
            current_id = start_id
            
            while True:
                if max_records and processed >= max_records:
                    break
                    
                # Obter próximo lote de registros
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            id, timestamp, actor_id, content_type_id, 
                            object_id, object_repr, action, changes, 
                            additional_data, remote_addr
                        FROM audit_logs_auditlog
                        WHERE id >= %s
                        ORDER BY id
                        LIMIT %s
                        """,
                        [current_id, batch_size]
                    )
                    
                    rows = cursor.fetchall()
                
                if not rows:
                    break
                    
                # Processar registros do lote
                for row in rows:
                    processed += 1
                    
                    # Atualizar progress bar
                    if processed % 100 == 0:
                        self.stdout.write(f"Progresso: {processed}/{total_records} ({processed/total_records*100:.1f}%)")
                    
                    try:
                        # Extrair dados do registro antigo
                        (
                            old_id, timestamp, actor_id, content_type_id,
                            object_id, object_repr, action, changes,
                            additional_data, remote_addr
                        ) = row
                        
                        # Mapear ação para formato django-auditlog
                        action_map = {
                            'create': LogEntry.Action.CREATE,
                            'update': LogEntry.Action.UPDATE,
                            'delete': LogEntry.Action.DELETE,
                            'view': LogEntry.Action.ACCESS,
                            0: LogEntry.Action.CREATE,
                            1: LogEntry.Action.UPDATE,
                            2: LogEntry.Action.DELETE,
                            3: LogEntry.Action.ACCESS,
                        }
                        
                        # Converter action para o formato correto
                        try:
                            action = action_map.get(action, LogEntry.Action.CREATE)
                        except Exception:
                            action = LogEntry.Action.CREATE
                        
                        # Parse additional data
                        try:
                            if additional_data:
                                additional_data = json.loads(additional_data)
                            else:
                                additional_data = {}
                        except Exception:
                            additional_data = {}
                            
                        # Parse changes data
                        try:
                            if changes:
                                changes = json.loads(changes)
                            else:
                                changes = {}
                        except Exception:
                            changes = {}
                        
                        # Processar apenas se não estiver em dry run
                        if not dry_run:
                            with transaction.atomic():
                                # Criar novo registro no django-auditlog
                                new_log = LogEntry(
                                    timestamp=timestamp or timezone.now(),
                                    content_type_id=content_type_id,
                                    object_pk=object_id,
                                    object_repr=object_repr or '',
                                    action=action,
                                    changes=changes,
                                    actor_id=actor_id,
                                    remote_addr=remote_addr or '',
                                    additional_data=additional_data
                                )
                                new_log.save()
                                
                        migrated += 1
                        current_id = old_id + 1
                        
                    except Exception as e:
                        errors += 1
                        logger.error(f"Erro ao migrar log ID {old_id}: {str(e)}")
                
                # Atualizar current_id para próxima iteração
                if rows:
                    current_id = rows[-1][0] + 1
            
            # Resumo final
            self.stdout.write(self.style.SUCCESS(
                f"Migração completa! Processados: {processed}, "
                f"Migrados: {migrated}, Ignorados: {skipped}, Erros: {errors}"
            ))
            
        except Exception as e:
            raise CommandError(f"Erro durante a migração: {str(e)}") 