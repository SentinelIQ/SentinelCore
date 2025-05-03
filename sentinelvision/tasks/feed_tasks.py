import logging
import requests
import traceback
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Q, F
from sentinelvision.models import FeedRegistry, FeedModule, FeedExecutionRecord, ExecutionSourceEnum, ExecutionStatusEnum
from companies.models import Company
from sentinelvision.feeds import get_feed_class
from sentinelvision.logging import get_structured_logger
from io import StringIO

# Get structured JSON logger
logger = get_structured_logger('sentinelvision.feeds')


@shared_task(
    bind=True,
    rate_limit="10/m",
    acks_late=True,
    max_retries=5,
    retry_backoff=True,
    default_retry_delay=60,
    queue="feeds",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5}
)
def update_feed(self, feed_id):
    """
    Update a specific feed by ID with throttling and resilience.
    
    Args:
        feed_id (str): UUID of the feed to update
    """
    try:
        # Get feed registry entry
        feed_registry = FeedRegistry.objects.get(id=feed_id, enabled=True)
        
        logger.info(
            f"Starting feed update for {feed_registry.name}",
            extra={
                'feed_name': feed_registry.name,
                'feed_id': str(feed_registry.id),
                'tenant_id': str(feed_registry.company.id),
                'feed_type': feed_registry.feed_type
            }
        )
        
        # Mark as syncing
        feed_registry.mark_sync_started()
        
        # Get feed class
        feed_class = get_feed_class(feed_registry.feed_type)
        if not feed_class:
            error_msg = f"No feed class found for type {feed_registry.feed_type}"
            logger.error(
                error_msg,
                extra={
                    'feed_name': feed_registry.name,
                    'feed_id': str(feed_registry.id),
                    'tenant_id': str(feed_registry.company.id)
                }
            )
            feed_registry.mark_sync_failure(error_msg)
            return {
                'status': 'error',
                'feed_name': feed_registry.name,
                'error': error_msg
            }
        
        # Get or create feed instance
        feed_instance, created = feed_class.objects.get_or_create(
            company=feed_registry.company,
            feed_type=feed_registry.feed_type,
            feed_url=feed_registry.source_url,
            defaults={'is_active': True}
        )
        
        if not feed_instance.is_active:
            error_msg = f"Feed instance for {feed_registry.name} is not active"
            logger.error(
                error_msg,
                extra={
                    'feed_name': feed_registry.name,
                    'feed_id': str(feed_registry.id),
                    'tenant_id': str(feed_registry.company.id)
                }
            )
            feed_registry.mark_sync_failure(error_msg)
            return {
                'status': 'error',
                'feed_name': feed_registry.name,
                'error': error_msg
            }
        
        # Update the feed
        result = feed_instance.update_feed()
        
        if result.get('status') == 'success':
            processed_count = result.get('processed_count', 0)
            feed_registry.mark_sync_success(processed_count)
            
            logger.info(
                f"Successfully updated feed {feed_registry.name}: {processed_count} IOCs processed",
                extra={
                    'feed_name': feed_registry.name,
                    'feed_id': str(feed_registry.id),
                    'tenant_id': str(feed_registry.company.id),
                    'processed_count': processed_count
                }
            )
            
            return {
                'status': 'success',
                'feed_name': feed_registry.name,
                'processed_count': processed_count
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            feed_registry.mark_sync_failure(error_msg)
            
            logger.error(
                f"Error updating feed {feed_registry.name}: {error_msg}",
                extra={
                    'feed_name': feed_registry.name,
                    'feed_id': str(feed_registry.id),
                    'tenant_id': str(feed_registry.company.id),
                    'error': error_msg
                }
            )
            
            # Raise exception to trigger retry
            raise Exception(f"Feed update failed: {error_msg}")
    
    except FeedRegistry.DoesNotExist:
        logger.error(
            f"Feed with ID {feed_id} not found or not active",
            extra={'feed_id': feed_id}
        )
        return {
            'status': 'error',
            'error': f"Feed with ID {feed_id} not found or not active"
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Exception updating feed {feed_id}: {error_msg}",
            extra={
                'feed_id': feed_id,
                'error': error_msg,
                'traceback': traceback.format_exc()
            },
            exc_info=True
        )
        
        # Update feed registry if available
        try:
            if 'feed_registry' in locals():
                feed_registry.mark_sync_failure(error_msg)
        except Exception:
            pass
        
        # Retry with backoff
        self.retry(exc=e)
        
        return {
            'status': 'error',
            'error': error_msg,
            'is_retrying': True
        }


@shared_task(queue="feeds")
def schedule_pending_feeds():
    """
    Scan for feeds that are due for update and schedule them.
    """
    now = timezone.now()
    
    # Find feeds that are enabled and due for update
    due_feeds = FeedRegistry.objects.filter(
        enabled=True,
        next_sync__lte=now,
        sync_status__in=[
            FeedRegistry.SyncStatus.PENDING,
            FeedRegistry.SyncStatus.SUCCESS,
            FeedRegistry.SyncStatus.FAILURE
        ]
    )
    
    logger.info(
        f"Found {due_feeds.count()} feeds due for update",
        extra={'due_feeds_count': due_feeds.count()}
    )
    
    scheduled_count = 0
    
    # Schedule each feed for update
    for feed in due_feeds:
        logger.info(
            f"Scheduling update for feed: {feed.name}",
            extra={
                'feed_name': feed.name,
                'feed_id': str(feed.id),
                'tenant_id': str(feed.company.id)
            }
        )
        
        # Schedule update task
        update_feed.apply_async(
            args=[str(feed.id)],
            expires=3600  # Expire task after 1 hour if not executed
        )
        
        scheduled_count += 1
    
    return {
        'status': 'success',
        'scheduled_count': scheduled_count,
        'total_due': due_feeds.count()
    }


@shared_task(queue="feeds")
def retry_failed_feeds():
    """
    Retry feeds that failed in the last 24 hours.
    """
    retry_threshold = timezone.now() - timedelta(hours=24)
    
    # Find recently failed feeds
    failed_feeds = FeedRegistry.objects.filter(
        enabled=True,
        sync_status=FeedRegistry.SyncStatus.FAILURE,
        last_sync__gte=retry_threshold
    )
    
    logger.info(
        f"Found {failed_feeds.count()} failed feeds to retry",
        extra={'failed_feeds_count': failed_feeds.count()}
    )
    
    retry_count = 0
    
    # Retry each failed feed
    for feed in failed_feeds:
        logger.info(
            f"Scheduling retry for failed feed: {feed.name}",
            extra={
                'feed_name': feed.name,
                'feed_id': str(feed.id),
                'tenant_id': str(feed.company.id),
                'last_error': feed.last_error[:100]  # Truncate for logging
            }
        )
        
        # Schedule update task with higher priority
        update_feed.apply_async(
            args=[str(feed.id)],
            priority=5,  # Higher priority for retries
            expires=3600  # Expire task after 1 hour if not executed
        )
        
        retry_count += 1
    
    return {
        'status': 'success',
        'retry_count': retry_count,
        'total_failed': failed_feeds.count()
    }


@shared_task(
    bind=True,
    rate_limit="15/h",
    acks_late=True,
    max_retries=3,
    retry_backoff=True,
    default_retry_delay=300,
    queue="sentineliq_soar_vision_feed",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3}
)
def update_ssl_blacklist_feed(self, company_id=None):
    """
    Update SSL Certificate Blacklist from abuse.ch
    
    Args:
        company_id: Optional UUID of specific company to update for
    """
    logger.info(
        "Starting SSL Certificate Blacklist feed update",
        extra={'feed_type': 'ssl_blacklist', 'company_id': company_id}
    )
    
    try:
        # If company_id provided, only update for that company
        if company_id:
            companies = Company.objects.filter(id=company_id)
        else:
            # Otherwise update for all companies
            companies = Company.objects.all()
        
        if not companies.exists():
            logger.warning(
                "No companies found for SSL Blacklist feed update",
                extra={'feed_type': 'ssl_blacklist', 'company_id': company_id}
            )
            return {
                'status': 'warning',
                'message': 'No companies found'
            }
        
        results = []
        
        # Process for each company
        for company in companies:
            # Get SSL Blacklist feed class
            feed_class = get_feed_class('ssl_blacklist')
            if not feed_class:
                error_msg = "SSL Blacklist feed class not found"
                logger.error(error_msg)
                continue
                
            # Get or create feed instance
            feed_instance, created = feed_class.objects.get_or_create(
                company=company,
                defaults={
                    'name': 'SSL Certificate Blacklist',
                    'feed_url': 'https://sslbl.abuse.ch/blacklist/sslblacklist.csv',
                    'description': 'SSL Certificate Blacklist from abuse.ch',
                    'interval_hours': 12,
                    'is_active': True,
                    'auto_mark_as_ioc': True
                }
            )
            
            # Update FeedRegistry to track status
            feed_registry, created = FeedRegistry.objects.get_or_create(
                company=company,
                name='SSL Certificate Blacklist',
                feed_type='ssl_blacklist',
                defaults={
                    'source_url': 'https://sslbl.abuse.ch/blacklist/sslblacklist.csv',
                    'description': 'SSL fingerprints associated with malware and botnet C&C',
                    'sync_interval_hours': 12,
                    'enabled': True
                }
            )
            
            # Mark as syncing
            feed_registry.mark_sync_started()
            
            # Run the update
            result = feed_instance.update_feed()
            
            # Update registry status
            if result.get('status') == 'success':
                processed_count = result.get('processed_count', 0)
                feed_registry.mark_sync_success(processed_count)
                
                logger.info(
                    f"Successfully updated SSL Blacklist feed for {company.name}: {processed_count} IOCs processed",
                    extra={
                        'feed_name': 'SSL Certificate Blacklist',
                        'company_name': company.name,
                        'company_id': str(company.id),
                        'processed_count': processed_count
                    }
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                feed_registry.mark_sync_failure(error_msg)
                
                logger.error(
                    f"Error updating SSL Blacklist feed for {company.name}: {error_msg}",
                    extra={
                        'feed_name': 'SSL Certificate Blacklist',
                        'company_name': company.name,
                        'company_id': str(company.id),
                        'error': error_msg
                    }
                )
            
            results.append({
                'company': company.name,
                'status': result.get('status'),
                'processed_count': result.get('processed_count', 0)
            })
        
        return {
            'status': 'success',
            'companies_processed': len(results),
            'results': results
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Exception in SSL Blacklist feed update: {error_msg}",
            extra={
                'feed_type': 'ssl_blacklist',
                'company_id': company_id,
                'error': error_msg
            },
            exc_info=True
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
    rate_limit="15/h",
    acks_late=True,
    max_retries=3,
    retry_backoff=True,
    default_retry_delay=300,
    queue="sentineliq_soar_vision_feed",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3}
)
def dynamic_feed_update(self, feed_type, company_id=None):
    """
    Dynamically update any feed type based on the feed registry.
    
    Args:
        feed_type: The type/ID of the feed to update
        company_id: Optional UUID of specific company to update for
    """
    from sentinelvision.feeds import get_feed_class
    
    logger.info(
        f"Starting dynamic feed update for {feed_type}",
        extra={'feed_type': feed_type, 'company_id': company_id}
    )
    
    try:
        # Get the feed class from the registry
        feed_class = get_feed_class(feed_type)
        
        if not feed_class:
            logger.error(
                f"Feed type '{feed_type}' not found in registry",
                extra={'feed_type': feed_type}
            )
            return {
                'status': 'error',
                'error': f"Feed type '{feed_type}' not found in registry"
            }
        
        # If company_id provided, only update for that company
        if company_id:
            companies = Company.objects.filter(id=company_id)
        else:
            # Otherwise update for all companies
            companies = Company.objects.all()
        
        if not companies.exists():
            logger.warning(
                f"No companies found for {feed_type} update",
                extra={'feed_type': feed_type, 'company_id': company_id}
            )
            return {
                'status': 'warning',
                'message': 'No companies found'
            }
        
        results = []
        
        # Process for each company
        for company in companies:
            # Ensure feed module exists 
            feed_instance, created = feed_class.objects.get_or_create(
                company=company,
                defaults={
                    'name': feed_class._meta.verbose_name,
                    'description': feed_class.__doc__.strip() if feed_class.__doc__ else '',
                    'is_active': True
                }
            )
            
            # Update or create FeedRegistry to track status
            feed_registry, created = FeedRegistry.objects.get_or_create(
                company=company,
                name=feed_class._meta.verbose_name,
                feed_type=feed_type,
                defaults={
                    'source_url': feed_instance.feed_url,
                    'description': feed_class.__doc__.strip() if feed_class.__doc__ else '',
                    'sync_interval_hours': feed_instance.interval_hours,
                    'enabled': True
                }
            )
            
            # Mark as syncing
            feed_registry.mark_sync_started()
            
            # Run the update
            result = feed_instance.update_feed()
            
            # Update registry status
            if result.get('status') == 'success':
                processed_count = result.get('processed_count', 0)
                feed_registry.mark_sync_success(processed_count)
                
                logger.info(
                    f"Successfully updated {feed_type} feed for {company.name}: {processed_count} IOCs processed",
                    extra={
                        'feed_name': feed_class._meta.verbose_name,
                        'feed_type': feed_type,
                        'company_name': company.name,
                        'company_id': str(company.id),
                        'processed_count': processed_count
                    }
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                feed_registry.mark_sync_failure(error_msg)
                
                logger.error(
                    f"Error updating {feed_type} feed for {company.name}: {error_msg}",
                    extra={
                        'feed_name': feed_class._meta.verbose_name,
                        'feed_type': feed_type,
                        'company_name': company.name,
                        'company_id': str(company.id),
                        'error': error_msg
                    }
                )
            
            results.append({
                'company': company.name,
                'status': result.get('status'),
                'processed_count': result.get('processed_count', 0)
            })
        
        return {
            'status': 'success',
            'feed_type': feed_type,
            'companies_processed': len(results),
            'results': results
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Exception in {feed_type} feed update: {error_msg}",
            extra={
                'feed_type': feed_type,
                'company_id': company_id,
                'error': error_msg
            },
            exc_info=True
        )
        
        # Retry with backoff
        self.retry(exc=e)
        
        return {
            'status': 'error',
            'feed_type': feed_type,
            'error': error_msg,
            'is_retrying': True
        }


@shared_task(queue="sentineliq_soar_vision_feed")
def schedule_all_feeds():
    """
    Schedule updates for all feed types registered in the system.
    """
    from sentinelvision.feeds import get_all_feeds
    
    # Get all registered feed types
    feed_registry = get_all_feeds()
    
    logger.info(
        f"Scheduling updates for {len(feed_registry)} feed types",
        extra={'feed_count': len(feed_registry)}
    )
    
    results = []
    
    # Schedule each feed type
    for feed_id, feed_class in feed_registry.items():
        logger.info(
            f"Scheduling {feed_id} feed update",
            extra={'feed_id': feed_id}
        )
        
        # Schedule task to update this feed type
        task_result = dynamic_feed_update.apply_async(
            args=[feed_id],
            expires=3600  # Expire task after 1 hour if not executed
        )
        
        results.append({
            'feed_type': feed_id,
            'task_id': task_result.id
        })
    
    return {
        'status': 'scheduled',
        'feeds_scheduled': len(results),
        'feed_results': results
    }


@shared_task(
    queue="sentineliq_soar_vision_feed"
)
def update_all_feeds():
    """
    Update all enabled feeds in the system.
    """
    logger.info("Starting update of all enabled feeds")
    
    # Get all active feeds
    feeds = FeedRegistry.objects.filter(enabled=True)
    
    if not feeds.exists():
        logger.warning("No enabled feeds found")
        return {
            'status': 'warning',
            'message': 'No enabled feeds found'
        }
    
    results = []
    
    for feed in feeds:
        try:
            # Get feed class
            feed_class = get_feed_class(feed.feed_type)
            if not feed_class:
                logger.error(
                    f"Feed type '{feed.feed_type}' not found",
                    extra={'feed_name': feed.name, 'feed_type': feed.feed_type}
                )
                continue
            
            # Get feed instance
            feed_instance = feed_class.objects.filter(
                company=feed.company,
                is_active=True
            ).first()
            
            if not feed_instance:
                logger.error(
                    f"No active feed instance found for {feed.name}",
                    extra={'feed_name': feed.name, 'feed_type': feed.feed_type}
                )
                continue
            
            # Check if feed is due for update
            if feed_instance.is_due_for_update:
                logger.info(
                    f"Updating feed: {feed.name}",
                    extra={'feed_name': feed.name, 'feed_type': feed.feed_type}
                )
                
                # Update the feed
                result = feed_instance.update_feed()
                
                results.append({
                    'feed_name': feed.name,
                    'feed_type': feed.feed_type,
                    'status': result.get('status'),
                    'processed_count': result.get('processed_count', 0)
                })
            else:
                logger.info(
                    f"Feed {feed.name} is not due for update yet",
                    extra={'feed_name': feed.name, 'feed_type': feed.feed_type}
                )
        
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Exception updating feed {feed.name}: {error_msg}",
                extra={
                    'feed_name': feed.name,
                    'feed_type': feed.feed_type,
                    'error': error_msg
                },
                exc_info=True
            )
            
            results.append({
                'feed_name': feed.name,
                'feed_type': feed.feed_type,
                'status': 'error',
                'error': error_msg
            })
    
    # Calculate statistics
    success_count = sum(1 for r in results if r.get('status') == 'success')
    error_count = sum(1 for r in results if r.get('status') == 'error')
    total_processed = sum(r.get('processed_count', 0) for r in results)
    
    logger.info(
        f"Feed update completed",
        extra={
            'success_count': success_count,
            'error_count': error_count,
            'total_processed': total_processed
        }
    )
    
    return {
        'status': 'completed',
        'success_count': success_count,
        'error_count': error_count,
        'total_processed': total_processed,
        'total_feeds': len(feeds),
        'results': results
    }


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


@shared_task(
    bind=True,
    name='sentinelvision.tasks.reprocess_tenant_iocs',
    acks_late=True,
    queue="sentineliq_soar_vision_enrichment"
)
def reprocess_tenant_iocs(self, days=7, limit=500):
    """
    Reprocess IOCs for all tenants to ensure enrichment with the latest feed data.
    
    This scheduled task runs every 30 minutes and ensures that IOCs submitted earlier
    can still be enriched with feed data that was added later.
    
    Args:
        days (int): Number of days back to look for IOCs to reprocess
        limit (int): Maximum number of IOCs to process per tenant
        
    Returns:
        dict: Results of the reprocessing operation
    """
    from companies.models import Company
    from sentinelvision.models import EnrichedIOC
    from sentinelvision.tasks.enrichment_tasks import enrich_ioc_batch
    from django.utils import timezone
    import time
    
    start_time = time.time()
    logger.info(
        f"Starting tenant IOC reprocessing (days={days}, limit={limit})",
        extra={'days': days, 'limit': limit}
    )
    
    # Get all active companies/tenants
    companies = Company.objects.filter(is_active=True)
    
    results = {
        'total_companies': companies.count(),
        'processed_companies': 0,
        'total_iocs_reprocessed': 0,
        'errors': 0,
        'company_results': []
    }
    
    # Define the cutoff date for IOCs to reprocess
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # Process each company
    for company in companies:
        company_result = {
            'company_id': str(company.id),
            'company_name': company.name,
            'iocs_processed': 0,
            'status': 'success'
        }
        
        try:
            logger.info(
                f"Reprocessing IOCs for company: {company.name}",
                extra={
                    'company_id': str(company.id),
                    'company_name': company.name
                }
            )
            
            # Get IOCs to reprocess for this tenant (oldest first)
            # - IOCs with pending status
            # - IOCs with last_checked older than the threshold
            # - Limit to specified number to avoid overwhelming the system
            iocs = EnrichedIOC.objects.filter(
                company=company
            ).filter(
                Q(status='pending') | 
                Q(last_checked__lt=cutoff_date)
            ).order_by(
                'last_checked'
            )[:limit]
            
            if iocs.exists():
                # Get IDs for batch processing
                ioc_ids = list(iocs.values_list('id', flat=True))
                
                # Call the enrichment task
                enrich_task = enrich_ioc_batch.delay(
                    company_id=str(company.id),
                    ioc_ids=ioc_ids
                )
                
                company_result['iocs_processed'] = len(ioc_ids)
                company_result['task_id'] = enrich_task.id
                
                results['total_iocs_reprocessed'] += len(ioc_ids)
                
                logger.info(
                    f"Scheduled {len(ioc_ids)} IOCs for reprocessing for company {company.name}",
                    extra={
                        'company_id': str(company.id),
                        'company_name': company.name,
                        'ioc_count': len(ioc_ids),
                        'task_id': enrich_task.id
                    }
                )
            else:
                logger.info(
                    f"No IOCs found for reprocessing for company {company.name}",
                    extra={
                        'company_id': str(company.id),
                        'company_name': company.name
                    }
                )
        
        except Exception as e:
            company_result['status'] = 'error'
            company_result['error'] = str(e)
            results['errors'] += 1
            
            logger.error(
                f"Error reprocessing IOCs for company {company.name}: {str(e)}",
                extra={
                    'company_id': str(company.id),
                    'company_name': company.name,
                    'error': str(e)
                },
                exc_info=True
            )
        
        results['processed_companies'] += 1
        results['company_results'].append(company_result)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    results['execution_time_seconds'] = execution_time
    
    logger.info(
        f"Tenant IOC reprocessing completed in {execution_time:.2f}s. "
        f"Reprocessed {results['total_iocs_reprocessed']} IOCs across {results['processed_companies']} companies.",
        extra={
            'execution_time': execution_time,
            'total_iocs': results['total_iocs_reprocessed'],
            'total_companies': results['processed_companies'],
            'errors': results['errors']
        }
    )
    
    return results 