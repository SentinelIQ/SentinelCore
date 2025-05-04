#!/usr/bin/env python
"""
Script to update OpenAPI tags in the codebase to match the new DDD tag structure.

This script searches for all files containing `extend_schema(tags=` and updates
the tag names to match the new Domain-Driven Design (DDD) structure as defined in settings.py.

Usage:
    docker compose exec web python api/scripts/update_openapi_tags.py

"""
import os
import re
import sys
from pathlib import Path

# Define the tag mapping (old_tag -> new_tag)
TAG_MAPPING = {
    'Authentication': 'Authentication & Access Control',
    'Users': 'Authentication & Access Control',
    'Companies': 'Company Management',
    'Alerts': 'Alert Management',
    'Incidents': 'Incident Management',
    'Observables': 'Observables & IOCs',
    'Tasks': 'Task Management',
    'Common': 'System Monitoring & Operations',
    'Reporting': 'Reporting',
    'Wiki Articles': 'Knowledge Base (Wiki)',
    'Wiki Categories': 'Knowledge Base (Wiki)',
    'Notifications': 'Notification System',
    'SentinelVision Feeds': 'Threat Intelligence (SentinelVision)',
    'SentinelVision Analyzers': 'Threat Intelligence (SentinelVision)',
    'SentinelVision Responders': 'Threat Intelligence (SentinelVision)',
    'MITRE ATT&CK': 'MITRE Framework',
    'MITRE Mappings': 'MITRE Framework',
    'Dashboard': 'System Monitoring & Operations',
    'System': 'System Monitoring & Operations',
    'API': 'System Monitoring & Operations',
    'sentinelvision': 'Threat Intelligence (SentinelVision)',
    'sentinel-vision': 'Threat Intelligence (SentinelVision)',
}

# Improved safer regex pattern to find extend_schema tags
# Looks specifically for decorators or function calls, not string literals inside documentation
TAG_PATTERN = r'((?:^|\s+)@?extend_schema\(\s*tags\s*=\s*\[\s*[\'"])([^\'"]*)([\'"](?:\s*\]|\s*\],))'

def update_file_tags(file_path):
    """
    Update tags in a single file.
    
    Args:
        file_path: Path to the file to update
        
    Returns:
        tuple: (changes_made, changes_count)
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_count = 0
    
    # Use regex to find all extend_schema(tags=['...']) instances
    matches = re.finditer(TAG_PATTERN, content, re.MULTILINE)
    
    # Process matches in reverse order to avoid position shifts
    matches = list(matches)
    for match in reversed(matches):
        prefix, old_tag, suffix = match.groups()
        
        if old_tag in TAG_MAPPING:
            new_tag = TAG_MAPPING[old_tag]
            # Replace the tag, ensuring we only replace within the matched pattern
            # This avoids corrupting string literals in example responses
            replacement = f"{prefix}{new_tag}{suffix}"
            start, end = match.span()
            content = content[:start] + replacement + content[end:]
            changes_count += 1
    
    # Save the file if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True, changes_count
    
    return False, 0

def find_and_update_files(root_dir, dry_run=False):
    """
    Find all Python files containing extend_schema tags and update them.
    
    Args:
        root_dir: Root directory to search in
        dry_run: If True, don't actually modify files, just show what would change
    """
    total_files = 0
    updated_files = 0
    total_changes = 0
    
    print(f"Scanning directory: {root_dir}")
    print(f"DRY RUN: {'Yes (no changes will be made)' if dry_run else 'No (changes will be applied)'}")
    print()
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Check if the file contains extend_schema(tags=
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'extend_schema' in content and 'tags=' in content:
                        total_files += 1
                        
                        if not dry_run:
                            changed, change_count = update_file_tags(file_path)
                            
                            if changed:
                                updated_files += 1
                                total_changes += change_count
                                print(f"Updated {file_path} ({change_count} changes)")
                        else:
                            # Dry run - just count potential changes
                            matches = re.finditer(TAG_PATTERN, content, re.MULTILINE)
                            matches = list(matches)
                            changes = sum(1 for match in matches if match.group(2) in TAG_MAPPING)
                            
                            if changes > 0:
                                updated_files += 1
                                total_changes += changes
                                print(f"Would update {file_path} ({changes} changes)")
    
    print("\nSummary:")
    print(f"Total files with tags: {total_files}")
    if dry_run:
        print(f"Files that would be updated: {updated_files}")
        print(f"Total tag changes that would be made: {total_changes}")
    else:
        print(f"Files updated: {updated_files}")
        print(f"Total tag changes: {total_changes}")

if __name__ == "__main__":
    # Get the Django project root directory
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    print(f"Enterprise-grade API Tag Update Tool")
    print(f"====================================")
    print(f"Project root: {project_root}")
    
    # Check if --dry-run flag is passed
    dry_run = "--dry-run" in sys.argv
    
    find_and_update_files(project_root, dry_run=dry_run)
    
    print("\nTag update complete!")
    if dry_run:
        print("No changes were made (dry run mode)")
    sys.exit(0) 