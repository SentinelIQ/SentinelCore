#!/usr/bin/env python
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Get project root directory
project_root = Path(__file__).resolve().parent.parent

@dataclass
class ComplianceCheckResult:
    check_name: str
    passed: bool
    output: str
    error_output: str

def run_check(script_name: str, description: str) -> ComplianceCheckResult:
    """Run a compliance check script and return the result."""
    script_path = project_root / 'scripts' / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=False
        )
        return ComplianceCheckResult(
            check_name=description,
            passed=result.returncode == 0,
            output=result.stdout,
            error_output=result.stderr
        )
    except Exception as e:
        return ComplianceCheckResult(
            check_name=description,
            passed=False,
            output="",
            error_output=str(e)
        )

def main():
    """Run all compliance checks."""
    print("Running SentinelIQ Enterprise Standards Compliance Checks...")
    print("=======================================================")
    
    checks = [
        ('generate_schema.py', 'OpenAPI Schema Generation'),
        ('check_api_docs.py', 'API Documentation'),
        ('check_admin_registration.py', 'Django Admin Registration'),
        ('check_placeholders.py', 'Code Placeholders'),
        ('check_logging.py', 'Logging Configuration'),
        ('check_app_structure.py', 'App Structure'),
        ('check_test_structure.py', 'Test Structure'),
        ('check_audit_logs.py', 'Audit Logs Integration'),
    ]
    
    results = []
    for script_name, description in checks:
        print(f"\nRunning {description} check...")
        result = run_check(script_name, description)
        results.append(result)
        
        # Print immediate result
        if result.passed:
            print(f"✅ {description} check passed")
        else:
            print(f"❌ {description} check failed")
    
    # Print detailed results
    print("\n\nDetailed Results:")
    print("================")
    
    for result in results:
        print(f"\n{result.check_name}:")
        print("─" * len(result.check_name))
        if result.passed:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
        
        if result.output:
            print("\nOutput:")
            print(result.output)
        
        if result.error_output:
            print("\nErrors:")
            print(result.error_output)
    
    # Print summary
    passed_checks = sum(1 for r in results if r.passed)
    total_checks = len(results)
    
    print("\nCompliance Summary:")
    print("==================")
    print(f"Total checks: {total_checks}")
    print(f"Passed checks: {passed_checks}")
    print(f"Failed checks: {total_checks - passed_checks}")
    print(f"Compliance rate: {(passed_checks/total_checks)*100:.1f}%")
    
    # List failed checks
    if total_checks - passed_checks > 0:
        print("\nFailed Checks:")
        for result in results:
            if not result.passed:
                print(f"❌ {result.check_name}")
    
    # Exit with error if any checks failed
    sys.exit(0 if passed_checks == total_checks else 1)

if __name__ == '__main__':
    main() 