#!/usr/bin/env python
"""
Script to update OpenAPI view tags in the codebase to match the new DDD tag structure.

This script searches for files using @extend_schema_view with multiple view actions
and updates them to use consistent tags following the Domain-Driven Design structure.

Usage:
    docker compose exec web python api/scripts/update_openapi_views.py [--dry-run]

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

# Improved safer regex pattern for view action tags
# Matches patterns like: list=extend_schema(tags=['Tag'])
VIEW_TAG_PATTERN = r'((?:^|\s+)(\w+)\s*=\s*extend_schema\(\s*tags\s*=\s*\[\s*[\'"])([^\'"]*)([\'"](?:\s*\]|\s*\],))'

def update_file_view_tags(file_path):
    """
    Update view tags in a single file.
    
    Args:
        file_path: Path to the file to update
        
    Returns:
        tuple: (changes_made, changes_count)
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_count = 0
    
    # Find the class or function name to determine the domain
    class_match = re.search(r"class\s+(\w+)(?:\(|\:)", content)
    if class_match:
        class_name = class_match.group(1)
        
        # Use class name to infer domain if possible
        inferred_domain = None
        for name_part, domain in [
            ('Alert', 'Alert Management'),
            ('Incident', 'Incident Management'),
            ('Observable', 'Observables & IOCs'),
            ('Task', 'Task Management'),
            ('User', 'Authentication & Access Control'),
            ('Company', 'Company Management'),
            ('Knowledge', 'Knowledge Base (Wiki)'),
            ('Wiki', 'Knowledge Base (Wiki)'),
            ('Notification', 'Notification System'),
            ('SentinelVision', 'Threat Intelligence (SentinelVision)'),
            ('Mitre', 'MITRE Framework'),
            ('Report', 'Reporting'),
            ('Dashboard', 'System Monitoring & Operations'),
        ]:
            if name_part.lower() in class_name.lower():
                inferred_domain = domain
                break
        
        # Use regex to find all view action tags
        matches = re.finditer(VIEW_TAG_PATTERN, content, re.MULTILINE)
        
        # Process matches in reverse order to avoid position shifts
        matches = list(matches)
        replaced_positions = []
        
        for match in reversed(matches):
            prefix, action, old_tag, suffix = match.groups()
            replacement_tag = None
            
            # Get new tag from mapping or use inferred domain
            if old_tag in TAG_MAPPING:
                replacement_tag = TAG_MAPPING[old_tag]
            elif inferred_domain:
                replacement_tag = inferred_domain
            
            if replacement_tag:
                # Replace the tag
                start, end = match.span()
                replacement = f"{prefix}{action}=extend_schema(tags=['{replacement_tag}'{suffix[1:]}"
                
                # Track position to avoid overlapping replacements
                if not any(start >= pos[0] and end <= pos[1] for pos in replaced_positions):
                    content = content[:start] + replacement + content[end:]
                    replaced_positions.append((start, end))
                    changes_count += 1
    
    # Save the file if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True, changes_count
    
    return False, 0

def analyze_file_view_tags(file_path):
    """
    Analyze view tags in a file without making changes (for dry run).
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        int: Number of changes that would be made
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    changes_count = 0
    
    # Find the class or function name to determine the domain
    class_match = re.search(r"class\s+(\w+)(?:\(|\:)", content)
    if class_match:
        class_name = class_match.group(1)
        
        # Use class name to infer domain if possible
        inferred_domain = None
        for name_part, domain in [
            ('Alert', 'Alert Management'),
            ('Incident', 'Incident Management'),
            ('Observable', 'Observables & IOCs'),
            ('Task', 'Task Management'),
            ('User', 'Authentication & Access Control'),
            ('Company', 'Company Management'),
            ('Knowledge', 'Knowledge Base (Wiki)'),
            ('Wiki', 'Knowledge Base (Wiki)'),
            ('Notification', 'Notification System'),
            ('SentinelVision', 'Threat Intelligence (SentinelVision)'),
            ('Mitre', 'MITRE Framework'),
            ('Report', 'Reporting'),
            ('Dashboard', 'System Monitoring & Operations'),
        ]:
            if name_part.lower() in class_name.lower():
                inferred_domain = domain
                break
        
        # Use regex to find all view action tags
        matches = re.finditer(VIEW_TAG_PATTERN, content, re.MULTILINE)
        
        # Just count how many matches would be replaced
        for match in matches:
            _, _, old_tag, _ = match.groups()
            
            # A tag would be replaced if it's in the mapping or we can infer the domain
            if old_tag in TAG_MAPPING or inferred_domain:
                changes_count += 1
    
    return changes_count

def find_and_update_view_files(root_dir, dry_run=False):
    """
    Find all Python files containing extend_schema_view and update them.
    
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
                
                # Check if the file contains extend_schema_view
                with open(file_path, 'r') as f:
                    content = f.read()
                    if '@extend_schema_view' in content:
                        total_files += 1
                        
                        if not dry_run:
                            changed, change_count = update_file_view_tags(file_path)
                            
                            if changed:
                                updated_files += 1
                                total_changes += change_count
                                print(f"Updated {file_path} ({change_count} changes)")
                        else:
                            # Dry run - just analyze without changing
                            change_count = analyze_file_view_tags(file_path)
                            
                            if change_count > 0:
                                updated_files += 1
                                total_changes += change_count
                                print(f"Would update {file_path} ({change_count} changes)")
    
    print("\nSummary:")
    print(f"Total files with view tags: {total_files}")
    if dry_run:
        print(f"Files that would be updated: {updated_files}")
        print(f"Total view tag changes that would be made: {total_changes}")
    else:
        print(f"Files updated: {updated_files}")
        print(f"Total view tag changes: {total_changes}")

if __name__ == "__main__":
    # Get the Django project root directory
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    print(f"Enterprise-grade API View Tag Update Tool")
    print(f"========================================")
    print(f"Project root: {project_root}")
    
    # Check if --dry-run flag is passed
    dry_run = "--dry-run" in sys.argv
    
    find_and_update_view_files(project_root, dry_run=dry_run)
    
    print("\nView tag update complete!")
    if dry_run:
        print("No changes were made (dry run mode)")
    sys.exit(0) 