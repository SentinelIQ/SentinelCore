#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')
django.setup()

from django.apps import apps

@dataclass
class AppStructureResult:
    app_name: str
    issues: List[str]
    is_valid: bool

def check_app_structure(app_config) -> AppStructureResult:
    """Check if an app follows the proper structure from startapp."""
    issues = []
    app_path = Path(app_config.path)
    app_name = app_config.name
    
    # Required files from startapp
    required_files = [
        'apps.py',
        'admin.py',
        'models.py',
        '__init__.py',
    ]
    
    # Required directories
    required_dirs = [
        'migrations',
    ]
    
    # Additional required directories for our enterprise structure
    enterprise_dirs = [
        'views',
        'serializers',
        'permissions',
        'filters',
    ]
    
    # Check required files
    for file_name in required_files:
        file_path = app_path / file_name
        if not file_path.exists():
            issues.append(f"Missing required file: {file_name}")
    
    # Check required directories
    for dir_name in required_dirs:
        dir_path = app_path / dir_name
        if not dir_path.is_dir():
            issues.append(f"Missing required directory: {dir_name}")
    
    # Check enterprise structure directories
    for dir_name in enterprise_dirs:
        dir_path = app_path / dir_name
        if not dir_path.is_dir():
            issues.append(f"Missing enterprise directory: {dir_name}")
        elif dir_name == 'views':
            # Check views directory structure
            init_file = dir_path / '__init__.py'
            if not init_file.exists():
                issues.append("Missing __init__.py in views directory")
            
            # Check for modular view files
            view_files = list(dir_path.glob('*_view*.py'))
            if not view_files:
                issues.append("No modular view files found in views directory")
    
    # Check apps.py content
    apps_file = app_path / 'apps.py'
    if apps_file.exists():
        with open(apps_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'AppConfig' not in content:
                issues.append("apps.py does not contain AppConfig class")
    
    # Check admin.py content
    admin_file = app_path / 'admin.py'
    if admin_file.exists():
        with open(admin_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'admin.site.register' not in content and 'ModelAdmin' not in content:
                issues.append("No models registered in admin.py")
    
    return AppStructureResult(
        app_name=app_name,
        issues=issues,
        is_valid=len(issues) == 0
    )

def main():
    """Main function to check app structure compliance."""
    print("Checking Django app structure compliance...")
    
    # Get all project apps
    project_apps = [
        app for app in apps.get_app_configs()
        if not app.name.startswith('django.') and not app.name.startswith('rest_framework')
    ]
    
    results = [check_app_structure(app) for app in project_apps]
    
    # Print results
    print("\nValidation Results:")
    print("==================")
    
    valid_count = sum(1 for r in results if r.is_valid)
    total_count = len(results)
    
    for result in sorted(results, key=lambda x: x.app_name):
        print(f"\n{result.app_name}:")
        if result.is_valid:
            print("✅ App structure compliant")
        else:
            print("❌ App structure issues found:")
            for issue in result.issues:
                print(f"  - {issue}")
    
    print(f"\nSummary:")
    print(f"Total apps: {total_count}")
    print(f"Compliant apps: {valid_count}")
    print(f"Non-compliant apps: {total_count - valid_count}")
    print(f"Compliance rate: {(valid_count/total_count)*100:.1f}%")
    
    # Exit with error if any non-compliant apps found
    sys.exit(0 if valid_count == total_count else 1)

if __name__ == '__main__':
    main() 