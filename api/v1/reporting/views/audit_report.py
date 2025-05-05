"""
Módulo para geração de relatórios de auditoria.

Este módulo fornece views para gerar diferentes tipos de relatórios
relacionados a logs de auditoria.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncDay, TruncHour
from auditlog.models import LogEntry
from api.core.responses import success_response
from api.core.rbac import HasEntityPermission
from dateutil.relativedelta import relativedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
import datetime


class AuditSummaryReportView(APIView):
    """
    Visão para gerar relatórios resumidos de auditoria.
    
    Fornece métricas e estatísticas sobre logs de auditoria para
    diferentes períodos e tipos de entidade.
    """
    permission_classes = [IsAuthenticated, HasEntityPermission]
    entity_type = 'audit_log'  # Para verificação RBAC
    
    @extend_schema(
        summary="Gerar relatório resumido de auditoria",
        description="Retorna estatísticas e métricas sobre logs de auditoria",
        tags=["Reporting"],
        parameters=[
            OpenApiParameter(name="period", description="Período do relatório (today, week, month, year)", type=str, required=False, default="month"),
            OpenApiParameter(name="entity_type", description="Tipo de entidade para filtrar", type=str, required=False),
            OpenApiParameter(name="user_id", description="ID do usuário para filtrar", type=str, required=False),
        ],
        responses={200: dict}
    )
    def get(self, request):
        """
        Gerar relatório resumido de logs de auditoria.
        
        Permite filtrar por:
        - Período (today, week, month, year)
        - Tipo de entidade
        - Usuário
        
        Retorna:
        - Contagem de logs por tipo de ação
        - Distribuição por tipo de entidade
        - Atividade ao longo do tempo
        - Usuários mais ativos
        """
        # Obter parâmetros de filtro
        period = request.query_params.get('period', 'month')
        entity_type = request.query_params.get('entity_type')
        user_id = request.query_params.get('user_id')
        
        # Calcular período de tempo
        now = timezone.now()
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            group_by = TruncHour('timestamp')
            date_format = '%H:%M'
        elif period == 'week':
            start_date = now - relativedelta(days=7)
            group_by = TruncDay('timestamp')
            date_format = '%b %d'
        elif period == 'year':
            start_date = now - relativedelta(years=1)
            group_by = TruncDay('timestamp')
            date_format = '%b %Y'
        else:  # month é o padrão
            start_date = now - relativedelta(months=1)
            group_by = TruncDay('timestamp')
            date_format = '%b %d'
        
        # Preparar queryset base
        queryset = LogEntry.objects.filter(timestamp__gte=start_date)
        
        # Aplicar filtro de empresa
        user = request.user
        if not user.is_superuser and hasattr(user, 'company') and user.company:
            company_id = str(user.company.id)
            queryset = queryset.filter(additional_data__company_id=company_id)
        
        # Aplicar filtros adicionais
        if entity_type:
            queryset = queryset.filter(additional_data__entity_type=entity_type)
            
        if user_id:
            queryset = queryset.filter(actor_id=user_id)
        
        # 1. Contagem por tipo de ação
        action_counts = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        action_data = []
        for item in action_counts:
            action_name = LogEntry.Action.choices[item['action']][1]
            action_data.append({
                'action': action_name,
                'count': item['count']
            })
        
        # 2. Distribuição por tipo de entidade
        entity_counts = queryset.filter(
            additional_data__entity_type__isnull=False
        ).values(
            'additional_data__entity_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        entity_data = []
        for item in entity_counts:
            entity_data.append({
                'entity_type': item['additional_data__entity_type'],
                'count': item['count']
            })
        
        # 3. Atividade ao longo do tempo
        time_series = queryset.annotate(
            date=group_by
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        time_data = []
        for item in time_series:
            time_data.append({
                'date': item['date'].strftime(date_format),
                'count': item['count']
            })
        
        # 4. Usuários mais ativos
        user_counts = queryset.filter(
            actor__isnull=False
        ).values(
            'actor__username', 'actor__id'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        user_data = []
        for item in user_counts:
            user_data.append({
                'username': item['actor__username'],
                'user_id': item['actor__id'],
                'count': item['count']
            })
        
        # Montar resposta
        report_data = {
            'period': period,
            'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'end_date': now.strftime('%Y-%m-%d %H:%M:%S'),
            'total_logs': queryset.count(),
            'action_distribution': action_data,
            'entity_distribution': entity_data,
            'time_series': time_data,
            'top_users': user_data,
        }
        
        return success_response(
            data=report_data,
            message="Relatório de auditoria gerado com sucesso"
        )


class UserActivityReportView(APIView):
    """
    Visão para gerar relatórios de atividade de usuários.
    
    Fornece detalhes sobre as ações realizadas por usuários específicos
    em diferentes períodos.
    """
    permission_classes = [IsAuthenticated, HasEntityPermission]
    entity_type = 'audit_log'  # Para verificação RBAC
    
    @extend_schema(
        summary="Gerar relatório de atividade de usuário",
        description="Retorna estatísticas sobre atividades de um usuário específico",
        tags=["Reporting"],
        parameters=[
            OpenApiParameter(name="user_id", description="ID do usuário para analisar", type=str, required=True),
            OpenApiParameter(name="period", description="Período do relatório (today, week, month, year)", type=str, required=False, default="month"),
        ],
        responses={200: dict}
    )
    def get(self, request):
        """
        Gerar relatório de atividade para um usuário específico.
        
        Parâmetros:
        - user_id: ID do usuário para analisar (obrigatório)
        - period: Período do relatório (today, week, month, year)
        
        Retorna:
        - Total de ações realizadas no período
        - Distribuição de ações por tipo
        - Entidades mais acessadas
        - Atividade ao longo do tempo
        """
        # Obter parâmetros
        user_id = request.query_params.get('user_id')
        period = request.query_params.get('period', 'month')
        
        # Validar ID do usuário
        if not user_id:
            return Response(
                {"detail": "O parâmetro user_id é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular período
        now = timezone.now()
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            group_by = TruncHour('timestamp')
            date_format = '%H:%M'
        elif period == 'week':
            start_date = now - relativedelta(days=7)
            group_by = TruncDay('timestamp')
            date_format = '%b %d'
        elif period == 'year':
            start_date = now - relativedelta(years=1)
            group_by = TruncDay('timestamp')
            date_format = '%b %Y'
        else:  # month é o padrão
            start_date = now - relativedelta(months=1)
            group_by = TruncDay('timestamp')
            date_format = '%b %d'
        
        # Preparar queryset para um usuário específico
        queryset = LogEntry.objects.filter(
            actor_id=user_id,
            timestamp__gte=start_date
        )
        
        # Aplicar filtro de empresa
        user = request.user
        if not user.is_superuser and hasattr(user, 'company') and user.company:
            company_id = str(user.company.id)
            queryset = queryset.filter(additional_data__company_id=company_id)
        
        # Total de ações
        total_actions = queryset.count()
        
        # Se não houver dados, retornar uma resposta vazia
        if total_actions == 0:
            return success_response(
                data={
                    'period': period,
                    'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_date': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_actions': 0,
                    'message': 'Nenhuma atividade encontrada para este usuário no período especificado'
                },
                message="Relatório de atividade do usuário gerado"
            )
        
        # 1. Distribuição por tipo de ação
        action_counts = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        action_data = []
        for item in action_counts:
            action_name = LogEntry.Action.choices[item['action']][1]
            action_data.append({
                'action': action_name,
                'count': item['count'],
                'percentage': round((item['count'] / total_actions) * 100, 2)
            })
        
        # 2. Entidades mais acessadas
        entity_counts = queryset.filter(
            additional_data__entity_type__isnull=False
        ).values(
            'additional_data__entity_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        entity_data = []
        for item in entity_counts:
            entity_data.append({
                'entity_type': item['additional_data__entity_type'],
                'count': item['count'],
                'percentage': round((item['count'] / total_actions) * 100, 2)
            })
        
        # 3. Atividade ao longo do tempo
        time_series = queryset.annotate(
            date=group_by
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        time_data = []
        for item in time_series:
            time_data.append({
                'date': item['date'].strftime(date_format),
                'count': item['count']
            })
        
        # 4. Obter detalhes do usuário
        try:
            user_details = queryset.filter(actor_id=user_id).first().actor
            username = user_details.username
        except:
            username = "Desconhecido"
        
        # Montar resposta
        report_data = {
            'user_id': user_id,
            'username': username,
            'period': period,
            'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'end_date': now.strftime('%Y-%m-%d %H:%M:%S'),
            'total_actions': total_actions,
            'action_distribution': action_data,
            'entity_distribution': entity_data,
            'time_series': time_data,
        }
        
        return success_response(
            data=report_data,
            message="Relatório de atividade do usuário gerado com sucesso"
        ) 