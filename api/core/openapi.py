from drf_spectacular.utils import OpenApiExample
from drf_spectacular.generators import SchemaGenerator
from .responses import standard_response


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