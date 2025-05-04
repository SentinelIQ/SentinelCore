# API Script Tools

This directory contains utility scripts for maintaining the Sentineliq API.

## OpenAPI Schema Tools

These scripts help maintain the enterprise-grade OpenAPI/Swagger documentation.

### All-in-One Tag Fixer

The easiest way to fix/update all OpenAPI tags is using the all-in-one script:

```bash
# Run in dry-run mode first to see what would change
./api/scripts/fix_openapi_tags.sh --dry-run

# Then run without the flag to apply the changes
./api/scripts/fix_openapi_tags.sh
```

This script will:
1. Perform a dry run to show what would change
2. Update `@extend_schema` tags
3. Update `@extend_schema_view` definitions
4. Verify the schema meets enterprise standards

### Individual Tag Update Scripts

If you need more control, you can run the individual scripts:

1. **`update_openapi_tags.py`**: Updates all `@extend_schema(tags=...)` instances in the codebase to use the current enterprise tag structure

   ```bash
   # Dry run mode (no changes)
   docker compose exec web python api/scripts/update_openapi_tags.py --dry-run
   
   # Apply changes
   docker compose exec web python api/scripts/update_openapi_tags.py
   ```

2. **`update_openapi_views.py`**: Updates tags in `@extend_schema_view` definitions with multiple view actions 

   ```bash
   # Dry run mode (no changes)
   docker compose exec web python api/scripts/update_openapi_views.py --dry-run
   
   # Apply changes
   docker compose exec web python api/scripts/update_openapi_views.py
   ```

3. **`verify_openapi_tags.py`**: Verifies that the OpenAPI schema meets enterprise standards

   ```bash
   docker compose exec web python api/scripts/verify_openapi_tags.py
   ```

### Safety Features

These scripts include safety features to prevent corrupting files:

- Improved regex patterns that avoid replacing tags inside string literals
- Processing matches in reverse order to maintain file integrity
- Preserving whitespace and context around tag declarations
- Dry run mode to preview changes before applying them

⚠️ **Warning**: After running these scripts, always check the updated files for potential issues. If any syntax errors occur when restarting the server, check for corrupted tags in string literals.

### When to Use

Run these scripts after:
- Adding new domains to `SPECTACULAR_SETTINGS['TAGS']` in settings.py
- Noticing inconsistent tag usage in the API documentation
- Refactoring domains or renaming tags
- Seeing unwanted legacy tags in the Swagger UI

### Tag Structure

The current tag structure follows Domain-Driven Design principles:

- Authentication & Access Control
- Company Management
- Alert Management
- Incident Management
- Observables & IOCs
- Threat Intelligence (SentinelVision)
- Notification System
- Knowledge Base (Wiki)
- Reporting
- System Monitoring & Operations
- Task Management
- MITRE Framework

For detailed documentation on the tag structure, see `/docs/api_tag_structure.md`.

## Adding New Tags

To add a new domain tag:

1. Update `TAG_MAPPING` in both scripts with the new mapping
2. Update `SPECTACULAR_SETTINGS['TAGS']` in settings.py
3. Run both scripts to apply the changes
4. Update documentation in `/docs/api_tag_structure.md`
5. Always restart the server and check for any syntax errors after running the scripts 