from __future__ import absolute_import, unicode_literals
import os
from celery import Celery, current_app
from django.conf import settings
from celery.signals import worker_ready, beat_init, celeryd_init
import importlib
import logging
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')

# Create the Celery app
app = Celery('sentineliq')

# Namespace for all Celery-related configuration options
app.config_from_object('django.conf:settings', namespace='CELERY')

# Ensure proper character encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LANG'] = 'C.UTF-8'

# Load task modules from all registered Django app configs
# This will find all tasks.py files in each app
app.autodiscover_tasks()

# Import Celery signals for Sentry monitoring
import sentineliq.celery_signals

# Define the schedule for periodic tasks
app.conf.beat_schedule = {
    'check-cases-for-escalation': {
        'task': 'sentineliq.tasks.check_cases_for_escalation',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'check-for-expired-cases': {
        'task': 'sentineliq.tasks.check_for_expired_cases',
        'schedule': crontab(minute='30', hour='*/1'),  # Every hour at minute 30
    },
    'schedule-feed-modules': {
        'task': 'sentinelvision.tasks.schedule_feeds',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'reprocess-tenant-iocs': {
        'task': 'sentinelvision.tasks.reprocess_tenant_iocs',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    """
    Simple debug task to verify Celery is working correctly.
    """
    print(f'Request: {self.request!r}')
    return {'status': 'success', 'task_id': self.request.id}


@app.task(bind=True, name='sentineliq.test_sentry_task')
def test_sentry_task(self):
    """
    Task to test Sentry error reporting in Celery tasks.
    Deliberately raises an exception to verify error reporting.
    
    Only use for testing!
    """
    try:
        from .sentry import capture_message, set_context
        # Add task context that will appear in Sentry
        set_context("celery_task", {
            "task_id": self.request.id,
            "args": self.request.args,
            "kwargs": self.request.kwargs,
            "task_name": self.name,
        })
        capture_message("Test message from Celery task", level="info")
        
        # Trigger a test exception
        division_by_zero = 1 / 0
        return division_by_zero
    except Exception as e:
        # This will be reported to Sentry automatically
        raise


@celeryd_init.connect
def verify_task_modules(sender, **kwargs):
    """
    Signal handler that runs when Celery workers initialize.
    Ensures that all task modules are properly imported and tasks are registered.
    """
    logger = logging.getLogger('celery.worker')
    logger.info("Verifying task modules are properly loaded...")
    
    # Task modules that must be explicitly imported
    critical_task_modules = [
        'api.core.tasks',
        'mitre.tasks',
        'sentinelvision.tasks',  # Import the main tasks module
        'sentinelvision.tasks.feed_tasks',
        'sentinelvision.tasks.feed_dispatcher',  # Explicitly import the feed dispatcher
        'sentinelvision.tasks.enrichment_tasks',
        'notifications.tasks'
    ]
    
    for module_path in critical_task_modules:
        try:
            importlib.import_module(module_path)
            logger.info(f"Successfully imported task module: {module_path}")
        except ImportError as e:
            logger.error(f"Failed to import task module {module_path}: {str(e)}")
    
    # Ensure all dynamic feed modules are imported and registered
    try:
        # First import the registry module to ensure feed registration functions are available
        import sentinelvision.feeds
        
        # Then explicitly discover all feeds
        sentinelvision.feeds.discover_feeds()
        
        # Log discovered feeds and their tasks
        all_feeds = sentinelvision.feeds.get_all_feeds()
        all_feed_tasks = sentinelvision.feeds.get_all_feed_tasks()
        
        logger.info(f"Discovered {len(all_feeds)} feed modules")
        for feed_id, feed_class in all_feeds.items():
            task_name = f"sentinelvision.feeds.{feed_id}.update"
            if feed_id in all_feed_tasks:
                logger.info(f"Feed module registered: {feed_id} -> Task: {task_name}")
            else:
                logger.error(f"Feed module found but task not registered: {feed_id}")
    
    except Exception as e:
        logger.error(f"Error discovering feed modules: {str(e)}", exc_info=True)
    
    # Print all registered task names
    all_tasks = list(current_app.tasks.keys())
    logger.info(f"Total registered tasks: {len(all_tasks)}")
    for task_name in sorted(all_tasks):
        if not task_name.startswith('celery.'):
            logger.info(f"Registered task: {task_name}")


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """
    Signal handler that triggers when a Celery worker becomes available.
    
    This ensures all scheduled tasks run as soon as the system initializes,
    rather than waiting for their first scheduled execution.
    """
    logger = logging.getLogger('celery.task')
    logger.info("Worker ready - Initializing system")
    
    # Extract worker name from hostname
    worker_name = sender.hostname.split('@')[0]
    logger.info(f"Worker ready: {worker_name}")
    
    # Only process tasks specific to each worker's queue
    if worker_name == 'soar_setup' or worker_name == 'worker1':
        # For setup worker, trigger system initialization tasks
        try:
            # Run migrations first
            logger.info("Triggering database migration task")
            result = app.send_task(
                'api.core.tasks.run_migrations',
                queue='sentineliq_soar_setup'  # Ensure task goes to the setup queue
            )
            logger.info(f"Database migration task scheduled with ID: {result.id}")
            
            # Sync MITRE data
            logger.info("Triggering MITRE data sync")
            result = app.send_task(
                'mitre.tasks.sync_mitre_data',
                queue='sentineliq_soar_setup'
            )
            logger.info(f"MITRE data sync task scheduled with ID: {result.id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule setup tasks: {str(e)}")
    
    elif worker_name == 'soar_vision_feed':
        # For vision feed worker, trigger feed tasks
        try:
            # Schedule pending feeds
            logger.info("Triggering pending feeds scheduling")
            result = app.send_task(
                'sentinelvision.tasks.feed_tasks.schedule_pending_feeds',
                queue='sentineliq_soar_vision_feed'
            )
            logger.info(f"Feed scheduling task triggered with ID: {result.id}")
            
            # Trigger centralized feed dispatcher
            logger.info("Triggering centralized feed dispatcher")
            result = app.send_task(
                'sentinelvision.tasks.feed_dispatcher.update_all_feeds',
                kwargs={'concurrent': True},
                queue='sentineliq_soar_vision_feed'
            )
            logger.info(f"Centralized feed dispatcher triggered with ID: {result.id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule vision feed tasks: {str(e)}")
    
    elif worker_name == 'soar_vision_enrichment':
        # For vision enrichment worker, trigger enrichment tasks
        try:
            logger.info("Triggering observable reenrichment")
            result = app.send_task(
                'sentinelvision.tasks.enrichment_tasks.reenrich_observables',
                kwargs={'days': 7, 'limit': 200},
                queue='sentineliq_soar_vision_enrichment'
            )
            logger.info(f"Reenrichment task triggered with ID: {result.id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule vision enrichment tasks: {str(e)}")
    
    elif worker_name == 'soar_vision_analyzer':
        # For vision analyzer worker, trigger analyzer tasks
        try:
            logger.info("Initializing analyzer systems")
            # You can add analyzer-specific initialization tasks here
        except Exception as e:
            logger.error(f"Failed to initialize analyzer systems: {str(e)}")
    
    elif worker_name == 'soar_vision_responder':
        # For vision responder worker, trigger responder tasks
        try:
            logger.info("Initializing responder systems")
            # You can add responder-specific initialization tasks here
        except Exception as e:
            logger.error(f"Failed to initialize responder systems: {str(e)}")
    
    elif worker_name == 'soar_notification':
        # For notification worker, initialize notification systems
        try:
            logger.info("Initializing notification systems")
            # You can add notification-specific initialization tasks here
        except Exception as e:
            logger.error(f"Failed to initialize notification systems: {str(e)}")
    
    # For all workers, search for tasks in the beat schedule that belong to their queue
    try:
        beat_schedule = getattr(settings, 'CELERY_BEAT_SCHEDULE', {})
        worker_queue_map = {
            'soar_setup': 'sentineliq_soar_setup',
            'soar_vision_feed': 'sentineliq_soar_vision_feed',
            'soar_vision_enrichment': 'sentineliq_soar_vision_enrichment',
            'soar_vision_analyzer': 'sentineliq_soar_vision_analyzer',
            'soar_vision_responder': 'sentineliq_soar_vision_responder',
            'soar_notification': 'sentineliq_soar_notification',
            'worker1': 'celery'
        }
        
        # Get the queue for this worker
        current_queue = worker_queue_map.get(worker_name)
        if not current_queue:
            logger.info(f"No queue mapping for worker: {worker_name}")
            return
            
        # Find and run tasks for this worker's queue
        for task_name, task_config in beat_schedule.items():
            options = task_config.get('options', {})
            task_queue = options.get('queue')
            
            # Only run tasks for this worker's queue
            if task_queue == current_queue:
                task_path = task_config.get('task')
                kwargs = task_config.get('kwargs', {})
                
                logger.info(f"Triggering scheduled task: {task_path} for queue: {task_queue}")
                
                try:
                    result = app.send_task(task_path, kwargs=kwargs, **options)
                    logger.info(f"Successfully triggered task: {task_path}")
                except Exception as e:
                    logger.error(f"Failed to trigger task {task_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing beat schedule for worker {worker_name}: {str(e)}")


@beat_init.connect
def on_beat_init(sender, **kwargs):
    """
    Signal handler that triggers when Celery Beat initializes.
    
    Useful for verifying that the scheduler is working correctly,
    and for setting up any dynamic schedules.
    """
    logger = logging.getLogger('celery.beat')
    logger.info("Celery Beat initialized - Scheduler is active")
    
    # Log all registered periodic tasks
    beat_schedule = getattr(settings, 'CELERY_BEAT_SCHEDULE', {})
    logger.info(f"Registered {len(beat_schedule)} periodic tasks")
    
    for task_name, task_config in beat_schedule.items():
        task_path = task_config.get('task')
        schedule = task_config.get('schedule')
        logger.info(f"Scheduled task: {task_name} -> {task_path} ({schedule})")


# Example of how to set up dynamic periodic tasks when Celery is configured
# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     """
#     Configure additional Celery Beat periodic tasks programmatically.
#     
#     This runs after Celery has been fully configured. You can use this to
#     dynamically create periodic tasks that aren't defined in settings.
#     """
#     # Add periodic tasks
#     sender.add_periodic_task(
#         crontab(minute='*/10'),
#         app.task(name='sentineliq.tasks.check_cases_for_escalation'),
#         name='check-cases-for-escalation',
#     )
#     
#     sender.add_periodic_task(
#         crontab(minute='30', hour='*/1'),
#         app.task(name='sentineliq.tasks.check_for_expired_cases'),
#         name='check-for-expired-cases',
#     )
#     
#     sender.add_periodic_task(
#         crontab(minute='*/15'),
#         app.task(name='sentinelvision.tasks.schedule_feeds'),
#         name='schedule-feed-modules',
#     ) 