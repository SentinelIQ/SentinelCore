from celery import shared_task
from django.utils import timezone
from sentinelvision.models import FeedRegistry
from sentinelvision.feeds import get_feed_class
from sentinelvision.logging import get_structured_logger

logger = get_structured_logger('sentinelvision.tasks')

@shared_task
def export_feed_data(feed_type, company_id=None):
    """
    Export data from a specific feed type.
    
    Args:
        feed_type (str): Type of feed to export
        company_id (UUID, optional): Specific company to export for
    """
    feed_class = get_feed_class(feed_type)
    if not feed_class:
        logger.error(f"Invalid feed type: {feed_type}")
        return
        
    if company_id:
        feeds = feed_class.objects.filter(company_id=company_id, is_active=True)
    else:
        feeds = feed_class.objects.filter(is_active=True)
        
    for feed in feeds:
        feed.export_data()

@shared_task
def update_specific_feed(feed_id):
    """
    Celery task to update a specific feed.
    
    Args:
        feed_id (str): UUID of the feed to update
    """
    try:
        # Get feed registry entry
        feed_registry = FeedRegistry.objects.get(id=feed_id, enabled=True)
        
        # Get feed class
        feed_class = get_feed_class(feed_registry.feed_type)
        if not feed_class:
            error_msg = f"Feed type '{feed_registry.feed_type}' not found"
            logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }
        
        # Get feed instance
        feed_instance = feed_class.objects.filter(
            id=feed_id,
            is_active=True
        ).first()
        
        if not feed_instance:
            error_msg = f"Feed with ID {feed_id} not found or not active"
            logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }
        
        logger.info(f"Manually updating feed: {feed_instance.name} ({feed_registry.feed_type})")
        
        # Update the feed
        result = feed_instance.update_feed()
        
        if result.get('status') == 'success':
            logger.info(f"Successfully updated feed {feed_instance.name}: {result.get('processed_count')} items processed")
            return {
                'status': 'success',
                'feed_name': feed_instance.name,
                'processed_count': result.get('processed_count', 0)
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Error updating feed {feed_instance.name}: {error_msg}")
            return {
                'status': 'error',
                'feed_name': feed_instance.name,
                'error': error_msg
            }
    
    except FeedRegistry.DoesNotExist:
        error_msg = f"Feed registry with ID {feed_id} not found or not enabled"
        logger.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Exception updating feed {feed_id}: {error_msg}")
        return {
            'status': 'error',
            'error': error_msg
        }


@shared_task
def schedule_feed_type(feed_type):
    """
    Celery task to schedule updates for any feed type.
    This allows dynamic scheduling of different feed types.
    
    Args:
        feed_type: The type/ID of the feed to schedule
    """
    from sentinelvision.feeds import get_feed_task
    
    logger.info(f"Scheduling {feed_type} feed updates")
    
    # Get the task for this feed type
    feed_task = get_feed_task(feed_type)
    
    if not feed_task:
        logger.error(f"No task found for feed type: {feed_type}")
        return {
            'status': 'error',
            'feed_type': feed_type,
            'error': f"No task found for feed type: {feed_type}"
        }
    
    # Execute the feed-specific task
    result = feed_task.delay()
    
    logger.info(f"{feed_type} feed update scheduled: {result.id}")
    
    return {
        'status': 'scheduled',
        'feed_type': feed_type,
        'task_id': result.id
    }


@shared_task
def schedule_all_feeds():
    """
    Celery task to schedule updates for all registered feed types.
    This task should be scheduled to run periodically.
    """
    from sentinelvision.feeds import get_all_feed_tasks
    
    logger.info("Scheduling updates for all registered feed types")
    
    # Get all registered feed tasks
    feed_tasks = get_all_feed_tasks()
    
    results = []
    
    # Schedule each feed task
    for feed_id, feed_task in feed_tasks.items():
        logger.info(f"Scheduling {feed_id} feed update")
        
        # Execute the feed task
        result = feed_task.delay()
        
        results.append({
            'feed_type': feed_id,
            'task_id': result.id
        })
    
    logger.info(f"All feeds scheduled ({len(results)} feeds)")
    
    return {
        'status': 'scheduled',
        'feeds_scheduled': len(results),
        'feed_results': results
    }


@shared_task
def schedule_ssl_blacklist_update():
    """
    Celery task to schedule updates for the SSL Certificate Blacklist feed.
    This task should be scheduled to run periodically (e.g., every 12 hours).
    It will trigger the dedicated SSL blacklist feed task for all active companies.
    """
    return schedule_feed_type('ssl_blacklist')


@shared_task
def list_available_feed_tasks():
    """
    List all available feed tasks in the system.
    Useful for diagnostics and for providing a menu of available feeds.
    
    Returns:
        dict: A dictionary with info about all registered feed tasks
    """
    from sentinelvision.feeds import get_all_feeds, get_all_feed_tasks
    
    logger.info("Listing all available feed tasks")
    
    feeds = get_all_feeds()
    feed_tasks = get_all_feed_tasks()
    
    result = {
        'count': len(feed_tasks),
        'feeds': []
    }
    
    # Gather info about each feed module and its task
    for feed_id, feed_class in feeds.items():
        feed_info = {
            'feed_id': feed_id,
            'name': feed_class._meta.verbose_name,
            'description': feed_class.__doc__.strip() if feed_class.__doc__ else '',
            'task_name': f"sentinelvision.feeds.{feed_id}.update",
            'is_registered': feed_id in feed_tasks
        }
        result['feeds'].append(feed_info)
    
    return result 