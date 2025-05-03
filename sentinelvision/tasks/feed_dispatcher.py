import logging
from celery import shared_task
from django.utils import timezone
from typing import Dict, List, Optional, Union
from companies.models import Company

logger = logging.getLogger('sentinelvision.feeds.dispatcher')

@shared_task(
    bind=True,
    name="sentinelvision.tasks.feed_dispatcher.update_all_feeds",
    rate_limit="2/m",
    queue="sentineliq_soar_vision_feed"
)
def update_all_feeds(self, company_id: Optional[str] = None, feed_types: Optional[List[str]] = None, 
                    concurrent: bool = False, timeout: int = 3600) -> Dict:
    """
    Centralized dispatcher that discovers and updates all registered feed modules.
    
    This task acts as the main orchestrator for all feed updates, respecting multi-tenancy
    and following the established pattern for modular task execution.
    
    Args:
        company_id: Optional UUID of specific company to update for
        feed_types: Optional list of specific feed types to update (default: all)
        concurrent: Whether to execute feeds concurrently (default: False)
        timeout: Timeout for task execution in seconds (default: 1 hour)
    
    Returns:
        Dict containing execution results for all feeds
    """
    from sentinelvision.feeds import get_all_feeds, get_feed_task
    
    # Get all registered feed classes
    feed_registry = get_all_feeds()
    
    # Filter to requested feed types if specified
    if feed_types:
        feed_registry = {k: v for k, v in feed_registry.items() if k in feed_types}
    
    logger.info(
        f"Starting update for {len(feed_registry)} feed types",
        extra={
            'company_id': company_id,
            'feed_count': len(feed_registry),
            'concurrent': concurrent,
            'feed_types': list(feed_registry.keys())
        }
    )
    
    # Verify company if specified
    if company_id:
        company_exists = Company.objects.filter(id=company_id).exists()
        if not company_exists:
            error_msg = f"Company with ID {company_id} not found"
            logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }
    
    # Track execution results
    results = []
    task_ids = {}
    
    # Schedule each feed type update
    for feed_id, feed_class in feed_registry.items():
        logger.info(
            f"Scheduling {feed_id} feed update",
            extra={'feed_id': feed_id, 'company_id': company_id}
        )
        
        # Get the dedicated task for this feed
        feed_task = get_feed_task(feed_id)
        
        if not feed_task:
            logger.error(
                f"No task registered for feed: {feed_id}",
                extra={'feed_id': feed_id}
            )
            results.append({
                'feed_id': feed_id,
                'status': 'error',
                'error': f"No task registered for feed: {feed_id}"
            })
            continue
        
        try:
            # Apply the task asynchronously with the company_id if provided
            kwargs = {'company_id': company_id} if company_id else {}
            
            # Execute the task
            task_result = feed_task.apply_async(
                kwargs=kwargs,
                expires=timeout
            )
            
            task_ids[feed_id] = task_result.id
            
            # If not concurrent, wait for this task to complete before scheduling the next
            if not concurrent:
                try:
                    # Wait for the task to complete with timeout
                    task_result = task_result.get(timeout=timeout, propagate=False)
                    
                    results.append({
                        'feed_id': feed_id,
                        'status': 'success' if task_result and task_result.get('status') == 'success' else 'error',
                        'task_id': task_ids[feed_id],
                        'result': task_result
                    })
                    
                    logger.info(
                        f"Completed {feed_id} feed update: {task_result.get('status', 'unknown')}",
                        extra={
                            'feed_id': feed_id,
                            'task_id': task_ids[feed_id],
                            'status': task_result.get('status', 'unknown')
                        }
                    )
                except Exception as e:
                    results.append({
                        'feed_id': feed_id,
                        'status': 'error',
                        'task_id': task_ids[feed_id],
                        'error': str(e)
                    })
                    
                    logger.error(
                        f"Error waiting for {feed_id} feed task: {str(e)}",
                        extra={
                            'feed_id': feed_id,
                            'task_id': task_ids[feed_id],
                            'error': str(e)
                        },
                        exc_info=True
                    )
            else:
                # For concurrent execution, just track that the task was scheduled
                results.append({
                    'feed_id': feed_id,
                    'status': 'scheduled',
                    'task_id': task_ids[feed_id]
                })
        except Exception as e:
            logger.error(
                f"Failed to schedule {feed_id} feed update: {str(e)}",
                extra={'feed_id': feed_id, 'error': str(e)},
                exc_info=True
            )
            
            results.append({
                'feed_id': feed_id,
                'status': 'error',
                'error': str(e)
            })
    
    # For concurrent execution, return task IDs so they can be checked later
    if concurrent:
        return {
            'status': 'scheduled',
            'scheduled_at': timezone.now().isoformat(),
            'feeds_scheduled': len(task_ids),
            'task_ids': task_ids,
            'results': results
        }
    
    # For sequential execution, return complete results
    successful = sum(1 for r in results if r.get('status') == 'success')
    failed = sum(1 for r in results if r.get('status') == 'error')
    
    return {
        'status': 'complete',
        'completed_at': timezone.now().isoformat(),
        'feeds_processed': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    }

@shared_task(
    bind=True,
    name="sentinelvision.tasks.feed_dispatcher.check_feed_status",
    queue="sentineliq_soar_vision_feed"
)
def check_feed_status(self, task_ids: Dict[str, str]) -> Dict:
    """
    Check the status of previously scheduled feed tasks.
    
    Args:
        task_ids: Dictionary mapping feed_id to task_id
        
    Returns:
        Dict containing status results for all tasks
    """
    from celery.result import AsyncResult
    
    results = []
    
    for feed_id, task_id in task_ids.items():
        try:
            # Get the task result
            result = AsyncResult(task_id)
            
            # Check the status
            if result.ready():
                if result.successful():
                    task_result = result.get()
                    results.append({
                        'feed_id': feed_id,
                        'status': 'success',
                        'task_id': task_id,
                        'result': task_result
                    })
                else:
                    results.append({
                        'feed_id': feed_id,
                        'status': 'error',
                        'task_id': task_id,
                        'error': str(result.result)
                    })
            else:
                results.append({
                    'feed_id': feed_id,
                    'status': 'pending',
                    'task_id': task_id
                })
        except Exception as e:
            results.append({
                'feed_id': feed_id,
                'status': 'error',
                'task_id': task_id,
                'error': str(e)
            })
    
    # Calculate summary
    total = len(results)
    complete = sum(1 for r in results if r.get('status') in ('success', 'error'))
    successful = sum(1 for r in results if r.get('status') == 'success')
    failed = sum(1 for r in results if r.get('status') == 'error')
    pending = sum(1 for r in results if r.get('status') == 'pending')
    
    return {
        'status': 'complete' if complete == total else 'partial',
        'total': total,
        'complete': complete,
        'successful': successful,
        'failed': failed,
        'pending': pending,
        'results': results
    } 