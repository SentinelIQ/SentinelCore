"""
Permission Matrix for RBAC in SentinelIQ.

This module defines the permission matrix that maps roles to permissions.
"""

# Global permission mapping - maps roles to permissions
ROLE_PERMISSIONS = {
    # Global role (Platform Scope)
    "superuser": ["*"],  # All permissions (adminsentinel equivalent)
    
    # Per-Company Roles (Organization Scope)
    "admin_company": [
        # Company management
        "view_company", "manage_users", "user_stats", "deactivate_users",
        
        # Common
        "view_common", "whoami",
        
        # Alerts
        "view_alert", "create_alert", "update_alert", "delete_alert", 
        "escalate_alert", "ingest_alert",  # Custom alert actions
        
        # Incidents
        "view_incident", "create_incident", "update_incident", "delete_incident",
        "assign_incident", "add_timeline_entry", "close_incident",  # Custom incident actions
        
        # Tasks
        "view_task", "create_task", "update_task", "delete_task",
        "complete_task", "assign_task",  # Custom task actions
        
        # Observables
        "view_observable", "create_observable", "update_observable", "delete_observable",
        "mark_as_ioc", "enrich_observable",  # Custom observable actions
        
        # Wiki
        "view_wiki", "create_wiki", "update_wiki", "delete_wiki",
        
        # Reports
        "view_report", "create_report",
        
        # Dashboard/Metrics
        "view_dashboard",
        
        # Notifications
        "manage_notifications",
        
        # Integrations
        "view_misp", "manage_misp", "view_mitre", "manage_mitre",
        
        # MITRE ATT&CK Framework
        "view_mitretactic", "view_mitretechnique", "view_mitremitigation", "view_mitrerelationship",
        "view_alertmitremapping", "create_alertmitremapping", "update_alertmitremapping", "delete_alertmitremapping",
        "view_incidentmitremapping", "create_incidentmitremapping", "update_incidentmitremapping", "delete_incidentmitremapping",
        "view_observablemitremapping", "create_observablemitremapping", "update_observablemitremapping", "delete_observablemitremapping",
        
        # SentinelVision (analyzers/responders)
        "run_analyzers", "run_responders"
    ],
    
    "analyst_company": [
        # Company 
        "view_company",
        
        # Common
        "view_common", "whoami",
        
        # Alerts
        "view_alert", "create_alert", "update_alert",
        "escalate_alert", "ingest_alert",  # Analysts can escalate and ingest alerts
        
        # Incidents
        "view_incident", "create_incident", "update_incident",
        "assign_incident", "add_timeline_entry",  # Can add timeline entries but not close incidents
        
        # Tasks
        "view_task", "create_task", "update_task",
        "complete_task", "assign_task",  # Custom task actions
        
        # Observables
        "view_observable", "create_observable", "update_observable",
        "mark_as_ioc", "enrich_observable",  # Custom observable actions
        
        # Wiki
        "view_wiki", "create_wiki", "update_wiki",
        
        # Reports
        "view_report", "create_report",
        
        # Dashboard/Metrics
        "view_dashboard",
        
        # MITRE ATT&CK Framework
        "view_mitretactic", "view_mitretechnique", "view_mitremitigation", "view_mitrerelationship",
        "view_alertmitremapping", "create_alertmitremapping", "update_alertmitremapping", "delete_alertmitremapping",
        "view_incidentmitremapping", "create_incidentmitremapping", "update_incidentmitremapping", "delete_incidentmitremapping",
        "view_observablemitremapping", "create_observablemitremapping", "update_observablemitremapping", "delete_observablemitremapping",
        
        # SentinelVision (only responders, not analyzers)
        "run_responders"
    ],
    
    "read_only": [
        # Common
        "view_common", "whoami",
        
        # Read-only permissions
        "view_company", "view_alert", "view_incident", "view_task", 
        "view_observable", "view_wiki", "view_report", "view_dashboard",
        
        # MITRE ATT&CK Framework - read-only access
        "view_mitretactic", "view_mitretechnique", "view_mitremitigation", "view_mitrerelationship",
        "view_alertmitremapping", "view_incidentmitremapping", "view_observablemitremapping"
    ]
}

# Maps HTTP methods to permission prefixes
METHOD_PERMISSION_MAP = {
    'GET': 'view',
    'HEAD': 'view',
    'OPTIONS': 'view',
    'POST': 'create',
    'PUT': 'update',
    'PATCH': 'update',
    'DELETE': 'delete'
}

# Maps entity types to permission suffixes
ENTITY_PERMISSION_MAP = {
    'company': 'company',
    'user': 'users',
    'alert': 'alert',
    'incident': 'incident',
    'task': 'task',
    'observable': 'observable',
    'wiki': 'wiki',
    'report': 'report',
    'dashboard': 'dashboard',
    'notification': 'notifications',
    'misp': 'misp',
    'mitre': 'mitre',
    'mitretactic': 'mitretactic',
    'mitretechnique': 'mitretechnique',
    'mitremitigation': 'mitremitigation',
    'mitrerelationship': 'mitrerelationship',
    'alertmitremapping': 'alertmitremapping',
    'incidentmitremapping': 'incidentmitremapping',
    'observablemitremapping': 'observablemitremapping',
    'analyzer': 'analyzers',
    'responder': 'responders',
    'common': 'common'
}

# Custom action to permission mapping
CUSTOM_ACTION_PERMISSION_MAP = {
    # Alert custom actions
    'escalate': 'escalate_alert',
    'ingest': 'ingest_alert',
    
    # Incident custom actions
    'assign': 'assign_incident',
    'add_timeline_entry': 'add_timeline_entry',
    'close_incident': 'close_incident',
    
    # Task custom actions
    'complete': 'complete_task',
    'assign_task': 'assign_task',
    
    # Observable custom actions
    'mark_as_ioc': 'mark_as_ioc',
    'enrich': 'enrich_observable',
    
    # Company custom actions
    'user_stats': 'user_stats',
    'deactivate_users': 'deactivate_users',
    
    # Common
    'whoami': 'whoami',
    
    # MITRE custom actions
    'bulk_delete': 'delete_alertmitremapping',
    
    # Integration actions
    'run_analyzer': 'run_analyzers',
    'run_responder': 'run_responders'
}

def has_permission(role, permission):
    """
    Check if the given role has the specified permission.
    
    Args:
        role (str): The role to check
        permission (str): The permission to check for
        
    Returns:
        bool: True if the role has the permission, False otherwise
    """
    if role not in ROLE_PERMISSIONS:
        return False
        
    # Superuser has all permissions
    if "*" in ROLE_PERMISSIONS[role]:
        return True
        
    return permission in ROLE_PERMISSIONS[role]
    
def get_required_permission(method, entity_type, custom_action=None):
    """
    Determine the required permission based on HTTP method and entity type.
    
    Args:
        method (str): HTTP method (GET, POST, etc.)
        entity_type (str): Entity type (alert, incident, etc.)
        custom_action (str, optional): Custom action name for special endpoints
        
    Returns:
        str: The required permission
    """
    if custom_action:
        # Check if we have a specific mapping for this custom action
        if custom_action in CUSTOM_ACTION_PERMISSION_MAP:
            return CUSTOM_ACTION_PERMISSION_MAP[custom_action]
            
        # Fall back to default mapping based on HTTP method and entity type
        return f"{METHOD_PERMISSION_MAP.get(method, 'view')}_{ENTITY_PERMISSION_MAP.get(entity_type, entity_type)}"
    
    # Standard CRUD operations
    permission_prefix = METHOD_PERMISSION_MAP.get(method, 'view')
    permission_suffix = ENTITY_PERMISSION_MAP.get(entity_type, entity_type)
    
    return f"{permission_prefix}_{permission_suffix}" 