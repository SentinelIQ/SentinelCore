from drf_spectacular.utils import OpenApiExample
from drf_spectacular.generators import SchemaGenerator
from .responses import standard_response
import logging
import re
import sys
import inspect
from django.conf import settings
from drf_spectacular.drainage import warn

logger = logging.getLogger('api.core.openapi')

class SentineliqSchemaGenerator(SchemaGenerator):
    """
    Custom schema generator that filters out unwanted tags from the OpenAPI schema.
    """
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        
        # Define the tags we want to keep (all others will be removed)
        allowed_tags = [
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
        
        # Define a mapping for old tag names to our standardized ones
        tag_mapping = {
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
            'Notification Channels': 'Notification System',
            'Notification Rules': 'Notification System',
            'Notification Preferences': 'Notification System',
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
            'enrichment': 'Threat Intelligence (SentinelVision)',
            'feeds': 'Threat Intelligence (SentinelVision)',
            'mitre': 'MITRE Framework',
            'api': 'System Monitoring & Operations',
        }

        # Unwanted tags - operations with only these tags will be completely removed
        unwanted_tags = [
            'api', 'Common', 'System', 'MITRE Mappings', 'MITRE ATT&CK',
            'mitre', 'Notifications', 'sentinelvision', 'enrichment',
            'sentinel-vision', 'feeds'
        ]
        
        # Filter operations by tag
        if 'paths' in schema:
            for path, path_item in list(schema['paths'].items()):
                for method, operation in list(path_item.items()):
                    if method in ['get', 'post', 'put', 'patch', 'delete']:
                        # Skip operations without tags
                        if 'tags' not in operation:
                            operation['tags'] = ['System Monitoring & Operations']
                            continue
                        
                        # Check if the operation only has unwanted tags
                        if all(tag in unwanted_tags for tag in operation['tags']):
                            # Remove this operation completely
                            del path_item[method]
                            continue
                        
                        # Map old tags to new ones and filter out any unmapped tags
                        new_tags = []
                        for tag in operation['tags']:
                            if tag in allowed_tags:
                                new_tags.append(tag)
                            elif tag in tag_mapping:
                                new_tags.append(tag_mapping[tag])
                        
                        # If no valid tags remain, assign to System Monitoring & Operations
                        if not new_tags:
                            new_tags = ['System Monitoring & Operations']
                        
                        # Deduplicate tags
                        operation['tags'] = list(set(new_tags))
                
                # Remove empty path items
                if not any(method in path_item for method in ['get', 'post', 'put', 'patch', 'delete']):
                    del schema['paths'][path]
        
        # Only keep the allowed tags in the tags section and ensure they're all defined
        if 'tags' in schema:
            # Keep only allowed tags and remove all others
            schema['tags'] = [tag for tag in schema['tags'] if tag.get('name') in allowed_tags]
            
            # Ensure all allowed tags are defined
            existing_tag_names = [tag['name'] for tag in schema['tags']]
            for tag_name in allowed_tags:
                if tag_name not in existing_tag_names:
                    # Add tag if it's missing but needed
                    description = self._get_tag_description(tag_name)
                    schema['tags'].append({
                        'name': tag_name,
                        'description': description
                    })
            
            # IMPORTANT: Explicitly ensure unwanted tags are removed from the schema's tags list
            # This guarantees they don't appear in the Swagger UI dropdown
            schema['tags'] = [tag for tag in schema['tags'] if tag.get('name') not in unwanted_tags]
        
        return schema
    
    def _get_tag_description(self, tag_name):
        """
        Get a standard description for a tag if we need to add it.
        """
        descriptions = {
            'Authentication & Access Control': 'Endpoints for user login, JWT token handling, and RBAC access policies.',
            'Company Management': 'Multi-tenant company provisioning, configuration, and statistics.',
            'Alert Management': 'Security alert lifecycle including creation, triage, classification, and correlation.',
            'Incident Management': 'Case and incident tracking with escalation, investigation, and resolution workflow.',
            'Observables & IOCs': 'Submission, enrichment, tagging, and search of indicators of compromise.',
            'Threat Intelligence (SentinelVision)': 'Analyzer modules, threat feeds, and automated responders for enrichment and action.',
            'Notification System': 'Notification rules, delivery methods (e-mail, Slack, webhook), and logs.',
            'Knowledge Base (Wiki)': 'Internal documentation including runbooks, categories, and standard procedures.',
            'Reporting': 'Report generation in Markdown or PDF format for audit and evidence purposes.',
            'System Monitoring & Operations': 'Health checks, logs, background tasks, and platform-level diagnostics.',
            'Task Management': 'Assignment and tracking of security tasks and playbook execution.',
            'MITRE Framework': 'MITRE ATT&CK framework mapping and threat intelligence correlation.',
        }
        return descriptions.get(tag_name, 'Endpoints related to ' + tag_name)


def get_examples(examples_request, **kwargs):
    """
    Factory function for generating standardized API response examples.
    
    This function helps DRF Spectacular generate example responses in the standardized format.
    
    Args:
        examples_request: The examples request context from DRF Spectacular
        
    Returns:
        Dictionary of example responses
    """
    operation_id = examples_request.get("operation_id", "")
    
    # Example responses by operation pattern
    examples = {}
    
    # User examples
    if operation_id.startswith("user_"):
        if "list" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data=[
                        {
                            "id": 1,
                            "username": "admin@example.com",
                            "email": "admin@example.com",
                            "first_name": "Admin",
                            "last_name": "User",
                            "company": {
                                "id": 1,
                                "name": "Example Company"
                            },
                            "is_active": True,
                            "is_superuser": True,
                            "is_admin_company": False,
                            "is_analyst_company": False,
                            "date_joined": "2023-05-15T10:00:00Z"
                        }
                    ],
                    metadata={
                        "pagination": {
                            "count": 1,
                            "page": 1,
                            "pages": 1,
                            "page_size": 50,
                            "next": None,
                            "previous": None
                        }
                    }
                )
            )
        elif "retrieve" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data={
                        "id": 1,
                        "username": "admin@example.com",
                        "email": "admin@example.com",
                        "first_name": "Admin",
                        "last_name": "User",
                        "company": {
                            "id": 1,
                            "name": "Example Company"
                        },
                        "is_active": True,
                        "is_superuser": True,
                        "is_admin_company": False,
                        "is_analyst_company": False,
                        "date_joined": "2023-05-15T10:00:00Z"
                    }
                )
            )
    
    # Company examples
    elif operation_id.startswith("company_"):
        if "list" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data=[
                        {
                            "id": 1,
                            "name": "Example Company",
                            "created_at": "2023-05-15T10:00:00Z",
                            "updated_at": "2023-05-15T10:00:00Z"
                        }
                    ],
                    metadata={
                        "pagination": {
                            "count": 1,
                            "page": 1,
                            "pages": 1,
                            "page_size": 50,
                            "next": None,
                            "previous": None
                        }
                    }
                )
            )
    
    # Authentication examples
    elif operation_id.startswith("token_"):
        if "obtain" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": 1,
                            "username": "admin@example.com",
                            "email": "admin@example.com",
                            "first_name": "Admin",
                            "last_name": "User"
                        }
                    },
                    message="Authentication successful"
                )
            )
        elif "refresh" in operation_id:
            examples["200"] = OpenApiExample(
                name="Success",
                value=standard_response(
                    data={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    },
                    message="Token refreshed successfully"
                )
            )
    
    # Default error responses
    examples["400"] = OpenApiExample(
        name="Validation Error",
        value=standard_response(
            status_type="error",
            message="Invalid data provided",
            data={
                "field_name": [
                    "Error message about this field"
                ]
            },
            code=400
        )
    )
    
    examples["401"] = OpenApiExample(
        name="Unauthorized",
        value=standard_response(
            status_type="error",
            message="Authentication credentials were not provided or are invalid",
            code=401
        )
    )
    
    examples["403"] = OpenApiExample(
        name="Forbidden",
        value=standard_response(
            status_type="error",
            message="You do not have permission to perform this action",
            code=403
        )
    )
    
    examples["404"] = OpenApiExample(
        name="Not Found",
        value=standard_response(
            status_type="error",
            message="The requested resource was not found",
            code=404
        )
    )
    
    examples["500"] = OpenApiExample(
        name="Server Error",
        value=standard_response(
            status_type="error",
            message="An unexpected error occurred",
            code="server_error"
        )
    )
    
    return examples 

def get_examples():
    """
    Factory function for example responses used in the OpenAPI schema.
    This is configured via SPECTACULAR_SETTINGS['EXAMPLES_FACTORY'].
    
    Returns:
        dict: Example responses mapped by key
    """
    return {
        # Generic examples
        'error_response': {
            'value': {
                'status': 'error',
                'message': 'An error occurred while processing the request.',
                'data': None
            }
        },
        'success_response': {
            'value': {
                'status': 'success',
                'message': 'Operation completed successfully.',
                'data': {}
            }
        },
    }

def custom_enum_name_resolver(enum_cls):
    """
    Custom function to resolve enum naming collisions in DRF-Spectacular.
    This function provides consistent, readable names for enum fields to avoid
    collisions and cryptic hash suffixes.
    
    Args:
        enum_cls: The Enum class for which to generate a schema name
        
    Returns:
        str: A unique, readable name for the Enum in the OpenAPI schema
    """
    # Get the class name
    class_name = enum_cls.__name__
    
    # Get the module path
    module_path = enum_cls.__module__
    
    # Get the calling model class name if possible
    calling_frame = None
    for frame in inspect.stack()[1:]:
        if 'models.py' in frame.filename or 'serializers.py' in frame.filename:
            calling_frame = frame
            break
    
    model_context = ""
    if calling_frame:
        # Extract model name from the frame's local variables if possible
        if 'self' in calling_frame.frame.f_locals:
            self_obj = calling_frame.frame.f_locals['self']
            if hasattr(self_obj, '__class__'):
                model_context = self_obj.__class__.__name__
    
    # Strip 'Enum' suffix if present
    if class_name.endswith('Enum'):
        base_name = class_name[:-4]
    else:
        base_name = class_name
    
    # Extract context from the module path components
    module_parts = module_path.split('.')
    app_name = ""
    model_name = ""
    
    # Find the app name from the module path
    for part in module_parts:
        if part in ['alerts', 'incidents', 'tasks', 'observables', 'sentinelvision', 'notifications', 
                   'mitre', 'reporting', 'wiki', 'companies']:
            app_name = part
            break
    
    # Convert app name to proper prefix
    app_prefix = ""
    if app_name == 'alerts':
        app_prefix = 'Alert'
    elif app_name == 'incidents':
        app_prefix = 'Incident'
    elif app_name == 'tasks':
        app_prefix = 'Task'
    elif app_name == 'observables':
        app_prefix = 'Observable'
    elif app_name == 'notifications':
        app_prefix = 'Notification'
    elif app_name == 'sentinelvision':
        app_prefix = 'SentinelVision'
    elif app_name == 'mitre':
        app_prefix = 'Mitre'
    elif app_name == 'reporting':
        app_prefix = 'Report'
    elif app_name == 'wiki':
        app_prefix = 'Article'
    elif app_name == 'companies':
        app_prefix = 'Company'
    
    # Special handling for common field names
    common_fields = ('Status', 'Priority', 'TLP', 'PAP', 'Type', 'Category', 'Format', 'Template', 'Level')
    
    if base_name in common_fields:
        # Always add app prefix for common fields to avoid collisions
        if app_prefix:
            return f"{app_prefix}{base_name}"
    
    # Special cases based on specific module contents
    if 'EnrichedIOC' in module_path and base_name == 'Status':
        return 'EnrichmentStatus'
    
    if 'FeedExecutionRecord' in module_path and base_name == 'Status':
        return 'ExecutionStatus'
    
    if 'EnrichedIOC' in module_path and base_name == 'TLP':
        return 'TLPLevel'
    
    if 'EnrichedIOC' in module_path and base_name == 'IOCType':
        return 'IOCType'
        
    # If the name already starts with a known prefix, keep it as-is
    prefixes = ('Alert', 'Incident', 'Task', 'Observable', 'Notification', 
               'Mitre', 'Company', 'Report', 'Article', 'Module', 'Feed', 
               'SentinelVision', 'Enrichment', 'Execution', 'IOC')
    
    for prefix in prefixes:
        if base_name.startswith(prefix):
            return base_name
    
    # Direct module-based mappings for common collision fields
    if 'execution' in module_path.lower() and base_name == 'Status':
        return 'ExecutionStatus'
        
    if 'enrichment' in module_path.lower() and base_name == 'Status':
        return 'EnrichmentStatus'
        
    if base_name == 'Status' and app_prefix:
        return f"{app_prefix}Status"
        
    if base_name == 'Type' and app_prefix:
        return f"{app_prefix}Type"
        
    if base_name == 'Category' and app_prefix:
        return f"{app_prefix}Category"
        
    if base_name == 'Priority' and app_prefix:
        return f"{app_prefix}Priority"
    
    # Return the base name if we couldn't determine a better name
    # If we have an app prefix and it's not already part of the name, add it
    if app_prefix and not base_name.startswith(app_prefix):
        return f"{app_prefix}{base_name}"
    
    return base_name

def reset_generator_stats_hook(generator, **kwargs):
    """
    Custom hook for DRF-Spectacular that can be used to reset generator stats
    or modify schema components before final schema generation.
    
    Args:
        generator: The schema generator instance
        
    Returns:
        dict: Modified schema
    """
    schema = kwargs.get('schema', {})
    
    # Reset enum collision counters if needed
    if hasattr(generator, '_enum_collision_counter'):
        generator._enum_collision_counter = {}
    
    # Apply custom enum name handling
    if 'components' in schema and 'schemas' in schema['components']:
        for schema_name, schema_def in list(schema['components']['schemas'].items()):
            # Fix any auto-generated enum names with hash suffixes
            pattern = r'([A-Za-z]+)([0-9a-f]{3})Enum$'
            match = re.match(pattern, schema_name)
            if match:
                base_name = match.group(1)
                # Create a cleaner name without the hash
                new_name = f'{base_name}Enum'
                
                # Only rename if the new name doesn't already exist
                if new_name not in schema['components']['schemas']:
                    schema['components']['schemas'][new_name] = schema_def
                    # Update references to this schema
                    _update_references(schema, f'#/components/schemas/{schema_name}', 
                                      f'#/components/schemas/{new_name}')
                    # Remove the old schema
                    del schema['components']['schemas'][schema_name]
    
    return schema

def _update_references(obj, old_ref, new_ref):
    """
    Recursively update $ref values in a schema object.
    
    Args:
        obj: The object to update
        old_ref: The reference string to replace
        new_ref: The new reference string
    """
    if isinstance(obj, dict):
        for key, value in list(obj.items()):
            if key == '$ref' and value == old_ref:
                obj[key] = new_ref
            elif isinstance(value, (dict, list)):
                _update_references(value, old_ref, new_ref)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                _update_references(item, old_ref, new_ref) 