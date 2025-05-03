import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, F, ExpressionWrapper, fields, Q, DurationField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth

logger = logging.getLogger('api.dashboard')

def calculate_date_range(days=30):
    """
    Calculate start and end dates for a given range.
    
    Args:
        days (int): Number of days to look back
        
    Returns:
        tuple: (start_date, end_date)
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def get_alert_metrics(company, start_date=None, end_date=None, days=30):
    """
    Get alert metrics for a company.
    
    Args:
        company: Company object
        start_date: Optional start date
        end_date: Optional end date
        days: Number of days to include if start/end not provided
        
    Returns:
        dict: Alert metrics
    """
    try:
        from alerts.models import Alert
        
        # Set date range if not provided
        if not start_date or not end_date:
            start_date, end_date = calculate_date_range(days)
            
        # Filter alerts by company and date range
        alerts = Alert.objects.filter(
            company=company,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Basic counts
        total_alerts = alerts.count()
        open_alerts = alerts.filter(status='open').count()
        closed_alerts = alerts.filter(status='closed').count()
        
        # Alerts by severity
        severity_counts = dict(alerts.values_list('severity').annotate(count=Count('id')))
        
        # Alerts over time (daily)
        alerts_by_day = alerts.annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Format for easier frontend consumption
        alerts_trend = [
            {'date': entry['day'].strftime('%Y-%m-%d'), 'count': entry['count']}
            for entry in alerts_by_day
        ]
        
        return {
            'total': total_alerts,
            'open': open_alerts,
            'closed': closed_alerts,
            'by_severity': severity_counts,
            'trend': alerts_trend
        }
    except Exception as e:
        logger.error(f"Error calculating alert metrics: {str(e)}")
        return {
            'total': 0,
            'open': 0,
            'closed': 0,
            'by_severity': {},
            'trend': []
        }


def get_incident_metrics(company, start_date=None, end_date=None, days=30):
    """
    Get incident metrics for a company.
    
    Args:
        company: Company object
        start_date: Optional start date
        end_date: Optional end date
        days: Number of days to include if start/end not provided
        
    Returns:
        dict: Incident metrics
    """
    try:
        from incidents.models import Incident
        
        # Set date range if not provided
        if not start_date or not end_date:
            start_date, end_date = calculate_date_range(days)
            
        # Filter incidents by company and date range
        incidents = Incident.objects.filter(
            company=company,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Basic counts
        total_incidents = incidents.count()
        
        # Incidents by status
        status_counts = dict(incidents.values_list('status').annotate(count=Count('id')))
        
        # Incidents by severity
        severity_counts = dict(incidents.values_list('severity').annotate(count=Count('id')))
        
        # Incidents over time (daily)
        incidents_by_day = incidents.annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Format for easier frontend consumption
        incidents_trend = [
            {'date': entry['day'].strftime('%Y-%m-%d'), 'count': entry['count']}
            for entry in incidents_by_day
        ]
        
        # Calculate MTTR (Mean Time to Resolve) for closed incidents
        closed_incidents = incidents.filter(
            status='closed',
            end_date__isnull=False
        )
        
        mttr_expression = ExpressionWrapper(
            F('end_date') - F('created_at'),
            output_field=DurationField()
        )
        
        mttr_data = closed_incidents.annotate(
            resolution_time=mttr_expression
        ).aggregate(
            avg_resolution_time=Avg('resolution_time')
        )
        
        mttr_hours = 0
        if mttr_data['avg_resolution_time']:
            mttr_hours = mttr_data['avg_resolution_time'].total_seconds() / 3600
        
        # Calculate escalation rate
        try:
            from alerts.models import Alert
            total_alerts_count = Alert.objects.filter(
                company=company,
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            
            # Count alerts that were escalated to incidents
            escalated_alerts_count = Alert.objects.filter(
                company=company,
                created_at__gte=start_date,
                created_at__lte=end_date,
                incidents__isnull=False
            ).distinct().count()
            
            escalation_rate = round((escalated_alerts_count / total_alerts_count * 100), 2) if total_alerts_count > 0 else 0
        except Exception:
            escalation_rate = 0
            
        return {
            'total': total_incidents,
            'by_status': status_counts,
            'by_severity': severity_counts,
            'trend': incidents_trend,
            'mttr_hours': round(mttr_hours, 2),
            'escalation_rate': escalation_rate
        }
    except Exception as e:
        logger.error(f"Error calculating incident metrics: {str(e)}")
        return {
            'total': 0,
            'by_status': {},
            'by_severity': {},
            'trend': [],
            'mttr_hours': 0,
            'escalation_rate': 0
        }


def get_task_metrics(company, start_date=None, end_date=None, days=30):
    """
    Get task metrics for a company.
    
    Args:
        company: Company object
        start_date: Optional start date
        end_date: Optional end date
        days: Number of days to include if start/end not provided
        
    Returns:
        dict: Task metrics
    """
    try:
        from tasks.models import Task
        
        # Set date range if not provided
        if not start_date or not end_date:
            start_date, end_date = calculate_date_range(days)
            
        # Filter tasks by company and date range
        tasks = Task.objects.filter(
            company=company,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Basic counts
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='completed').count()
        pending_tasks = tasks.filter(status='pending').count()
        in_progress_tasks = tasks.filter(status='in_progress').count()
        
        # Calculate task completion rate
        completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0
        
        # Tasks by priority
        priority_counts = dict(tasks.values_list('priority').annotate(count=Count('id')))
        
        # Tasks over time (daily)
        tasks_by_day = tasks.annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Format for easier frontend consumption
        tasks_trend = [
            {'date': entry['day'].strftime('%Y-%m-%d'), 'count': entry['count']}
            for entry in tasks_by_day
        ]
        
        return {
            'total': total_tasks,
            'completed': completed_tasks,
            'pending': pending_tasks,
            'in_progress': in_progress_tasks,
            'completion_rate': completion_rate,
            'by_priority': priority_counts,
            'trend': tasks_trend
        }
    except Exception as e:
        logger.error(f"Error calculating task metrics: {str(e)}")
        return {
            'total': 0,
            'completed': 0,
            'pending': 0,
            'in_progress': 0,
            'completion_rate': 0,
            'by_priority': {},
            'trend': []
        }


def get_dashboard_summary(company, days=30):
    """
    Get a complete dashboard summary for a company.
    
    Args:
        company: Company object
        days: Number of days to include
        
    Returns:
        dict: Dashboard summary data
    """
    try:
        start_date, end_date = calculate_date_range(days)
        
        # Get metrics from each category
        alerts = get_alert_metrics(company, start_date, end_date)
        incidents = get_incident_metrics(company, start_date, end_date)
        tasks = get_task_metrics(company, start_date, end_date)
        
        # User activity - use related_name 'users' instead of user_set
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_count = User.objects.filter(company=company, is_active=True).count()
        
        return {
            'timeframe': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days': days
            },
            'alerts': alerts,
            'incidents': incidents,
            'tasks': tasks,
            'users': {
                'active': user_count
            }
        }
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {str(e)}")
        return {
            'error': str(e)
        } 