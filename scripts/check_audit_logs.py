#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
from typing import List, Dict, Any, Set
from dataclasses import dataclass

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')
django.setup()

from django.apps import apps
from django.db import models

@dataclass
class AuditLogResult:
    app_name: str
    model_name: str
    issues: List[str]
    is_valid: bool

def check_model_audit_integration(model: models.Model) -> List[str]:
    """Check if a model has proper audit log integration."""
    issues = []
    
    # Check for AuditlogModelMixin
    if not any('AuditlogModelMixin' in base.__name__ for base in model.__bases__):
        issues.append("Missing AuditlogModelMixin")
    
    # Check for audit_log attribute
    if not hasattr(model, 'audit_log'):
        issues.append("Missing audit_log manager")
    
    # Check for excluded_fields configuration
    if not hasattr(model, 'audit_log_exclude'):
        issues.append("Missing audit_log_exclude configuration")
    
    return issues

def check_view_audit_integration(app_path: Path) -> List[str]:
    """Check if views have proper audit log integration."""
    issues = []
    views_dir = app_path / 'views'
    
    if not views_dir.exists():
        return issues
    
    for view_file in views_dir.rglob('*.py'):
        if view_file.name == '__init__.py':
            continue
            
        with open(view_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for AuditLogMixin
            if 'class' in content and 'AuditLogMixin' not in content:
                issues.append(f"View file missing AuditLogMixin: {view_file.name}")
            
            # Check for audit_action decorator
            if 'def ' in content and '@audit_action' not in content:
                issues.append(f"View actions missing @audit_action decorator: {view_file.name}")
    
    return issues

def check_app_audit_integration(app_config) -> List[AuditLogResult]:
    """Check audit log integration for a single app."""
    results = []
    app_path = Path(app_config.path)
    
    # Check models
    for model in app_config.get_models():
        model_issues = check_model_audit_integration(model)
        results.append(AuditLogResult(
            app_name=app_config.name,
            model_name=model.__name__,
            issues=model_issues,
            is_valid=len(model_issues) == 0
        ))
    
    # Check views
    view_issues = check_view_audit_integration(app_path)
    if view_issues:
        results.append(AuditLogResult(
            app_name=app_config.name,
            model_name='views',
            issues=view_issues,
            is_valid=False
        ))
    
    return results

def main():
    """Main function to check audit log integration compliance."""
    print("Checking audit log integration compliance...")
    
    # Get all project apps
    project_apps = [
        app for app in apps.get_app_configs()
        if not app.name.startswith('django.') and not app.name.startswith('rest_framework')
    ]
    
    # Check each app's audit log integration
    all_results = []
    for app in project_apps:
        results = check_app_audit_integration(app)
        all_results.extend(results)
    
    # Print results
    print("\nValidation Results:")
    print("==================")
    
    # Group by app
    app_results: Dict[str, List[AuditLogResult]] = {}
    for result in all_results:
        if result.app_name not in app_results:
            app_results[result.app_name] = []
        app_results[result.app_name].append(result)
    
    valid_count = sum(1 for r in all_results if r.is_valid)
    total_count = len(all_results)
    
    # Print results by app
    for app_name, results in sorted(app_results.items()):
        print(f"\n{app_name}:")
        for result in results:
            print(f"\n  {result.model_name}:")
            if result.is_valid:
                print("  ✅ Audit log integration compliant")
            else:
                print("  ❌ Audit log integration issues found:")
                for issue in result.issues:
                    print(f"    - {issue}")
    
    print(f"\nSummary:")
    print(f"Total components checked: {total_count}")
    print(f"Compliant components: {valid_count}")
    print(f"Non-compliant components: {total_count - valid_count}")
    print(f"Compliance rate: {(valid_count/total_count)*100:.1f}%")
    
    # Check for audit_logs app
    if 'audit_logs' not in [app.name for app in apps.get_app_configs()]:
        print("\n❌ audit_logs app not found in INSTALLED_APPS")
        sys.exit(1)
    
    # Exit with error if any non-compliant components found
    sys.exit(0 if valid_count == total_count else 1)

if __name__ == '__main__':
    main() 