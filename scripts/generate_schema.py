#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')
django.setup()

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenAPIYAMLRenderer
from django.urls import get_resolver

def generate_schema():
    """Generate OpenAPI schema and save it to docs directory."""
    print("Generating OpenAPI schema...")
    
    # Initialize schema generator
    generator = SchemaGenerator(
        title="SentinelIQ API",
        version="v1",
        patterns=get_resolver().url_patterns
    )
    
    # Generate schema
    schema = generator.get_schema(request=None, public=True)
    
    # Convert to YAML
    renderer = OpenAPIYAMLRenderer()
    yaml_schema = renderer.render(schema, renderer_context={})
    
    # Save to docs directory
    schema_path = project_root / 'docs' / 'schema.yaml'
    schema_path.write_bytes(yaml_schema)
    
    print(f"Schema generated successfully at: {schema_path}")

if __name__ == '__main__':
    generate_schema() 