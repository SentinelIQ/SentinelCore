#!/bin/bash

# Script to generate and validate OpenAPI schema
# This helps verify that enum standardization is working correctly
# and identifies any naming collisions

# Navigate to project root
cd $(dirname $0)/..

# Set environment variables
export DJANGO_SETTINGS_MODULE=sentineliq.settings

echo "Generating OpenAPI schema..."
docker compose exec web python manage.py spectacular --validate --file openapi-schema.yaml

if [ $? -eq 0 ]; then
    echo "✅ Schema validation successful!"
    echo "Schema saved to: openapi-schema.yaml"
    
    # Count enums in the schema
    echo "Analyzing schema for enums..."
    ENUM_COUNT=$(grep -c "enum:" openapi-schema.yaml)
    echo "Total enums found: $ENUM_COUNT"
    
    # Extract enum names
    echo "Extracting enum names..."
    ENUM_NAMES=$(grep -A 1 "enum:" openapi-schema.yaml | grep "title:" | awk '{print $2}' | sort | uniq)
    
    echo "Enum names in schema:"
    echo "$ENUM_NAMES"
    
    # Check for duplicate enum names (which would indicate collisions)
    DUPLICATE_COUNT=$(grep -A 1 "enum:" openapi-schema.yaml | grep "title:" | awk '{print $2}' | sort | uniq -d | wc -l)
    
    if [ $DUPLICATE_COUNT -eq 0 ]; then
        echo "✅ No enum name collisions detected!"
    else
        echo "❌ Found $DUPLICATE_COUNT enum name collisions:"
        grep -A 1 "enum:" openapi-schema.yaml | grep "title:" | awk '{print $2}' | sort | uniq -d
    fi
else
    echo "❌ Schema validation failed!"
fi 