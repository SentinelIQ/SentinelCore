"""
Celery tasks implementation template.

This file serves as a template for implementing Celery tasks
in Django modules following the SentinelIQ application patterns.
"""

from celery import Task as CeleryTask
from celery.utils.log import get_task_logger
from api.core.audit import AuditLogTaskMixin
from django.conf import settings
import json
import logging

# Specific logger for tasks
logger = get_task_logger(__name__)


class BaseTask(AuditLogTaskMixin, CeleryTask):
    """
    Base class for all Celery tasks in the application.
    
    Implements common functionality like:
    - Audit logging
    - Error handling
    - Task tracking
    - Queue management
    """
    
    # Default entity type for audit logging
    entity_type = 'task'
    
    # Retry config: maximum attempts and time between retries
    max_retries = 3
    default_retry_delay = 60
    
    # Only confirm task after successful execution
    acks_late = True
    
    def __call__(self, *args, **kwargs):
        """
        Run the task, capturing the company context if available.
        """
        try:
            # Extract company ID from kwargs if available
            company_id = kwargs.get('company_id')
            if company_id:
                # Add to context for audit logging
                self.company_id = company_id
                
                # Get company name for more descriptive logs
                from companies.models import Company
                try:
                    company = Company.objects.get(id=company_id)
                    self.company_name = company.name
                except Company.DoesNotExist:
                    self.company_name = "Unknown"
            
            # Call parent implementation
            return super().__call__(*args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Error in task {self.name}: {str(e)}")
            raise
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log retry attempts."""
        logger.warning(
            f"Retrying task {self.name} due to error: {str(exc)}. "
            f"Attempt {self.request.retries + 1}/{self.max_retries}."
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failures."""
        logger.error(
            f"Task {self.name} failed after {self.request.retries + 1} attempts. "
            f"Error: {str(exc)}"
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Log successful task completion."""
        logger.info(f"Task {self.name} completed successfully.")
        super().on_success(retval, task_id, args, kwargs)


def handle_task_exception(task, exc, max_retries=3, should_retry=True):
    """
    Helper function to handle task exceptions consistently.
    
    Args:
        task: The Celery task instance
        exc: The exception that was raised
        max_retries: Maximum number of retries
        should_retry: Whether to retry the task
        
    Returns:
        None. Either retries the task or raises the exception.
    """
    task_id = task.request.id
    task_name = task.name
    attempt = task.request.retries + 1
    
    # Log the exception
    logger.error(
        f"Error in task {task_name} (id: {task_id}): {str(exc)}. "
        f"Attempt {attempt}/{max_retries}."
    )
    
    # If we should retry and haven't exceeded max retries
    if should_retry and task.request.retries < max_retries:
        # Retry with exponential backoff
        retry_delay = 60 * (2 ** task.request.retries)  # 60s, 120s, 240s, etc.
        logger.info(f"Retrying task {task_name} in {retry_delay} seconds.")
        task.retry(exc=exc, countdown=retry_delay)
    else:
        # Or simply propagate the exception to use the default retry
        raise exc 