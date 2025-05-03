import logging
import uuid
import traceback
from datetime import datetime
from io import StringIO
from celery import shared_task
from django.utils import timezone
from django.db.models import F

from sentinelvision.models import (
    FeedModule, FeedExecutionRecord, 
    ExecutionSourceEnum, ExecutionStatusEnum
)
from sentinelvision.logging import get_structured_logger

logger = get_structured_logger('sentinelvision.tasks')

@shared_task(
    bind=True,
    name='sentinelvision.tasks.run_feed_task',
    rate_limit="10/m",
    acks_late=True,
    max_retries=3,
    retry_backoff=True,
    queue="sentineliq_soar_vision_feed"
)
def run_feed_task(self, feed_id, execution_record_id=None, company_id=None):
    """
    Execute a feed module.
    
    Args:
        feed_id: UUID of the feed module to execute
        execution_record_id: Optional UUID of an existing execution record
        company_id: Optional UUID of company (for filtering)
    
    Returns:
        dict: Execution results
    """
    structured_log = {
        'feed_id': feed_id,
        'execution_id': execution_record_id,
        'company_id': company_id,
        'task_id': self.request.id
    }
    
    logger.info(
        f"Starting feed execution task for feed {feed_id}",
        extra=structured_log
    )
    
    try:
        # Get feed module
        try:
            feed = FeedModule.objects.get(id=feed_id)
            structured_log['feed_name'] = feed.name
            structured_log['feed_type'] = getattr(feed, 'feed_id', feed.__class__.__name__.lower())
        except FeedModule.DoesNotExist:
            error_msg = f"Feed with ID {feed_id} not found"
            logger.error(error_msg, extra=structured_log)
            
            # Update execution record if it exists
            if execution_record_id:
                try:
                    execution_record = FeedExecutionRecord.objects.get(id=execution_record_id)
                    execution_record.mark_failed(error_message=error_msg)
                except Exception as exec_err:
                    logger.error(
                        f"Error updating execution record: {str(exec_err)}",
                        extra=structured_log
                    )
            
            return {
                'status': 'error',
                'error': error_msg
            }
        
        # Get or create execution record
        execution_record = None
        if execution_record_id:
            try:
                execution_record = FeedExecutionRecord.objects.get(id=execution_record_id)
                structured_log['execution_id'] = str(execution_record.id)
            except FeedExecutionRecord.DoesNotExist:
                logger.warning(
                    f"Execution record {execution_record_id} not found, creating new one",
                    extra=structured_log
                )
                execution_record = None
        
        if not execution_record:
            execution_record = FeedExecutionRecord.objects.create(
                feed=feed,
                source=ExecutionSourceEnum.SCHEDULED,
                status=ExecutionStatusEnum.PENDING,
                started_at=timezone.now()
            )
            structured_log['execution_id'] = str(execution_record.id)
            
        # Mark as running
        execution_record.mark_running()
        
        # Capture logs
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger.addHandler(handler)
        
        # Execute feed
        logger.info(
            f"Executing feed '{feed.name}'",
            extra=structured_log
        )
        
        # Run the feed update
        start_time = timezone.now()
        result = feed.execute()
        end_time = timezone.now()
        
        # Parse result
        status = result.get('status', 'error')
        processed_count = result.get('processed_count', 0)
        error_msg = result.get('error', '')
        
        structured_log['status'] = status
        structured_log['processed_count'] = processed_count
        structured_log['duration_seconds'] = (end_time - start_time).total_seconds()
        
        if status == 'success':
            logger.info(
                f"Feed '{feed.name}' executed successfully: {processed_count} IOCs processed",
                extra=structured_log
            )
            
            # Update execution record
            execution_record.mark_success(
                iocs_processed=processed_count,
                log=log_capture.getvalue()
            )
            
            # Update feed metrics
            feed.total_iocs_imported = F('total_iocs_imported') + processed_count
            feed.last_successful_fetch = timezone.now()
            feed.save(update_fields=['total_iocs_imported', 'last_successful_fetch'])
            
        else:
            logger.error(
                f"Feed '{feed.name}' execution failed: {error_msg}",
                extra=structured_log
            )
            
            # Update execution record
            execution_record.mark_failed(
                error_message=error_msg,
                log=log_capture.getvalue()
            )
        
        # Clean up log handler
        logger.removeHandler(handler)
        
        # Return result
        return {
            'status': status,
            'feed_id': str(feed.id),
            'feed_name': feed.name,
            'execution_id': str(execution_record.id),
            'processed_count': processed_count,
            'error': error_msg,
            'duration_seconds': structured_log['duration_seconds']
        }
        
    except Exception as e:
        error_msg = f"Exception in feed execution task: {str(e)}"
        logger.error(
            error_msg,
            extra={**structured_log, 'error': str(e), 'traceback': traceback.format_exc()},
            exc_info=True
        )
        
        # Update execution record if it exists
        if execution_record_id:
            try:
                execution_record = FeedExecutionRecord.objects.get(id=execution_record_id)
                execution_record.mark_failed(
                    error_message=error_msg,
                    log=f"Unexpected error: {str(e)}\n\n{traceback.format_exc()}"
                )
            except Exception as exec_err:
                logger.error(
                    f"Error updating execution record: {str(exec_err)}",
                    extra=structured_log
                )
        
        # Retry with backoff
        self.retry(exc=e)
        
        return {
            'status': 'error',
            'error': error_msg,
            'is_retrying': True
        }

@shared_task(
    bind=True,
    name='sentinelvision.tasks.schedule_feeds',
    acks_late=True,
    queue="sentineliq_soar_vision_scheduled"
)
def schedule_feeds(self):
    """
    Check for feeds that need to be executed based on their cron schedule.
    This task is triggered by Celery Beat.
    
    Returns:
        dict: Scheduling results
    """
    from django_celery_beat.models import CrontabSchedule, PeriodicTask
    import json
    
    logger.info("Checking for scheduled feeds to execute")
    
    # Get all active feeds with a cron schedule
    feeds = FeedModule.objects.filter(
        is_active=True
    ).exclude(cron_schedule='')
    
    scheduled_count = 0
    error_count = 0
    
    # Process each feed
    for feed in feeds:
        try:
            if not feed.cron_schedule:
                continue
                
            feed_id = str(feed.id)
            feed_name = feed.name
            company_id = str(feed.company.id) if feed.company else None
            
            logger.info(
                f"Scheduling feed '{feed_name}' with cron: {feed.cron_schedule}",
                extra={
                    'feed_id': feed_id,
                    'feed_name': feed_name,
                    'company_id': company_id,
                    'cron_schedule': feed.cron_schedule
                }
            )
            
            # Parse cron expression (minute hour day_of_month month day_of_week)
            cron_parts = feed.cron_schedule.split()
            if len(cron_parts) != 5:
                logger.error(
                    f"Invalid cron expression for feed '{feed_name}': {feed.cron_schedule}",
                    extra={'feed_id': feed_id, 'feed_name': feed_name}
                )
                error_count += 1
                continue
                
            minute, hour, day_of_month, month, day_of_week = cron_parts
            
            # Get or create cron schedule
            cron_schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=minute,
                hour=hour,
                day_of_month=day_of_month,
                month_of_year=month,
                day_of_week=day_of_week
            )
            
            # Get or create periodic task
            task_name = f"feed.{feed_id}.scheduled"
            task_args = json.dumps([feed_id, None, company_id])
            
            periodic_task, created = PeriodicTask.objects.update_or_create(
                name=task_name,
                defaults={
                    'task': 'sentinelvision.tasks.run_feed_task',
                    'crontab': cron_schedule,
                    'args': task_args,
                    'kwargs': json.dumps({}),
                    'enabled': True,
                    'description': f"Scheduled execution of feed {feed_name}"
                }
            )
            
            scheduled_count += 1
            
        except Exception as e:
            logger.error(
                f"Error scheduling feed {feed.name}: {str(e)}",
                extra={'feed_id': str(feed.id), 'feed_name': feed.name, 'error': str(e)},
                exc_info=True
            )
            error_count += 1
    
    logger.info(
        f"Feed scheduling complete. Scheduled {scheduled_count} feeds with {error_count} errors.",
        extra={'scheduled_count': scheduled_count, 'error_count': error_count}
    )
    
    return {
        'status': 'success',
        'scheduled_count': scheduled_count,
        'error_count': error_count
    } 