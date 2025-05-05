#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')
django.setup()

from django.conf import settings

@dataclass
class LoggingCheckResult:
    component: str
    issues: List[str]
    is_valid: bool

def check_logging_directory() -> LoggingCheckResult:
    """Check if logging directory exists and is writable."""
    issues = []
    log_dir = project_root / 'logs'
    
    if not log_dir.exists():
        issues.append("Logging directory does not exist")
    elif not log_dir.is_dir():
        issues.append("'logs' exists but is not a directory")
    else:
        # Check for required log files
        required_logs = ['api.log', 'error.log', 'django.log']
        for log_file in required_logs:
            log_path = log_dir / log_file
            if not log_path.exists():
                issues.append(f"Missing required log file: {log_file}")
            elif not os.access(log_path.parent, os.W_OK):
                issues.append(f"Log directory not writable for: {log_file}")
    
    return LoggingCheckResult(
        component="Logging Directory",
        issues=issues,
        is_valid=len(issues) == 0
    )

def check_logging_settings() -> LoggingCheckResult:
    """Check Django logging settings configuration."""
    issues = []
    
    # Check if LOGGING is defined
    if not hasattr(settings, 'LOGGING'):
        issues.append("LOGGING setting is not defined")
        return LoggingCheckResult(
            component="Logging Settings",
            issues=issues,
            is_valid=False
        )
    
    logging_config = settings.LOGGING
    
    # Check required handlers
    required_handlers = {'file', 'console', 'error_file', 'api_file'}
    if 'handlers' not in logging_config:
        issues.append("No handlers defined in LOGGING")
    else:
        missing_handlers = required_handlers - set(logging_config['handlers'].keys())
        if missing_handlers:
            issues.append(f"Missing required handlers: {', '.join(missing_handlers)}")
    
    # Check formatters
    if 'formatters' not in logging_config:
        issues.append("No formatters defined in LOGGING")
    
    # Check loggers
    if 'loggers' not in logging_config:
        issues.append("No loggers defined in LOGGING")
    else:
        # Check for django and root loggers
        required_loggers = {'django', 'django.request', ''}  # '' is the root logger
        missing_loggers = required_loggers - set(logging_config['loggers'].keys())
        if missing_loggers:
            issues.append(f"Missing required loggers: {', '.join(missing_loggers or ['root'])}")
    
    return LoggingCheckResult(
        component="Logging Settings",
        issues=issues,
        is_valid=len(issues) == 0
    )

def check_logging_usage() -> LoggingCheckResult:
    """Check logging usage in Python files."""
    issues = []
    
    # Get all Python files
    python_files = []
    for path in project_root.rglob('*.py'):
        if not any(part in str(path) for part in ['migrations', 'venv', '__pycache__', '.git']):
            python_files.append(path)
    
    # Check for proper logging imports and usage
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for print statements used for logging
            if 'print(' in content and not file_path.name.startswith('test_'):
                issues.append(f"Found print statements in {file_path.relative_to(project_root)}")
            
            # Check for proper logging import
            if 'import logging' not in content and any(log_call in content for log_call in ['.info(', '.error(', '.warning(', '.debug(']):
                issues.append(f"Missing logging import in {file_path.relative_to(project_root)}")
    
    return LoggingCheckResult(
        component="Logging Usage",
        issues=issues,
        is_valid=len(issues) == 0
    )

def main():
    """Main function to check logging configuration compliance."""
    print("Checking logging configuration compliance...")
    
    checks = [
        check_logging_directory(),
        check_logging_settings(),
        check_logging_usage()
    ]
    
    # Print results
    print("\nValidation Results:")
    print("==================")
    
    all_valid = True
    for result in checks:
        print(f"\n{result.component}:")
        if result.is_valid:
            print("✅ Configuration compliant")
        else:
            all_valid = False
            print("❌ Configuration issues found:")
            for issue in result.issues:
                print(f"  - {issue}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total checks: {len(checks)}")
    print(f"Passing checks: {sum(1 for c in checks if c.is_valid)}")
    print(f"Failing checks: {sum(1 for c in checks if not c.is_valid)}")
    
    # Exit with error if any checks failed
    sys.exit(0 if all_valid else 1)

if __name__ == '__main__':
    main() 