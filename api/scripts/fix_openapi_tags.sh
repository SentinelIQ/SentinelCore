#!/bin/bash

# fix_openapi_tags.sh - Enterprise-grade OpenAPI tag structure sanitizer
# 
# This script runs all the tools needed to fix the OpenAPI tag structure:
# 1. First performs a dry run to show what would change
# 2. Then runs the tag update scripts to fix @extend_schema tags
# 3. Next updates view tags in @extend_schema_view decorators
# 4. Finally verifies the schema structure to ensure it meets enterprise standards
#
# Usage:
#   ./api/scripts/fix_openapi_tags.sh [--dry-run]

set -e

echo "🔧 Sentineliq Enterprise-grade OpenAPI Tag Fixer"
echo "==============================================="
echo

# Check if we're running in dry run mode
DRY_RUN=0
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=1
    break
  fi
done

if [[ $DRY_RUN -eq 1 ]]; then
  echo "🔍 DRY RUN MODE: No changes will be made"
else
  echo "⚠️ LIVE MODE: Changes will be applied to your codebase"
  
  # Ask for confirmation in live mode
  read -p "Do you want to continue? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled"
    exit 1
  fi
fi

echo
echo "Step 1: Checking for outdated OpenAPI tags"
echo "-----------------------------------------"

# First, run tag updates in dry run mode to see what would change
docker compose exec web python api/scripts/update_openapi_tags.py --dry-run
echo
docker compose exec web python api/scripts/update_openapi_views.py --dry-run

# If not in dry run mode, apply the changes
if [[ $DRY_RUN -eq 0 ]]; then
  echo
  echo "Step 2: Updating @extend_schema tags"
  echo "-----------------------------------"
  docker compose exec web python api/scripts/update_openapi_tags.py
  
  echo
  echo "Step 3: Updating @extend_schema_view tags"
  echo "---------------------------------------"
  docker compose exec web python api/scripts/update_openapi_views.py
fi

echo
echo "Step 4: Verifying OpenAPI schema structure"
echo "----------------------------------------"
docker compose exec web python api/scripts/verify_openapi_tags.py

echo
if [[ $DRY_RUN -eq 1 ]]; then
  echo "✅ Dry run completed. No changes were made."
  echo "   To apply the changes, run this script without the --dry-run flag."
else
  echo "✅ Tag update completed. All changes have been applied."
  echo "   You should restart the Django server for changes to take effect:"
  echo "   docker compose restart web"
fi

# Set execute permissions for this script
chmod +x "$(dirname "$0")/fix_openapi_tags.sh" 