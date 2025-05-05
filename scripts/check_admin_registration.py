#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')
django.setup()

from django.apps import apps
from django.contrib import admin
from django.db.models import Model

@dataclass
class AdminRegistrationResult:
    app_name: str
    model_name: str
    is_registered: bool
    has_list_display: bool
    has_search_fields: bool
    has_readonly_fields: bool
    issues: List[str]

def get_all_models() -> List[Tuple[str, Model]]:
    """Get all models from installed apps."""
    models = []
    for app_config in apps.get_app_configs():
        if not app_config.name.startswith('django.'):  # Skip Django's internal apps
            for model in app_config.get_models():
                models.append((app_config.name, model))
    return models

def check_admin_registration(app_name: str, model: Model) -> AdminRegistrationResult:
    """Check if a model is properly registered in Django Admin."""
    issues = []
    model_name = model.__name__
    
    # Check if model is registered
    is_registered = model in admin.site._registry
    if not is_registered:
        issues.append("Model not registered in Django Admin")
        return AdminRegistrationResult(
            app_name=app_name,
            model_name=model_name,
            is_registered=False,
            has_list_display=False,
            has_search_fields=False,
            has_readonly_fields=False,
            issues=issues
        )
    
    # Get admin class
    admin_class = admin.site._registry[model]
    
    # Check list_display
    has_list_display = bool(getattr(admin_class, 'list_display', None))
    if not has_list_display:
        issues.append("Missing list_display configuration")
    
    # Check search_fields
    has_search_fields = bool(getattr(admin_class, 'search_fields', None))
    if not has_search_fields:
        issues.append("Missing search_fields configuration")
    
    # Check readonly_fields
    has_readonly_fields = bool(getattr(admin_class, 'readonly_fields', None))
    if not has_readonly_fields:
        issues.append("Missing readonly_fields configuration")
    
    return AdminRegistrationResult(
        app_name=app_name,
        model_name=model_name,
        is_registered=is_registered,
        has_list_display=has_list_display,
        has_search_fields=has_search_fields,
        has_readonly_fields=has_readonly_fields,
        issues=issues
    )

def main():
    """Main function to check admin registration compliance."""
    print("Checking Django Admin registration compliance...")
    
    models = get_all_models()
    results = [check_admin_registration(app_name, model) for app_name, model in models]
    
    # Print results
    print("\nValidation Results:")
    print("==================")
    
    valid_count = sum(1 for r in results if not r.issues)
    total_count = len(results)
    
    # Group by app
    app_results: Dict[str, List[AdminRegistrationResult]] = {}
    for result in results:
        if result.app_name not in app_results:
            app_results[result.app_name] = []
        app_results[result.app_name].append(result)
    
    # Print results by app
    for app_name, app_results in sorted(app_results.items()):
        print(f"\n{app_name}:")
        for result in app_results:
            print(f"\n  {result.model_name}:")
            if not result.issues:
                print("  ✅ Admin registration compliant")
            else:
                print("  ❌ Admin registration issues found:")
                for issue in result.issues:
                    print(f"    - {issue}")
    
    print(f"\nSummary:")
    print(f"Total models: {total_count}")
    print(f"Compliant models: {valid_count}")
    print(f"Non-compliant models: {total_count - valid_count}")
    print(f"Compliance rate: {(valid_count/total_count)*100:.1f}%")
    
    # Exit with error if any non-compliant models found
    sys.exit(0 if valid_count == total_count else 1)

if __name__ == '__main__':
    main() 