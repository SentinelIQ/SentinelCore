"""
Scheduled periodic tasks for SentinelIQ.

This module contains all tasks that run on a schedule via Celery Beat,
providing regular system maintenance, reporting, and data processing.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from django.utils import timezone
from django.conf import settings
from django.db.models import Count, Q, Sum

from celery.utils.log import get_task_logger
from django_celery_beat.models import (
    PeriodicTask, IntervalSchedule, CrontabSchedule, SolarSchedule
)

from sentineliq.tasks.base import PeriodicTask, register_task

# Get a dedicated logger for the scheduled tasks
logger = get_task_logger('sentineliq.tasks.scheduled')


@register_task(
    name='sentineliq.tasks.scheduled.schedule_periodic_tasks',
    queue='sentineliq_soar_setup',
    base=PeriodicTask
)
def schedule_periodic_tasks(self, enable_all: bool = True, task_list: Optional[List[str]] = None):
    """
    Schedule or update all periodic tasks in the system.
    
    This meta-task ensures all scheduled tasks are properly registered in the
    Celery Beat scheduler with appropriate intervals.
    
    Args:
        enable_all: Whether to enable all tasks (default: True)
        task_list: Optional list of specific tasks to enable (if enable_all is False)
    
    Returns:
        Dict containing the results of the scheduling operation
    """
    if task_list is None:
        task_list = []
    
    logger.info(f"Setting up periodic tasks (enable_all={enable_all}, tasks={task_list})")
    
    task_configs = {
        # Daily tasks
        'daily_report_generator': {
            'schedule_type': 'crontab',
            'crontab': {
                'minute': '0',
                'hour': '1',  # 1 AM
                'day_of_week': '*',
                'day_of_month': '*',
                'month_of_year': '*',
            },
            'task': 'sentineliq.tasks.scheduled.daily_report_generator',
            'args': '[]',
            'kwargs': '{"days": 1}',
            'description': 'Generate daily summary reports',
        },
        
        # Weekly tasks
        'weekly_cleanup': {
            'schedule_type': 'crontab',
            'crontab': {
                'minute': '0',
                'hour': '2',  # 2 AM
                'day_of_week': 'sunday',
                'day_of_month': '*',
                'month_of_year': '*',
            },
            'task': 'sentineliq.tasks.scheduled.weekly_cleanup',
            'args': '[]',
            'kwargs': '{"days": 7}',
            'description': 'Weekly system cleanup',
        },
        
        # Monthly tasks
        'monthly_statistics': {
            'schedule_type': 'crontab',
            'crontab': {
                'minute': '0',
                'hour': '3',  # 3 AM
                'day_of_week': '*',
                'day_of_month': '1',  # First day of month
                'month_of_year': '*',
            },
            'task': 'sentineliq.tasks.scheduled.monthly_statistics',
            'args': '[]',
            'kwargs': '{}',
            'description': 'Generate monthly statistics',
        },
        
        # System health check - every 15 minutes
        'system_health_check': {
            'schedule_type': 'interval',
            'interval': {
                'every': 15,
                'period': 'minutes',
            },
            'task': 'sentineliq.tasks.system.health_check',
            'args': '[]',
            'kwargs': '{}',
            'description': 'Regular system health check',
        },
        
        # Old log cleanup - daily at 4 AM
        'cleanup_old_logs': {
            'schedule_type': 'crontab',
            'crontab': {
                'minute': '0',
                'hour': '4',  # 4 AM
                'day_of_week': '*',
                'day_of_month': '*',
                'month_of_year': '*',
            },
            'task': 'sentineliq.tasks.system.cleanup_old_logs',
            'args': '[]',
            'kwargs': '{"days": 90}',
            'description': 'Cleanup old log entries',
        },
    }
    
    created = []
    updated = []
    errors = []
    
    try:
        # Process each task configuration
        for task_name, config in task_configs.items():
            # Skip if not in task_list (when enable_all is False)
            if not enable_all and task_name not in task_list:
                continue
                
            try:
                # Get or create the schedule
                schedule = None
                
                if config['schedule_type'] == 'interval':
                    # Create interval schedule
                    schedule, created = IntervalSchedule.objects.get_or_create(
                        every=config['interval']['every'],
                        period=config['interval']['period'],
                    )
                    
                elif config['schedule_type'] == 'crontab':
                    # Create crontab schedule
                    schedule, created = CrontabSchedule.objects.get_or_create(
                        minute=config['crontab']['minute'],
                        hour=config['crontab']['hour'],
                        day_of_week=config['crontab']['day_of_week'],
                        day_of_month=config['crontab']['day_of_month'],
                        month_of_year=config['crontab']['month_of_year'],
                    )
                    
                # Get or create the periodic task
                if schedule:
                    periodic_task, created = PeriodicTask.objects.update_or_create(
                        name=task_name,
                        defaults={
                            'task': config['task'],
                            f"{config['schedule_type']}": schedule,
                            'args': config['args'],
                            'kwargs': config['kwargs'],
                            'description': config['description'],
                            'enabled': True,
                        }
                    )
                    
                    if created:
                        created.append(task_name)
                    else:
                        updated.append(task_name)
                        
            except Exception as e:
                logger.error(f"Error creating periodic task {task_name}: {str(e)}")
                errors.append({
                    'task': task_name,
                    'error': str(e)
                })
        
        # Log results
        logger.info(f"Periodic tasks setup complete: {len(created)} created, {len(updated)} updated, {len(errors)} errors")
        
        return {
            'status': 'success' if not errors else 'partial',
            'created': created,
            'updated': updated,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Error setting up periodic tasks: {str(e)}")
        logger.exception(e)
        
        return {
            'status': 'error',
            'error': str(e),
            'created': created,
            'updated': updated,
            'errors': errors
        }


@register_task(
    name='sentineliq.tasks.scheduled.daily_report_generator',
    queue='sentineliq_soar_notification',
    base=PeriodicTask
)
def daily_report_generator(self, days: int = 1, report_format: str = 'pdf'):
    """
    Generate and distribute daily reports.
    
    This scheduled task runs daily to compile activity reports
    and distribute them to administrators.
    
    Args:
        days: Number of days to include in the report (default: 1)
        report_format: Report format (pdf, html, csv)
    
    Returns:
        Dict containing the report generation results
    """
    logger.info(f"Generating daily report for the past {days} days in {report_format} format")
    
    try:
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        report_data = {
            'report_type': 'daily',
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days,
            },
            'format': report_format,
            'sections': {},
        }
        
        # Collect statistics for alerts
        try:
            from alerts.models import Alert
            
            alert_stats = {
                'total': Alert.objects.filter(
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).count(),
                'by_severity': {},
                'by_status': {},
            }
            
            # Get alerts by severity
            severity_counts = Alert.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).values('severity').annotate(count=Count('id'))
            
            for item in severity_counts:
                alert_stats['by_severity'][item['severity']] = item['count']
                
            # Get alerts by status
            status_counts = Alert.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).values('status').annotate(count=Count('id'))
            
            for item in status_counts:
                alert_stats['by_status'][item['status']] = item['count']
                
            report_data['sections']['alerts'] = alert_stats
                
        except ImportError:
            logger.warning("Alert module not available, skipping alert statistics")
        
        # Collect statistics for incidents
        try:
            from incidents.models import Incident
            
            incident_stats = {
                'total': Incident.objects.filter(
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).count(),
                'by_status': {},
                'by_severity': {},
            }
            
            # Get incidents by status
            status_counts = Incident.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).values('status').annotate(count=Count('id'))
            
            for item in status_counts:
                incident_stats['by_status'][item['status']] = item['count']
                
            # Get incidents by severity
            severity_counts = Incident.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).values('severity').annotate(count=Count('id'))
            
            for item in severity_counts:
                incident_stats['by_severity'][item['severity']] = item['count']
                
            report_data['sections']['incidents'] = incident_stats
                
        except ImportError:
            logger.warning("Incident module not available, skipping incident statistics")
        
        # Generate the report file
        report_filename = f"daily_report_{start_date.strftime('%Y-%m-%d')}.{report_format}"
        report_path = f"/app/reports/{report_filename}"
        
        # This is a placeholder - in a real implementation, you would
        # generate the actual report file using a reporting library
        logger.info(f"Report would be generated at: {report_path}")
        
        # Send the report to administrators
        try:
            from notifications.tasks import send_notification
            
            # Create notification about the report
            notification_data = {
                'title': f"Daily Report for {start_date.strftime('%Y-%m-%d')}",
                'message': f"The daily report for {start_date.strftime('%Y-%m-%d')} has been generated.",
                'report_path': report_path,
                'report_data': report_data,
            }
            
            logger.info(f"Sending report notification to administrators")
            
            # In a real implementation, you would create the notification
            # and send it to administrators
            
        except ImportError:
            logger.warning("Notification module not available, skipping notification")
        
        return {
            'status': 'success',
            'report': report_filename,
            'report_data': report_data,
        }
        
    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        logger.exception(e)
        
        return {
            'status': 'error',
            'error': str(e),
        }


@register_task(
    name='sentineliq.tasks.scheduled.weekly_cleanup',
    queue='sentineliq_soar_setup',
    base=PeriodicTask
)
def weekly_cleanup(self, days: int = 7):
    """
    Perform weekly maintenance and cleanup tasks.
    
    This scheduled task runs weekly to clean up temporary files,
    optimize database tables, and perform other maintenance.
    
    Args:
        days: Number of days of data to examine (default: 7)
    
    Returns:
        Dict containing the cleanup results
    """
    logger.info(f"Starting weekly cleanup process for the past {days} days")
    
    results = {
        'status': 'success',
        'cleanup_actions': [],
        'errors': [],
    }
    
    try:
        # Calculate date range
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # 1. Clean up temporary files
        try:
            import os
            import glob
            
            # Clean up temporary files in the tmp directory
            tmp_files = glob.glob('/app/tmp/*')
            tmp_file_count = len(tmp_files)
            
            for tmp_file in tmp_files:
                try:
                    # Check if file is older than the cutoff date
                    file_time = os.path.getmtime(tmp_file)
                    file_date = datetime.fromtimestamp(file_time)
                    
                    if file_date < cutoff_date:
                        os.remove(tmp_file)
                except Exception as e:
                    results['errors'].append({
                        'action': 'tmp_file_cleanup',
                        'file': tmp_file,
                        'error': str(e),
                    })
            
            results['cleanup_actions'].append({
                'action': 'tmp_file_cleanup',
                'files_examined': tmp_file_count,
            })
            
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {str(e)}")
            results['errors'].append({
                'action': 'tmp_file_cleanup',
                'error': str(e),
            })
        
        # 2. Clean up expired tokens
        try:
            from rest_framework.authtoken.models import Token
            
            # Delete expired tokens
            expired_tokens = Token.objects.filter(created__lt=cutoff_date)
            token_count = expired_tokens.count()
            expired_tokens.delete()
            
            results['cleanup_actions'].append({
                'action': 'token_cleanup',
                'tokens_deleted': token_count,
            })
            
        except ImportError:
            logger.warning("Token module not available, skipping token cleanup")
        except Exception as e:
            logger.error(f"Error cleaning up tokens: {str(e)}")
            results['errors'].append({
                'action': 'token_cleanup',
                'error': str(e),
            })
        
        # 3. Optimize database tables
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # List of tables to optimize (example)
                tables = ['auditlog_logentry', 'alerts_alert', 'incidents_incident']
                
                for table in tables:
                    try:
                        # For PostgreSQL, use VACUUM ANALYZE
                        cursor.execute(f"VACUUM ANALYZE {table};")
                        logger.info(f"Optimized table: {table}")
                    except Exception as e:
                        results['errors'].append({
                            'action': 'db_optimization',
                            'table': table,
                            'error': str(e),
                        })
                
                results['cleanup_actions'].append({
                    'action': 'db_optimization',
                    'tables_optimized': len(tables),
                })
                
        except Exception as e:
            logger.error(f"Error optimizing database tables: {str(e)}")
            results['errors'].append({
                'action': 'db_optimization',
                'error': str(e),
            })
        
        # Log results
        if results['errors']:
            logger.warning(f"Weekly cleanup completed with {len(results['errors'])} errors")
            results['status'] = 'partial'
        else:
            logger.info(f"Weekly cleanup completed successfully with {len(results['cleanup_actions'])} actions")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in weekly cleanup: {str(e)}")
        logger.exception(e)
        
        return {
            'status': 'error',
            'error': str(e),
        }


@register_task(
    name='sentineliq.tasks.scheduled.monthly_statistics',
    queue='sentineliq_soar_setup',
    base=PeriodicTask
)
def monthly_statistics(self):
    """
    Generate monthly statistics and reports.
    
    This scheduled task runs monthly to compile detailed statistics
    about system usage, alerts, incidents, and other metrics.
    
    Returns:
        Dict containing the statistics results
    """
    logger.info("Generating monthly statistics")
    
    try:
        # Calculate date range (previous month)
        end_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_date = (end_date - timedelta(days=1)).replace(day=1)
        
        stats = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'month': start_date.month,
                'year': start_date.year,
            },
            'metrics': {},
            'status': 'success',
        }
        
        # 1. Collect alert statistics
        try:
            from alerts.models import Alert
            
            alert_stats = {
                'total': Alert.objects.filter(
                    created_at__gte=start_date,
                    created_at__lt=end_date
                ).count(),
                'by_severity': {},
                'by_status': {},
                'avg_resolution_time': None,
            }
            
            # Get alerts by severity
            severity_counts = Alert.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values('severity').annotate(count=Count('id'))
            
            for item in severity_counts:
                alert_stats['by_severity'][item['severity']] = item['count']
                
            # Get alerts by status
            status_counts = Alert.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values('status').annotate(count=Count('id'))
            
            for item in status_counts:
                alert_stats['by_status'][item['status']] = item['count']
                
            # Calculate average resolution time for resolved alerts
            resolved_alerts = Alert.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                status='resolved',
                resolved_at__isnull=False
            )
            
            total_resolution_time = sum(
                (alert.resolved_at - alert.created_at).total_seconds()
                for alert in resolved_alerts
            )
            
            if resolved_alerts.count() > 0:
                avg_seconds = total_resolution_time / resolved_alerts.count()
                alert_stats['avg_resolution_time'] = avg_seconds / 3600  # Convert to hours
                
            stats['metrics']['alerts'] = alert_stats
                
        except ImportError:
            logger.warning("Alert module not available, skipping alert statistics")
        
        # 2. Collect incident statistics
        try:
            from incidents.models import Incident
            
            incident_stats = {
                'total': Incident.objects.filter(
                    created_at__gte=start_date,
                    created_at__lt=end_date
                ).count(),
                'by_status': {},
                'by_severity': {},
                'avg_resolution_time': None,
            }
            
            # Get incidents by status
            status_counts = Incident.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values('status').annotate(count=Count('id'))
            
            for item in status_counts:
                incident_stats['by_status'][item['status']] = item['count']
                
            # Get incidents by severity
            severity_counts = Incident.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values('severity').annotate(count=Count('id'))
            
            for item in severity_counts:
                incident_stats['by_severity'][item['severity']] = item['count']
                
            # Calculate average resolution time for resolved incidents
            resolved_incidents = Incident.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                status='closed',
                closed_at__isnull=False
            )
            
            total_resolution_time = sum(
                (incident.closed_at - incident.created_at).total_seconds()
                for incident in resolved_incidents
            )
            
            if resolved_incidents.count() > 0:
                avg_seconds = total_resolution_time / resolved_incidents.count()
                incident_stats['avg_resolution_time'] = avg_seconds / 3600  # Convert to hours
                
            stats['metrics']['incidents'] = incident_stats
                
        except ImportError:
            logger.warning("Incident module not available, skipping incident statistics")
        
        # 3. Collect system usage statistics
        try:
            from api.v1.audit_logs.models import AuditLog
            
            audit_stats = {
                'total_actions': AuditLog.objects.filter(
                    created_at__gte=start_date,
                    created_at__lt=end_date
                ).count(),
                'by_actor_type': {},
                'by_action': {},
                'by_entity_type': {},
            }
            
            # Get actions by actor type
            actor_counts = AuditLog.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values('actor').annotate(count=Count('id'))
            
            for item in actor_counts:
                actor = item['actor'] or 'unknown'
                audit_stats['by_actor_type'][actor] = item['count']
                
            # Get actions by action type
            action_counts = AuditLog.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values('action').annotate(count=Count('id'))
            
            for item in action_counts:
                action = item['action'] or 'unknown'
                audit_stats['by_action'][action] = item['count']
                
            # Get actions by entity type
            entity_counts = AuditLog.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values('entity_type').annotate(count=Count('id'))
            
            for item in entity_counts:
                entity_type = item['entity_type'] or 'unknown'
                audit_stats['by_entity_type'][entity_type] = item['count']
                
            stats['metrics']['audit_logs'] = audit_stats
                
        except ImportError:
            logger.warning("AuditLog module not available, skipping audit statistics")
        
        # Store the statistics in a file
        stat_filename = f"monthly_stats_{start_date.strftime('%Y-%m')}.json"
        
        # This is a placeholder - in a real implementation, you would
        # store the statistics in a file or database
        logger.info(f"Statistics would be stored in: {stat_filename}")
        
        # Log results
        logger.info(f"Monthly statistics generation completed successfully")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error generating monthly statistics: {str(e)}")
        logger.exception(e)
        
        return {
            'status': 'error',
            'error': str(e),
        } 