import os
import importlib
import inspect
import pkgutil
import sys
import logging
from typing import Dict, Type, List
from django.apps import apps
from functools import wraps
from celery import shared_task
from sentinelvision.models import FeedModule

# Feed registry to store all available feed classes
FEED_REGISTRY = {}

# Task registry to store all feed tasks
TASK_REGISTRY = {}

def register_feed(feed_class):
    """
    Register a feed class in the registry.
    
    Args:
        feed_class: The feed class to register
    """
    feed_id = getattr(feed_class, 'feed_id', feed_class.__name__.lower())
    FEED_REGISTRY[feed_id] = feed_class
    
    # Automatically create and register a task for this feed
    register_feed_task(feed_id, feed_class)
    
    return feed_class

def register_feed_task(feed_id, feed_class):
    """
    Dynamically create and register a Celery task for a feed.
    
    Args:
        feed_id: ID of the feed
        feed_class: The feed class
    """
    task_name = f"sentinelvision.feeds.{feed_id}.update"
    
    # Define the feed task dynamically with correct docstring
    def feed_task_function(self, company_id=None):
        """Dynamically created task for updating a specific feed type."""
        import logging
        from django.utils import timezone
        from companies.models import Company
        from sentinelvision.models import FeedRegistry
        
        logger = logging.getLogger('sentinelvision.feeds')
        
        logger.info(
            f"Starting {feed_id} feed update",
            extra={'feed_type': feed_id, 'company_id': company_id}
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
                    f"No companies found for {feed_id} update",
                    extra={'feed_type': feed_id, 'company_id': company_id}
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
                    feed_type=feed_id,
                    defaults={
                        'source_url': getattr(feed_instance, 'feed_url', ''),
                        'description': feed_class.__doc__.strip() if feed_class.__doc__ else '',
                        'sync_interval_hours': getattr(feed_instance, 'interval_hours', 24),
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
                        f"Successfully updated {feed_id} feed for {company.name}: {processed_count} IOCs processed",
                        extra={
                            'feed_name': feed_class._meta.verbose_name,
                            'feed_type': feed_id,
                            'company_name': company.name,
                            'company_id': str(company.id),
                            'processed_count': processed_count
                        }
                    )
                else:
                    error_msg = result.get('error', 'Unknown error')
                    feed_registry.mark_sync_failure(error_msg)
                    
                    logger.error(
                        f"Error updating {feed_id} feed for {company.name}: {error_msg}",
                        extra={
                            'feed_name': feed_class._meta.verbose_name,
                            'feed_type': feed_id,
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
                'feed_type': feed_id,
                'companies_processed': len(results),
                'results': results
            }
        
        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(
                f"Exception in {feed_id} feed update: {error_msg}",
                extra={
                    'feed_type': feed_id,
                    'company_id': company_id,
                    'error': error_msg,
                    'traceback': traceback.format_exc()
                },
                exc_info=True
            )
            
            # Retry with backoff
            self.retry(exc=e)
            
            return {
                'status': 'error',
                'feed_type': feed_id,
                'error': error_msg,
                'is_retrying': True
            }
    
    # Create the Celery task with the predefined name
    feed_task = shared_task(
        bind=True,
        name=task_name,
        rate_limit="10/h",
        acks_late=True,
        max_retries=3,
        retry_backoff=True,
        default_retry_delay=300,
        queue="sentineliq_soar_vision_feed"
    )(feed_task_function)
    
    # Add documentation to the task
    feed_task.__doc__ = f"""
    Auto-generated task for updating the {feed_class._meta.verbose_name}.
    
    This task processes data from the feed and imports it as observables.
    
    Args:
        company_id: Optional UUID of specific company to update for
    """
    
    # Store the task in our registry
    TASK_REGISTRY[feed_id] = feed_task
    
    return feed_task

def get_feed_class(feed_id):
    """
    Get a feed class by its ID.
    
    Args:
        feed_id: The ID of the feed class
        
    Returns:
        The feed class or None if not found
    """
    return FEED_REGISTRY.get(feed_id)

def get_feed_task(feed_id):
    """
    Get a feed task by its feed ID.
    
    Args:
        feed_id: The ID of the feed
        
    Returns:
        The Celery task function or None if not found
    """
    return TASK_REGISTRY.get(feed_id)

def get_all_feeds():
    """
    Get all registered feed classes.
    
    Returns:
        Dict of feed classes with their IDs as keys
    """
    return FEED_REGISTRY

def get_all_feed_tasks():
    """
    Get all registered feed tasks.
    
    Returns:
        Dict of feed task functions with feed IDs as keys
    """
    return TASK_REGISTRY

def discover_feeds():
    """
    Dynamically discover and register all feed modules.
    This searches for feed modules in the sentinelvision/feeds/ directory.
    """
    logger = logging.getLogger('sentinelvision.feeds')
    
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_name = __name__
    
    # Log discovery start
    logger.info(f"Discovering feed modules in {current_dir}")
    
    # Method 1: Find all Python files ending with _feed.py
    discovered_modules = set()
    for filename in os.listdir(current_dir):
        if filename.endswith('_feed.py') and not filename.startswith('__'):
            module_name = filename[:-3]  # Remove .py extension
            module_path = f"{package_name}.{module_name}"
            discovered_modules.add(module_path)
            
            try:
                # Import the module
                module = importlib.import_module(module_path)
                
                # Find feed classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        obj.__module__ == module_path and 
                        issubclass(obj, FeedModule) and 
                        obj != FeedModule and
                        not obj._meta.abstract):
                        
                        # Register the feed class if not already registered
                        feed_id = getattr(obj, 'feed_id', obj.__name__.lower())
                        if feed_id not in FEED_REGISTRY:
                            register_feed(obj)
                            logger.info(f"Registered feed module: {feed_id} ({obj.__name__})")
                        
            except Exception as e:
                logger.error(
                    f"Error loading feed module {module_name}: {str(e)}",
                    exc_info=True
                )
    
    # Method 2: Use pkgutil to find all modules in the package
    for _, name, is_pkg in pkgutil.iter_modules([current_dir]):
        if not is_pkg and name.endswith('_feed') and not name.startswith('__'):
            module_path = f"{package_name}.{name}"
            
            # Skip if already imported via Method 1
            if module_path in discovered_modules:
                continue
                
            try:
                # Import the module
                module = importlib.import_module(module_path)
                
                # Find feed classes in the module
                for class_name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        obj.__module__ == module_path and 
                        issubclass(obj, FeedModule) and 
                        obj != FeedModule and
                        not obj._meta.abstract):
                        
                        # Register the feed class if not already registered
                        feed_id = getattr(obj, 'feed_id', obj.__name__.lower())
                        if feed_id not in FEED_REGISTRY:
                            register_feed(obj)
                            logger.info(f"Registered feed module via pkgutil: {feed_id} ({obj.__name__})")
                    
            except Exception as e:
                logger.error(
                    f"Error loading feed module {name} via pkgutil: {str(e)}",
                    exc_info=True
                )
    
    # Method 3: Attempt to directly import known feed modules if they weren't found
    known_feeds = ['ssl_blacklist_feed', 'alienvault_reputation_feed', 'blocklist_de_feed']
    for feed_module in known_feeds:
        module_path = f"{package_name}.{feed_module}"
        
        # Skip if already imported
        if module_path in discovered_modules:
            continue
            
        try:
            # Import the module
            module = importlib.import_module(module_path)
            
            # Find feed classes in the module
            for class_name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    obj.__module__ == module_path and 
                    issubclass(obj, FeedModule) and 
                    obj != FeedModule and
                    not obj._meta.abstract):
                    
                    # Register the feed class if not already registered
                    feed_id = getattr(obj, 'feed_id', obj.__name__.lower())
                    if feed_id not in FEED_REGISTRY:
                        register_feed(obj)
                        logger.info(f"Registered known feed module: {feed_id} ({obj.__name__})")
                
        except Exception as e:
            logger.error(
                f"Error loading known feed module {feed_module}: {str(e)}",
                exc_info=True
            )
    
    # Log discovery results
    logger.info(f"Feed module discovery complete. Found {len(FEED_REGISTRY)} feed modules: {', '.join(FEED_REGISTRY.keys())}")
    
    return FEED_REGISTRY

# Run feed discovery during module import
discover_feeds()
