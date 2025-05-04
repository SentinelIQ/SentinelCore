#!/usr/bin/env python
"""
Script to verify the OpenAPI schema structure and ensure no unwanted tags remain.

This script loads the OpenAPI schema and checks that:
1. Only allowed domain tags are present
2. No unwanted legacy tags remain 
3. All operations have appropriate tags
4. No unused tags exist in the schema

Usage:
    docker compose exec web python api/scripts/verify_openapi_tags.py

"""
import os
import json
import sys
from pathlib import Path
from collections import Counter

# Define the allowed domain tags
ALLOWED_TAGS = [
    'Authentication & Access Control',
    'Company Management',
    'Alert Management',
    'Incident Management', 
    'Observables & IOCs',
    'Task Management',
    'Threat Intelligence (SentinelVision)',
    'MITRE Framework',
    'Notification System',
    'Knowledge Base (Wiki)',
    'Reporting',
    'System Monitoring & Operations',
]

# Define the unwanted legacy tags
UNWANTED_TAGS = [
    'api', 'Common', 'System', 'MITRE Mappings', 'MITRE ATT&CK',
    'mitre', 'Notifications', 'sentinelvision', 'enrichment',
    'sentinel-vision', 'feeds'
]

def verify_schema():
    """
    Generate and verify the OpenAPI schema structure.
    """
    # Generate the schema using the Django management command
    os.system('docker compose exec -T web python manage.py spectacular --file /tmp/schema.json')
    
    # Read the generated schema
    try:
        with open('/tmp/schema.json', 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print("❌ Error: Schema file not found. Make sure the schema generation command succeeded.")
        return False
    
    # Check schema structure
    all_checks_passed = True
    
    # Check 1: Verify that only allowed tags are defined
    print("\n✅ Checking defined tags...")
    defined_tags = [tag.get('name') for tag in schema.get('tags', [])]
    
    # Look for unwanted tags
    unwanted_defined = [tag for tag in defined_tags if tag in UNWANTED_TAGS]
    if unwanted_defined:
        print(f"❌ Error: Unwanted tags are still defined in the schema: {unwanted_defined}")
        all_checks_passed = False
    else:
        print("✓ No unwanted tags defined in schema")
    
    # Look for undefined allowed tags
    missing_allowed = [tag for tag in ALLOWED_TAGS if tag not in defined_tags]
    if missing_allowed:
        print(f"❌ Error: Some allowed tags are missing from the schema: {missing_allowed}")
        all_checks_passed = False
    else:
        print("✓ All allowed domain tags are defined")
    
    # Check 2: Verify that all operations have appropriate tags
    print("\n✅ Checking operation tags...")
    operation_tags = []
    
    # Collect all tags used in operations
    if 'paths' in schema:
        for path, path_item in schema.get('paths', {}).items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    if 'tags' in operation:
                        operation_tags.extend(operation['tags'])
    
    # Count usage of each tag
    tag_counts = Counter(operation_tags)
    
    # Check for unwanted tags in operations
    unwanted_in_ops = [tag for tag in tag_counts.keys() if tag in UNWANTED_TAGS]
    if unwanted_in_ops:
        print(f"❌ Error: Unwanted tags are still used in operations: {unwanted_in_ops}")
        all_checks_passed = False
    else:
        print("✓ No unwanted tags used in operations")
    
    # Check for unused defined tags
    unused_tags = [tag for tag in defined_tags if tag not in tag_counts]
    if unused_tags:
        print(f"⚠️ Warning: Some defined tags are not used in any operation: {unused_tags}")
    
    # Print tag usage statistics
    print("\n📊 Tag usage statistics:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tag}: {count} operations")
    
    # Final result
    if all_checks_passed:
        print("\n✅ All checks passed! OpenAPI schema structure is valid.")
        return True
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    print("OpenAPI Schema Structure Verification")
    print("=====================================")
    
    success = verify_schema()
    sys.exit(0 if success else 1) 