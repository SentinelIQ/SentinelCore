"""
API module for SentinelIQ.
"""
default_app_config = 'api.apps.ApiConfig'

# Import core tasks to ensure they are registered
from api.core.tasks import run_migrations
