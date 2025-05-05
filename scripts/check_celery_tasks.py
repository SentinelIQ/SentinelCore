#!/usr/bin/env python
"""
Script to check all registered Celery tasks and their origins.

This tool helps identify which task modules are already registered
and which ones need to be migrated to the centralized structure.

Usage:
    docker compose exec web python scripts/check_celery_tasks.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')
django.setup()

from celery import current_app
from celery.app.registry import TaskRegistry
from importlib import import_module
import inspect
from collections import defaultdict
import json

# Import the task registry from centralized location
try:
    from sentineliq.tasks import TASK_MODULES as REGISTERED_MODULES
except ImportError:
    REGISTERED_MODULES = []


def get_module_from_task(task_name):
    """Extract module name from a task name."""
    parts = task_name.split('.')
    
    if len(parts) <= 1:
        return 'unknown'
    
    # Handle special cases for celery's built-in tasks
    if parts[0] == 'celery':
        return 'celery'
    
    # For most task names, the module is everything before the last segment
    return '.'.join(parts[:-1])


def classify_tasks(tasks):
    """Classify tasks by their origin module."""
    classified = defaultdict(list)
    
    for name, task in tasks.items():
        # Skip celery internal tasks
        if name.startswith('celery.'):
            continue
        
        module_name = get_module_from_task(name)
        classified[module_name].append({
            'name': name, 
            'module': module_name,
            'type': task.__class__.__name__
        })
    
    return classified


def get_module_file_location(module_name):
    """Get file location for a module."""
    try:
        module = import_module(module_name)
        return getattr(module, '__file__', 'unknown')
    except ImportError:
        return "Module not importable"


def is_migrated(module_name):
    """Check if a module is already migrated to the centralized structure."""
    return module_name.startswith('sentineliq.tasks.')


def collect_task_info():
    """Collect information about all registered tasks."""
    all_tasks = current_app.tasks
    
    # Get tasks by module
    tasks_by_module = classify_tasks(all_tasks)
    
    # Enhance with file locations and migration status
    result = []
    
    for module_name, tasks in sorted(tasks_by_module.items()):
        file_location = get_module_file_location(module_name)
        migrated = is_migrated(module_name)
        registered = module_name in REGISTERED_MODULES
        
        module_info = {
            'module': module_name,
            'file_location': file_location,
            'migrated': migrated,
            'registered': registered,
            'task_count': len(tasks),
            'tasks': tasks
        }
        
        result.append(module_info)
    
    return result


def print_migration_status(task_info):
    """Print a report of migration status."""
    print("\n===== Celery Task Migration Status =====\n")
    print("Modules already migrated to centralized structure:")
    print("-" * 50)
    migrated_count = 0
    
    for module in task_info:
        if module['migrated']:
            migrated_count += 1
            print(f"✅ {module['module']} ({module['task_count']} tasks)")
    
    if migrated_count == 0:
        print("No modules have been migrated yet.")
    
    print("\nModules that need migration:")
    print("-" * 50)
    needs_migration = False
    
    for module in task_info:
        if not module['migrated'] and module['module'] not in ('celery', 'unknown'):
            needs_migration = True
            print(f"❌ {module['module']} ({module['task_count']} tasks) -> {module['file_location']}")
    
    if not needs_migration:
        print("All modules have been migrated!")
    
    print("\n===== Migration Guide =====\n")
    print("To migrate a task module:")
    print("1. Create directory: mkdir -p sentineliq/tasks/app_name")
    print("2. Create __init__.py and task files in the new directory")
    print("3. Update sentineliq/tasks/__init__.py to register the new module")
    print("4. Test the migrated tasks thoroughly")
    print("5. Update task calls throughout the codebase")
    print("\n")


if __name__ == "__main__":
    task_info = collect_task_info()
    
    # Print human-readable report
    print_migration_status(task_info)
    
    # Optionally export to JSON for further analysis
    if '--json' in sys.argv:
        with open('celery_tasks_report.json', 'w') as f:
            json.dump(task_info, f, indent=2)
            print(f"Full report exported to celery_tasks_report.json") 