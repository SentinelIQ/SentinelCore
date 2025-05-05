"""
Celery tasks for the api.core package.

This module contains celery tasks for background processing,
including audit log analysis, monitoring, and maintenance tasks.
"""

import os
import logging
import subprocess
import sys
from celery import shared_task
from celery.utils.log import get_task_logger
from typing import Dict, Any, Optional
from django.conf import settings

# Use the Celery-specific task logger
logger = get_task_logger(__name__)

@shared_task(
    name="api.core.tasks.run_migrations",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    acks_late=True,
    queue='sentineliq_soar_setup'  # Updated queue name
)
def run_migrations(self):
    """
    Task to run makemigrations and migrate automatically on system startup.
    This ensures the database is always in sync with the models.
    
    Features:
    - Auto-retry on failure (up to 3 times)
    - Late acknowledgment (only ack if task completes)
    - Detailed logging
    - Safe subprocess execution
    """
    task_id = self.request.id
    logger.info(f"Starting run_migrations task with ID: {task_id}")
    logger.info(f"Current directory: {os.getcwd()}")
    
    try:
        # Run makemigrations
        logger.info("Executing makemigrations...")
        makemigrations_result = subprocess.run(
            ["python", "manage.py", "makemigrations", "--noinput"], 
            capture_output=True, 
            text=True,
            check=True
        )
        logger.info(f"makemigrations output: {makemigrations_result.stdout}")
        
        # Check if any migrations were created
        if "No changes detected" in makemigrations_result.stdout:
            logger.info("No model changes detected that require migrations")
        else:
            logger.info("New migrations created successfully")
        
        # Run migrate
        logger.info("Executing migrate...")
        migrate_result = subprocess.run(
            ["python", "manage.py", "migrate", "--noinput"], 
            capture_output=True, 
            text=True,
            check=True
        )
        logger.info(f"migrate output: {migrate_result.stdout}")
        logger.info(f"Migrations completed successfully for task {task_id}")
        
        return {
            "status": "success",
            "task_id": self.request.id,
            "makemigrations": makemigrations_result.stdout,
            "migrate": migrate_result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        error_message = f"Error in migration process: {e.stderr}"
        logger.error(error_message)
        # Raise exception to trigger retry mechanism
        raise Exception(f"Migration command failed: {error_message}")
        
    except Exception as e:
        error_message = f"Unexpected error during migration process: {str(e)}"
        logger.error(error_message)
        logger.exception(e)  # Log full traceback
        # Raise exception to trigger retry mechanism 
        raise 

@shared_task(
    name="api.core.tasks.audit_log_anomaly_detection",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    acks_late=True
)
def audit_log_anomaly_detection(
    self,
    lookback_hours: int = 24,
    threshold: int = 10
):
    """
    Periodically check audit logs for security anomalies.
    
    Args:
        lookback_hours: Hours to look back for activity
        threshold: Activity threshold for anomaly detection
    
    Returns:
        Dict containing results of the anomaly detection
    """
    try:
        from api.core.audit_sentry import detect_anomalies
        
        # Run anomaly detection with parameters
        detect_anomalies(
            lookback_hours=lookback_hours,
            threshold=threshold
        )
        
        return {
            "status": "success",
            "lookback_hours": lookback_hours,
            "threshold": threshold,
        }
    except Exception as e:
        logger.exception(f"Error in anomaly detection: {str(e)}")
        
        # Retry with exponential backoff
        self.retry(exc=e)


@shared_task(
    name="api.core.tasks.audit_log_statistics",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True
)
def audit_log_statistics(self, period: str = "daily"):
    """
    Generate and store audit log statistics for reporting.
    
    Args:
        period: Time period for statistics (daily, weekly, monthly)
    
    Returns:
        Dict containing statistics and metrics
    """
    try:
        from django.utils import timezone
        import datetime
        from auditlog.models import LogEntry
        from django.db.models import Count
        
        # Determine time range based on period
        end_date = timezone.now()
        if period == "daily":
            start_date = end_date - datetime.timedelta(days=1)
        elif period == "weekly":
            start_date = end_date - datetime.timedelta(days=7)
        elif period == "monthly":
            start_date = end_date - datetime.timedelta(days=30)
        else:
            start_date = end_date - datetime.timedelta(days=1)
        
        # Get logs for the period
        logs = LogEntry.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Count total logs
        total_logs = logs.count()
        
        # Count by action type
        action_counts = logs.values('action').annotate(
            count=Count('action')
        ).order_by('-count')
        
        # Map to action names
        action_map = {
            LogEntry.Action.CREATE: 'create',
            LogEntry.Action.UPDATE: 'update',
            LogEntry.Action.DELETE: 'delete',
            LogEntry.Action.ACCESS: 'access',
        }
        
        action_statistics = {
            action_map.get(item['action'], 'unknown'): item['count'] 
            for item in action_counts
        }
        
        # Get entity type counts
        entity_counts = {}
        for log in logs:
            entity_type = None
            if hasattr(log, 'additional_data') and log.additional_data:
                entity_type = log.additional_data.get('entity_type')
            
            if not entity_type and log.content_type:
                entity_type = log.content_type.model
                
            if entity_type:
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        # Create statistics object
        statistics = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_logs": total_logs,
            "action_statistics": action_statistics,
            "entity_statistics": entity_counts,
        }
        
        # Report statistics to Sentry if available
        try:
            from sentineliq.sentry import set_context, capture_message
            
            set_context("audit_statistics", statistics)
            capture_message(
                f"Audit log statistics for {period} period",
                level="info"
            )
        except ImportError:
            logger.debug("Sentry not available for reporting statistics")
            
        return statistics
    except Exception as e:
        logger.exception(f"Error generating audit statistics: {str(e)}")
        self.retry(exc=e)


def setup_anomaly_detection():
    """
    Set up periodic anomaly detection tasks.
    
    This function schedules the anomaly detection task
    to run periodically using Celery Beat.
    """
    try:
        from django.conf import settings
        from django_celery_beat.models import PeriodicTask, IntervalSchedule
        import json
        
        # Check if the task already exists
        task_name = "Audit Log Anomaly Detection"
        if PeriodicTask.objects.filter(name=task_name).exists():
            logger.info(f"Periodic task '{task_name}' already exists")
            return
        
        # Create interval schedule (every 3 hours)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=3,
            period=IntervalSchedule.HOURS,
        )
        
        # Create periodic task
        PeriodicTask.objects.create(
            name=task_name,
            task="api.core.tasks.audit_log_anomaly_detection",
            interval=schedule,
            args=json.dumps([]),
            kwargs=json.dumps({
                "lookback_hours": 6,  # Look back 6 hours
                "threshold": getattr(settings, 'ANOMALY_THRESHOLD', 10),
            }),
            description="Check audit logs for security anomalies",
        )
        
        # Also set up daily statistics task
        stats_task_name = "Daily Audit Log Statistics"
        if not PeriodicTask.objects.filter(name=stats_task_name).exists():
            # Daily schedule
            daily_schedule, created = IntervalSchedule.objects.get_or_create(
                every=24,
                period=IntervalSchedule.HOURS,
            )
            
            # Create statistics task
            PeriodicTask.objects.create(
                name=stats_task_name,
                task="api.core.tasks.audit_log_statistics",
                interval=daily_schedule,
                args=json.dumps([]),
                kwargs=json.dumps({"period": "daily"}),
                description="Generate daily audit log statistics",
            )
        
        logger.info("Anomaly detection and statistics tasks scheduled successfully")
    except ImportError:
        logger.warning(
            "django_celery_beat not available, "
            "skipping automatic task scheduling"
        )
    except Exception as e:
        logger.exception(f"Error setting up anomaly detection tasks: {str(e)}") 