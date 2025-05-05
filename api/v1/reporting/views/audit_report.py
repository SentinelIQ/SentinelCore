"""
Module for generating audit reports.

This module provides views to generate different types of reports
related to audit logs.
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
    View for generating summarized audit reports.
    
    Provides metrics and statistics about audit logs for
    different periods and entity types.
    """
    permission_classes = [IsAuthenticated, HasEntityPermission]
    entity_type = 'audit_log'  # For RBAC verification
    
    @extend_schema(
        summary="Generate audit summary report",
        description="Returns statistics and metrics about audit logs",
        tags=["Reporting"],
        parameters=[
            OpenApiParameter(name="period", description="Report period (today, week, month, year)", type=str, required=False, default="month"),
            OpenApiParameter(name="entity_type", description="Entity type to filter", type=str, required=False),
            OpenApiParameter(name="user_id", description="User ID to filter", type=str, required=False),
        ],
        responses={200: dict}
    )
    def get(self, request):
        """
        Generate a summary report of audit logs.
        
        Filter by:
        - Period (today, week, month, year)
        - Entity type
        - User
        
        Returns:
        - Count of logs by action type
        - Distribution by entity type
        - Activity over time
        - Most active users
        """
        # Get filter parameters
        period = request.query_params.get('period', 'month')
        entity_type = request.query_params.get('entity_type')
        user_id = request.query_params.get('user_id')
        
        # Calculate time period
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
        else:  # month is default
            start_date = now - relativedelta(months=1)
            group_by = TruncDay('timestamp')
            date_format = '%b %d'
        
        # Prepare base queryset
        queryset = LogEntry.objects.filter(timestamp__gte=start_date)
        
        # Apply company filter
        user = request.user
        if not user.is_superuser and hasattr(user, 'company') and user.company:
            company_id = str(user.company.id)
            queryset = queryset.filter(additional_data__company_id=company_id)
        
        # Apply additional filters
        if entity_type:
            queryset = queryset.filter(additional_data__entity_type=entity_type)
            
        if user_id:
            queryset = queryset.filter(actor_id=user_id)
        
        # 1. Count by action type
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
        
        # 2. Distribution by entity type
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
        
        # 3. Activity over time
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
        
        # 4. Most active users
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
        
        # Build response
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
            message="Audit report generated successfully"
        )


class UserActivityReportView(APIView):
    """
    View for generating user activity reports.
    
    Provides details about actions performed by specific users
    in different periods.
    """
    permission_classes = [IsAuthenticated, HasEntityPermission]
    entity_type = 'audit_log'  # For RBAC verification
    
    @extend_schema(
        summary="Generate user activity report",
        description="Returns statistics about activities of a specific user",
        tags=["Reporting"],
        parameters=[
            OpenApiParameter(name="user_id", description="User ID to analyze", type=str, required=True),
            OpenApiParameter(name="period", description="Report period (today, week, month, year)", type=str, required=False, default="month"),
        ],
        responses={200: dict}
    )
    def get(self, request):
        """
        Generate activity report for a specific user.
        
        Parameters:
        - user_id: ID of the user to analyze (required)
        - period: Report period (today, week, month, year)
        
        Returns:
        - Total number of actions performed in the period
        - Distribution of actions by type
        - Most accessed entities
        - Activity over time
        """
        # Get parameters
        user_id = request.query_params.get('user_id')
        period = request.query_params.get('period', 'month')
        
        # Validate user ID
        if not user_id:
            return Response(
                {"detail": "The user_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate period
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
        else:  # month is default
            start_date = now - relativedelta(months=1)
            group_by = TruncDay('timestamp')
            date_format = '%b %d'
        
        # Prepare queryset for a specific user
        queryset = LogEntry.objects.filter(
            actor_id=user_id,
            timestamp__gte=start_date
        )
        
        # Apply company filter
        user = request.user
        if not user.is_superuser and hasattr(user, 'company') and user.company:
            company_id = str(user.company.id)
            queryset = queryset.filter(additional_data__company_id=company_id)
        
        # Total number of actions
        total_actions = queryset.count()
        
        # If there are no data, return an empty response
        if total_actions == 0:
            return success_response(
                data={
                    'period': period,
                    'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_date': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_actions': 0,
                    'message': 'No activity found for this user in the specified period'
                },
                message="User activity report generated"
            )
        
        # 1. Distribution by action type
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
        
        # 2. Most accessed entities
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
        
        # 3. Activity over time
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
        
        # 4. Get user details
        try:
            user_details = queryset.filter(actor_id=user_id).first().actor
            username = user_details.username
        except:
            username = "Unknown"
        
        # Build response
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
            message="User activity report generated successfully"
        ) 