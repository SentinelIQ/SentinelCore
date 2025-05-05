#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
import inspect
from typing import List, Dict, Any
from dataclasses import dataclass

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')
django.setup()

from django.urls import get_resolver, URLPattern, URLResolver
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema

@dataclass
class ValidationResult:
    view_name: str
    issues: List[str]
    is_valid: bool

def get_all_api_views() -> List[Any]:
    """Get all API views from URL patterns."""
    def extract_views(patterns):
        views = []
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                views.extend(extract_views(pattern.url_patterns))
            elif isinstance(pattern, URLPattern):
                if hasattr(pattern.callback, 'view_class'):
                    view_class = pattern.callback.view_class
                    if issubclass(view_class, (ViewSet, APIView)):
                        views.append(view_class)
        return views
    
    resolver = get_resolver()
    return extract_views(resolver.url_patterns)

def validate_view_documentation(view_class: Any) -> ValidationResult:
    """Validate documentation for a single view class."""
    issues = []
    view_name = view_class.__name__
    
    # Check for @extend_schema decorator
    has_extend_schema = False
    for method in ['get', 'post', 'put', 'patch', 'delete']:
        if hasattr(view_class, method):
            method_handler = getattr(view_class, method)
            if hasattr(method_handler, '_spectacular_annotation'):
                has_extend_schema = True
            else:
                issues.append(f"Method {method} missing @extend_schema decorator")
    
    # Check docstring
    if not view_class.__doc__:
        issues.append("Missing class docstring")
    
    # Check for response descriptions
    if hasattr(view_class, 'get_serializer_class'):
        serializer_class = view_class.get_serializer_class()
        if not serializer_class.__doc__:
            issues.append("Serializer missing docstring")
    
    return ValidationResult(
        view_name=view_name,
        issues=issues,
        is_valid=len(issues) == 0
    )

def main():
    """Main function to check API documentation compliance."""
    print("Checking API documentation compliance...")
    
    views = get_all_api_views()
    results = [validate_view_documentation(view) for view in views]
    
    # Print results
    print("\nValidation Results:")
    print("==================")
    
    valid_count = sum(1 for r in results if r.is_valid)
    total_count = len(results)
    
    for result in results:
        print(f"\n{result.view_name}:")
        if result.is_valid:
            print("✅ Documentation compliant")
        else:
            print("❌ Documentation issues found:")
            for issue in result.issues:
                print(f"  - {issue}")
    
    print(f"\nSummary:")
    print(f"Total views: {total_count}")
    print(f"Compliant views: {valid_count}")
    print(f"Non-compliant views: {total_count - valid_count}")
    print(f"Compliance rate: {(valid_count/total_count)*100:.1f}%")
    
    # Exit with error if any non-compliant views found
    sys.exit(0 if valid_count == total_count else 1)

if __name__ == '__main__':
    main() 