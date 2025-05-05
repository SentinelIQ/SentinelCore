"""
Base definitions for all Celery tasks in SentinelIQ.

This module provides base classes and utilities to standardize
task definitions, error handling, auditing, and logging across
the application.
"""

import logging
import time
import traceback
from functools import wraps
from typing import Any, Dict, Optional, Callable, TypeVar, Union

from celery import Task, shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

# Type definitions
F = TypeVar('F', bound=Callable[..., Any])

# Get a dedicated task logger
logger = get_task_logger('sentineliq.tasks')


class BaseTask(Task):
    """
    Base class for all tasks in the system.
    
    Provides:
    - Consistent error handling
    - Performance tracking
    - Audit logging integration
    """
    
    # Default task settings - can be overridden in subclasses
    name = None  # Must be explicitly set
    autoretry_for = (Exception,)
    retry_kwargs = {
        'max_retries': 3,
        'countdown': 60
    }
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    acks_late = True  # Only acknowledge after task completes
    track_started = True
    store_errors_even_if_ignored = True
    
    # Task categorization for reporting and monitoring
    task_category = 'general'  # Override in subclasses
    
    def __call__(self, *args, **kwargs):
        """
        Execute the task with timing and tracking.
        """
        start_time = time.time()
        task_id = getattr(self.request, 'id', 'unknown')
        context = {
            'task_id': task_id,
            'task_name': self.name,
            'args': args,
            'kwargs': kwargs,
        }
        
        logger.info(f"Starting task {self.name}", extra=context)
        
        try:
            # Execute the task
            result = super().__call__(*args, **kwargs)
            
            # Log completion and timing
            execution_time = time.time() - start_time
            logger.info(
                f"Task {self.name} completed in {execution_time:.2f}s",
                extra={**context, 'execution_time': execution_time}
            )
            
            # Record in audit log if available
            try:
                self._record_task_audit(
                    status='success',
                    execution_time=execution_time,
                    result=result,
                    args=args,
                    kwargs=kwargs
                )
            except Exception as audit_error:
                logger.warning(f"Failed to audit task: {str(audit_error)}")
            
            return result
            
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Get traceback
            exc_traceback = traceback.format_exc()
            
            # Log the error
            logger.error(
                f"Task {self.name} failed after {execution_time:.2f}s: {str(e)}",
                extra={
                    **context,
                    'execution_time': execution_time,
                    'error': str(e),
                    'traceback': exc_traceback
                },
                exc_info=True
            )
            
            # Record in audit log if available
            try:
                self._record_task_audit(
                    status='error',
                    execution_time=execution_time,
                    error=str(e),
                    traceback=exc_traceback,
                    args=args, 
                    kwargs=kwargs
                )
            except Exception as audit_error:
                logger.warning(f"Failed to audit task error: {str(audit_error)}")
            
            # Re-raise the exception for Celery's retry mechanism
            raise
    
    def _record_task_audit(self, status: str, execution_time: float, **extra_data) -> None:
        """
        Record task execution in the audit log.
        
        Args:
            status: Task execution status (success/error)
            execution_time: Task execution time in seconds
            **extra_data: Additional data to include in the audit log
        """
        try:
            from api.v1.audit_logs.models import AuditLog
            
            # Extract company_id if available in kwargs
            company_id = extra_data.get('kwargs', {}).get('company_id')
            
            # Create audit log entry
            AuditLog.objects.create(
                entity_type='task',
                action=self.name.split('.')[-1],  # Extract task action from name
                actor='system',
                company_id=company_id,
                additional_data={
                    'task_id': self.request.id,
                    'task_name': self.name,
                    'execution_time': execution_time,
                    'status': status,
                    'task_category': self.task_category,
                    'system_actor': 'system.celery.task',
                    **extra_data
                }
            )
        except ImportError:
            logger.debug("AuditLog model not available, skipping audit")
        except Exception as e:
            logger.warning(f"Error creating audit log: {str(e)}")


class PeriodicTask(BaseTask):
    """
    Base class for periodic (scheduled) tasks.
    
    Provides additional functionality for tasks that run on a schedule.
    """
    
    task_category = 'scheduled'
    
    def apply_async(self, args=None, kwargs=None, **options):
        """
        Override to add scheduled task tracking.
        """
        # Add metadata about schedule
        task_kwargs = kwargs or {}
        if 'scheduled_time' not in task_kwargs:
            task_kwargs['scheduled_time'] = timezone.now().isoformat()
        
        return super().apply_async(args=args, kwargs=task_kwargs, **options)


class MaintenanceTask(BaseTask):
    """
    Base class for system maintenance tasks.
    """
    
    task_category = 'maintenance'
    

class DataProcessingTask(BaseTask):
    """
    Base class for data processing tasks.
    """
    
    task_category = 'data_processing'
    

def audit_task_decorator(entity_type: str, action: str) -> Callable[[F], F]:
    """
    Decorator for functions that should be audited.
    
    Args:
        entity_type: Type of entity being affected
        action: Action being performed
    
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Audit successful execution
                try:
                    from api.v1.audit_logs.models import AuditLog
                    AuditLog.objects.create(
                        entity_type=entity_type,
                        action=action,
                        actor='system',
                        additional_data={
                            'execution_time': execution_time,
                            'args': args,
                            'kwargs': kwargs,
                            'result': result,
                            'status': 'success'
                        }
                    )
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to create audit log: {str(e)}")
                
                return result
                
            except Exception as e:
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Audit failed execution
                try:
                    from api.v1.audit_logs.models import AuditLog
                    AuditLog.objects.create(
                        entity_type=entity_type,
                        action=action,
                        actor='system',
                        additional_data={
                            'execution_time': execution_time,
                            'args': args,
                            'kwargs': kwargs,
                            'error': str(e),
                            'traceback': traceback.format_exc(),
                            'status': 'error'
                        }
                    )
                except ImportError:
                    pass
                except Exception as audit_e:
                    logger.warning(f"Failed to create error audit log: {str(audit_e)}")
                
                # Re-raise the original exception
                raise
                
        return wrapper
    
    return decorator


# Task registration utilities

def register_task(
    name: str,
    queue: str = None,
    bind: bool = True,
    base: Task = BaseTask,
    **kwargs
) -> Callable[[F], Task]:
    """
    Factory function to create a registered task with standard configuration.
    
    Args:
        name: Full task name (e.g., 'app.module.task_name')
        queue: Queue to run the task in
        bind: Whether to bind the task to self
        base: Base task class to use
        **kwargs: Additional task options
    
    Returns:
        Function decorator that registers the task
    """
    # Default the queue based on the task name if not specified
    if queue is None:
        if 'setup' in name or 'system' in name:
            queue = 'sentineliq_soar_setup'
        elif 'feed' in name:
            queue = 'sentineliq_soar_vision_feed'
        elif 'enrich' in name:
            queue = 'sentineliq_soar_vision_enrichment'
        elif 'analyze' in name:
            queue = 'sentineliq_soar_vision_analyzer'
        elif 'respond' in name:
            queue = 'sentineliq_soar_vision_responder'
        elif 'notif' in name:
            queue = 'sentineliq_soar_notification'
        else:
            queue = 'celery'
    
    # Set default task options
    task_options = {
        'name': name,
        'queue': queue,
        'bind': bind,
        'base': base,
        'autoretry_for': (Exception,),
        'retry_kwargs': {'max_retries': 3, 'countdown': 60},
        'retry_backoff': True,
        'acks_late': True,
        'track_started': True,
    }
    
    # Override with any provided options
    task_options.update(kwargs)
    
    # Create the decorated function
    return shared_task(**task_options) 