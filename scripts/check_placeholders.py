#!/usr/bin/env python
import os
import sys
from pathlib import Path
import re
from typing import List, Dict, Any, Set
from dataclasses import dataclass

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent

@dataclass
class PlaceholderResult:
    file_path: str
    line_number: int
    line_content: str
    placeholder_type: str

def get_python_files() -> List[Path]:
    """Get all Python files in the project."""
    python_files = []
    for path in project_root.rglob('*.py'):
        # Skip migrations, venv, and cache directories
        if not any(part in str(path) for part in ['migrations', 'venv', '__pycache__', '.git']):
            python_files.append(path)
    return python_files

def check_file_for_placeholders(file_path: Path) -> List[PlaceholderResult]:
    """Check a file for placeholders and TODOs."""
    results = []
    patterns = {
        'TODO': r'\bTODO\b',
        'FIXME': r'\bFIXME\b',
        'pass statement': r'\bpass\b',
        'NotImplementedError': r'\bNotImplementedError\b',
        'raise NotImplemented': r'raise\s+NotImplemented\b',
        'ellipsis': r'\.\.\.',
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            for placeholder_type, pattern in patterns.items():
                if re.search(pattern, line):
                    results.append(PlaceholderResult(
                        file_path=str(file_path.relative_to(project_root)),
                        line_number=i,
                        line_content=line.strip(),
                        placeholder_type=placeholder_type
                    ))
    
    return results

def main():
    """Main function to check for placeholders in the codebase."""
    print("Checking for placeholders and TODOs in the codebase...")
    
    python_files = get_python_files()
    all_results: List[PlaceholderResult] = []
    
    for file_path in python_files:
        results = check_file_for_placeholders(file_path)
        all_results.extend(results)
    
    # Group results by file
    files_with_issues: Dict[str, List[PlaceholderResult]] = {}
    for result in all_results:
        if result.file_path not in files_with_issues:
            files_with_issues[result.file_path] = []
        files_with_issues[result.file_path].append(result)
    
    # Print results
    print("\nValidation Results:")
    print("==================")
    
    if not files_with_issues:
        print("✅ No placeholders or TODOs found in the codebase!")
    else:
        for file_path, results in sorted(files_with_issues.items()):
            print(f"\n{file_path}:")
            for result in sorted(results, key=lambda x: x.line_number):
                print(f"  Line {result.line_number}: {result.placeholder_type}")
                print(f"    {result.line_content}")
    
    # Print summary
    total_files = len(python_files)
    files_with_placeholders = len(files_with_issues)
    total_placeholders = len(all_results)
    
    print(f"\nSummary:")
    print(f"Total Python files: {total_files}")
    print(f"Files with placeholders: {files_with_placeholders}")
    print(f"Total placeholders found: {total_placeholders}")
    
    if files_with_placeholders > 0:
        print("\n❌ Found placeholders or TODOs that need to be addressed!")
        sys.exit(1)
    else:
        print("\n✅ All files are compliant!")
        sys.exit(0)

if __name__ == '__main__':
    main() 