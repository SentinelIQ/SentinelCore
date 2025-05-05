"""
System maintenance tasks for SentinelIQ.

This module provides system-level tasks for maintenance operations,
database management, and system health monitoring.
"""

import os
import logging
import subprocess
import json
import psutil
import datetime
from typing import Dict, Any, Optional, List, Tuple

from django.conf import settings
from django.utils import timezone
from django.db import connections

from sentineliq.tasks.base import MaintenanceTask, register_task

# Get a dedicated logger for the system tasks
logger = logging.getLogger('sentineliq.tasks.system')


@register_task(
    name='sentineliq.tasks.system.run_migrations',
    queue='sentineliq_soar_setup',
    rate_limit='2/h',
    max_retries=5,
    retry_backoff=True,
    base=MaintenanceTask
)
def run_migrations(self, skip_apps: Optional[List[str]] = None):
    """
    Run database migrations on application startup or when triggered manually.
    
    This task ensures database schema is synchronized with models by running
    Django's migration commands in a safe and logged manner.
    
    Args:
        skip_apps: List of app names to skip during migration (optional)
    
    Returns:
        Dict containing the results of the migration operation
    """
    skip_apps = skip_apps or []
    task_id = self.request.id
    
    logger.info(f"Starting run_migrations task with ID: {task_id}")
    logger.info(f"Current directory: {os.getcwd()}")
    
    try:
        # Run makemigrations
        logger.info("Executing makemigrations...")
        makemigrations_cmd = ["python", "manage.py", "makemigrations", "--noinput"]
        
        # Add any apps to skip
        if skip_apps:
            for app in skip_apps:
                makemigrations_cmd.extend(["--skip-app", app])
                
        makemigrations_result = subprocess.run(
            makemigrations_cmd, 
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
        migrate_cmd = ["python", "manage.py", "migrate", "--noinput"]
        
        # Add any apps to skip
        if skip_apps:
            for app in skip_apps:
                migrate_cmd.extend(["--skip-app", app])
                
        migrate_result = subprocess.run(
            migrate_cmd, 
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
            "migrate": migrate_result.stdout,
            "skipped_apps": skip_apps
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


@register_task(
    name='sentineliq.tasks.system.cleanup_old_logs',
    queue='sentineliq_soar_setup',
    rate_limit='1/h',
    base=MaintenanceTask
)
def cleanup_old_logs(self, days: int = 90):
    """
    Cleanup old log entries from the database to prevent unbounded growth.
    
    This task removes old log entries that exceed the retention period,
    helping manage database size and query performance.
    
    Args:
        days: Number of days to keep logs (default: 90)
    
    Returns:
        Dict containing statistics about the cleanup operation
    """
    from api.v1.audit_logs.models import AuditLog
    from django.db.models import Q
    
    logger.info(f"Starting cleanup of logs older than {days} days")
    
    try:
        # Calculate cutoff date
        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        
        # Count records before deletion
        total_logs = AuditLog.objects.count()
        old_logs = AuditLog.objects.filter(created_at__lt=cutoff_date).count()
        
        # Delete old logs
        deletion_result = AuditLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        # Calculate remaining logs
        remaining_logs = AuditLog.objects.count()
        
        logger.info(
            f"Log cleanup complete: {old_logs} logs removed, {remaining_logs} logs remaining"
        )
        
        return {
            "status": "success",
            "total_logs_before": total_logs,
            "logs_deleted": old_logs,
            "logs_remaining": remaining_logs,
            "retention_days": days,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        logger.exception(e)
        raise


@register_task(
    name='sentineliq.tasks.system.health_check',
    queue='sentineliq_soar_setup',
    soft_time_limit=60,
    base=MaintenanceTask
)
def health_check(self) -> Dict[str, Any]:
    """
    Perform a comprehensive health check of the system.
    
    Checks:
    - Database connections
    - Memory usage
    - Disk space
    - Connected services
    
    Returns:
        Dict containing health metrics for monitoring
    """
    logger.info("Starting system health check")
    
    health_status = {
        "timestamp": timezone.now().isoformat(),
        "database": {},
        "system": {},
        "services": {},
        "overall_status": "healthy"
    }
    
    try:
        # Check database connections
        for connection_name in connections:
            try:
                connection = connections[connection_name]
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    health_status["database"][connection_name] = {
                        "status": "connected" if result and result[0] == 1 else "error",
                        "error": None
                    }
            except Exception as e:
                health_status["database"][connection_name] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
        
        # Check system resources
        memory = psutil.virtual_memory()
        health_status["system"]["memory"] = {
            "total": memory.total,
            "available": memory.available,
            "percent_used": memory.percent,
            "status": "warning" if memory.percent > 85 else "healthy"
        }
        
        # Set overall status to warning if memory usage is high
        if memory.percent > 85:
            health_status["overall_status"] = "degraded"
        
        # Check disk space
        disk = psutil.disk_usage('/')
        health_status["system"]["disk"] = {
            "total": disk.total,
            "free": disk.free,
            "percent_used": disk.percent,
            "status": "warning" if disk.percent > 85 else "healthy"
        }
        
        # Set overall status to warning if disk usage is high
        if disk.percent > 85:
            health_status["overall_status"] = "degraded"
        
        # Check Redis connection
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            redis_conn.ping()
            health_status["services"]["redis"] = {
                "status": "connected",
                "error": None
            }
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check RabbitMQ connection
        try:
            from celery.app.control import Control
            from celery import current_app
            
            control = Control(current_app)
            ping_result = control.ping()
            health_status["services"]["rabbitmq"] = {
                "status": "connected" if ping_result else "error",
                "workers": len(ping_result) if ping_result else 0,
                "error": None if ping_result else "No workers responded"
            }
            
            if not ping_result:
                health_status["overall_status"] = "degraded"
                
        except Exception as e:
            health_status["services"]["rabbitmq"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Log health check results
        logger.info(
            f"Health check completed: System is {health_status['overall_status']}"
        )
        
        # Save health check result to Redis for dashboard display
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            redis_conn.set(
                "sentineliq:system:health_check", 
                json.dumps(health_status),
                ex=3600  # Expire after 1 hour
            )
        except Exception as e:
            logger.warning(f"Failed to save health check to Redis: {str(e)}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        logger.exception(e)
        
        health_status["overall_status"] = "critical"
        health_status["error"] = str(e)
        
        return health_status


@register_task(
    name='sentineliq.tasks.system.maintenance_mode_toggle',
    queue='sentineliq_soar_setup',
    base=MaintenanceTask
)
def maintenance_mode_toggle(self, enable: bool = False, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Enable or disable maintenance mode for the application.
    
    When in maintenance mode, the application will show a maintenance page
    to end users and prevent certain operations from executing.
    
    Args:
        enable: Whether to enable (True) or disable (False) maintenance mode
        message: Optional message to display to users
    
    Returns:
        Dict containing the operation result
    """
    action = "enable" if enable else "disable"
    message = message or f"System maintenance in progress. Please check back later."
    
    logger.info(f"Request to {action} maintenance mode with message: {message}")
    
    try:
        # Use Redis to track maintenance mode
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        
        if enable:
            # Set maintenance mode in Redis with the provided message
            redis_conn.set("sentineliq:system:maintenance_mode", "1")
            redis_conn.set("sentineliq:system:maintenance_message", message)
            redis_conn.set("sentineliq:system:maintenance_started", timezone.now().isoformat())
            
            logger.info(f"Maintenance mode enabled with message: {message}")
            
            # Optionally, you could pause Celery workers here
            
            return {
                "status": "success",
                "maintenance_mode": "enabled",
                "message": message,
                "started_at": timezone.now().isoformat()
            }
        else:
            # Disable maintenance mode
            redis_conn.delete("sentineliq:system:maintenance_mode")
            redis_conn.delete("sentineliq:system:maintenance_message")
            
            # Record when maintenance mode was disabled
            end_time = timezone.now().isoformat()
            redis_conn.set("sentineliq:system:maintenance_ended", end_time)
            
            logger.info("Maintenance mode disabled")
            
            # Optionally, resume Celery workers here
            
            return {
                "status": "success",
                "maintenance_mode": "disabled",
                "ended_at": end_time
            }
            
    except Exception as e:
        logger.error(f"Error toggling maintenance mode: {str(e)}")
        logger.exception(e)
        
        return {
            "status": "error",
            "action": action,
            "error": str(e)
        } 