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

@dataclass
class TestStructureResult:
    app_name: str
    issues: List[str]
    is_valid: bool

def find_test_files() -> Dict[str, List[Path]]:
    """Find all test files in the project."""
    test_files = {
        'centralized': [],
        'app_level': [],
    }
    
    # Find centralized test files
    tests_dir = project_root / 'tests'
    if tests_dir.exists():
        for path in tests_dir.rglob('test_*.py'):
            test_files['centralized'].append(path)
    
    # Find app-level test files
    for app_config in apps.get_app_configs():
        if not app_config.name.startswith('django.'):
            app_path = Path(app_config.path)
            for path in app_path.rglob('test_*.py'):
                if 'tests' not in path.parts:  # Exclude files in app's 'tests' directory
                    test_files['app_level'].append(path)
    
    return test_files

def check_test_coverage() -> Set[str]:
    """Check which apps have test coverage."""
    covered_apps = set()
    tests_dir = project_root / 'tests'
    
    if tests_dir.exists():
        # Get all app names
        app_names = {
            app.name.split('.')[-1]
            for app in apps.get_app_configs()
            if not app.name.startswith('django.')
        }
        
        # Check for test directories matching app names
        for app_name in app_names:
            app_test_dir = tests_dir / app_name
            if app_test_dir.exists() and any(p.name.startswith('test_') for p in app_test_dir.rglob('*.py')):
                covered_apps.add(app_name)
    
    return covered_apps

def check_app_test_structure(app_config) -> TestStructureResult:
    """Check test structure for a single app."""
    issues = []
    app_name = app_config.name.split('.')[-1]
    app_path = Path(app_config.path)
    
    # Check for app-level test files
    app_test_files = list(app_path.rglob('test_*.py'))
    if app_test_files:
        for test_file in app_test_files:
            if 'tests' not in test_file.parts:  # Exclude files in app's 'tests' directory
                issues.append(f"Test file found in app directory: {test_file.relative_to(project_root)}")
    
    # Check for centralized test coverage
    tests_dir = project_root / 'tests' / app_name
    if not tests_dir.exists():
        issues.append(f"No test directory found in /tests/{app_name}/")
    else:
        test_files = list(tests_dir.rglob('test_*.py'))
        if not test_files:
            issues.append(f"No test files found in /tests/{app_name}/")
    
    return TestStructureResult(
        app_name=app_name,
        issues=issues,
        is_valid=len(issues) == 0
    )

def main():
    """Main function to check test structure compliance."""
    print("Checking test structure compliance...")
    
    # Get all project apps
    project_apps = [
        app for app in apps.get_app_configs()
        if not app.name.startswith('django.') and not app.name.startswith('rest_framework')
    ]
    
    # Find all test files
    test_files = find_test_files()
    
    # Check each app's test structure
    results = [check_app_test_structure(app) for app in project_apps]
    
    # Print results
    print("\nValidation Results:")
    print("==================")
    
    # Report on test file locations
    print("\nTest File Locations:")
    if test_files['app_level']:
        print("\n❌ Test files found in app directories (should be moved to /tests/):")
        for path in sorted(test_files['app_level']):
            print(f"  - {path.relative_to(project_root)}")
    else:
        print("\n✅ No test files found in app directories")
    
    print(f"\nCentralized test files: {len(test_files['centralized'])}")
    
    # Report on app coverage
    print("\nApp Test Coverage:")
    valid_count = sum(1 for r in results if r.is_valid)
    total_count = len(results)
    
    for result in sorted(results, key=lambda x: x.app_name):
        print(f"\n{result.app_name}:")
        if result.is_valid:
            print("✅ Test structure compliant")
        else:
            print("❌ Test structure issues found:")
            for issue in result.issues:
                print(f"  - {issue}")
    
    print(f"\nSummary:")
    print(f"Total apps: {total_count}")
    print(f"Compliant apps: {valid_count}")
    print(f"Non-compliant apps: {total_count - valid_count}")
    print(f"Compliance rate: {(valid_count/total_count)*100:.1f}%")
    
    # Exit with error if any non-compliant apps found
    sys.exit(0 if valid_count == total_count and not test_files['app_level'] else 1)

if __name__ == '__main__':
    main() 