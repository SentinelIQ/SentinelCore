"""
Celery task registry for SentinelIQ.

This module serves as a central registry for all Celery tasks defined in the application.
It imports all task modules to ensure they are registered with the Celery app.
"""

import importlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

# Set up logger
logger = logging.getLogger('sentineliq.tasks')

# Task module registry
TASK_MODULES = [
    # Core task modules
    'sentineliq.tasks.alerts.alert_tasks',
    'sentineliq.tasks.incidents.incident_tasks',
    'sentineliq.tasks.observables.observable_tasks',
    'sentineliq.tasks.reporting.report_tasks',
    'sentineliq.tasks.scheduled.periodic_tasks',
    'sentineliq.tasks.system.system_tasks',
    'sentineliq.tasks.mitre.mitre_tasks',
    
    # External app modules
    'api.core.tasks',
    'mitre.tasks',
    'sentinelvision.tasks',
    'sentinelvision.tasks.feed_tasks',
    'sentinelvision.tasks.feed_dispatcher',
    'sentinelvision.tasks.enrichment_tasks',
    'notifications.tasks',
]

def register_all_tasks() -> Dict[str, List[str]]:
    """
    Explicitly import all task modules to ensure they're registered with Celery.
    
    Returns:
        Dict containing successful and failed imports
    """
    results = {
        'success': [],
        'failed': [],
    }
    
    for module_path in TASK_MODULES:
        try:
            importlib.import_module(module_path)
            results['success'].append(module_path)
            logger.info(f"Successfully registered task module: {module_path}")
        except ImportError as e:
            results['failed'].append({
                'module': module_path,
                'error': str(e)
            })
            logger.warning(f"Failed to import task module {module_path}: {str(e)}")
            
    # Log summary
    logger.info(f"Task registration complete: {len(results['success'])} successful, {len(results['failed'])} failed")
    
    return results


def autodiscover_task_modules() -> List[str]:
    """
    Automatically discover and import task modules based on module pattern.
    
    Searches for any Python module containing 'tasks' in the name within the project.
    This helps ensure dynamically added tasks are registered properly.
    
    Returns:
        List of discovered task modules
    """
    discovered_modules = []
    base_dir = Path(__file__).parent.parent.parent
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py') and 'task' in file:
                # Convert file path to module path
                relative_path = os.path.relpath(os.path.join(root, file), base_dir)
                if '__pycache__' in relative_path:
                    continue
                
                module_path = relative_path.replace(os.path.sep, '.').replace('.py', '')
                
                try:
                    importlib.import_module(module_path)
                    discovered_modules.append(module_path)
                    logger.debug(f"Auto-discovered task module: {module_path}")
                except ImportError:
                    # Skip modules that can't be imported directly
                    pass
    
    logger.info(f"Auto-discovered {len(discovered_modules)} additional task modules")
    return discovered_modules


# Export public API
__all__ = ['register_all_tasks', 'autodiscover_task_modules'] 