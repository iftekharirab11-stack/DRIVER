#!/usr/bin/env python3
"""
AUDIT_FIXES_VERIFICATION.py - Verify critical fixes from the audit report

This script validates that all P0 and P1 critical issues have been addressed.
"""

import os
import sys
import json
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{RESET}\n")

def check_pass(msg):
    print(f"{GREEN}✓ PASS{RESET}: {msg}")

def check_fail(msg):
    print(f"{RED}✗ FAIL{RESET}: {msg}")

def check_warn(msg):
    print(f"{YELLOW}⚠ WARN{RESET}: {msg}")

def check_file_exists(path, description):
    """Check if a file exists."""
    if Path(path).exists():
        check_pass(f"{description} exists at {path}")
        return True
    else:
        check_fail(f"{description} NOT FOUND at {path}")
        return False

def check_file_contains(path, search_string, description):
    """Check if a file contains a specific string."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string in content:
                check_pass(f"{description}")
                return True
            else:
                check_fail(f"{description} - string not found: {search_string}")
                return False
    except Exception as e:
        check_fail(f"Error reading {path}: {e}")
        return False

def check_file_not_contains(path, search_string, description):
    """Check if a file does NOT contain a specific string."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string not in content:
                check_pass(f"{description}")
                return True
            else:
                check_fail(f"{description} - string found but shouldn't be: {search_string}")
                return False
    except Exception as e:
        check_fail(f"Error reading {path}: {e}")
        return False

def main():
    print_header("ALPHA SAAS - CRITICAL AUDIT FIXES VERIFICATION")
    
    project_root = Path(__file__).parent.absolute()
    results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
    
    # ========================================================================
    # P0 CRITICAL FIXES
    # ========================================================================
    print_header("P0 CRITICAL FIXES (Must pass for any deployment)")
    
    # Check 1: requirements.txt exists
    print("1. Checking requirements.txt...")
    if check_file_exists(project_root / "requirements.txt", "requirements.txt"):
        results['passed'] += 1
        # Verify it has key packages
        if check_file_contains(project_root / "requirements.txt", "fastapi", "requirements.txt contains fastapi"):
            results['passed'] += 1
        else:
            results['failed'] += 1
            
        if check_file_contains(project_root / "requirements.txt", "langchain", "requirements.txt contains langchain"):
            results['passed'] += 1
        else:
            results['failed'] += 1
    else:
        results['failed'] += 1
    
    # Check 2: main.py import path is fixed
    print("\n2. Checking main.py import path...")
    if check_file_contains(
        project_root / "main.py",
        "from session_manager import SessionStore",
        "main.py imports SessionStore from session_manager (not DRIVER.session_manager)"
    ):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    if check_file_not_contains(
        project_root / "main.py",
        "from DRIVER.session_manager import SessionStore",
        "main.py does NOT import from DRIVER.session_manager"
    ):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # ========================================================================
    # P1 IMPORTANT FIXES
    # ========================================================================
    print_header("P1 IMPORTANT FIXES")
    
    # Check 3: test_main.py has uuid import
    print("1. Checking test_main.py...")
    if check_file_contains(
        project_root / "test_main.py",
        "import uuid",
        "test_main.py imports uuid"
    ):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Check 4: executor_driver.py telemetry fix
    print("\n2. Checking executor_driver.py telemetry fixes...")
    executor_path = project_root / "DRIVER" / "executor_driver.py"
    
    if check_file_contains(
        executor_path,
        "from DRIVER.telemetry_logger import TelemetryEntry",
        "executor_driver.py imports TelemetryEntry"
    ):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    if check_file_not_contains(
        executor_path,
        ".capitalize()(entry_id",
        "executor_driver.py does NOT use broken .capitalize() pattern"
    ):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    if check_file_contains(
        executor_path,
        "TelemetryEntry(",
        "executor_driver.py uses TelemetryEntry constructor"
    ):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Check 5: Frontend Vue deps removed
    print("\n3. Checking frontend package.json...")
    frontend_package_path = project_root / "project" / "frontend" / "package.json"
    
    try:
        with open(frontend_package_path, 'r') as f:
            pkg = json.load(f)
            
        if check_file_not_contains(
            frontend_package_path,
            '"vue":',
            "package.json does NOT have Vue dependency"
        ):
            results['passed'] += 1
        else:
            results['failed'] += 1
        
        if check_file_not_contains(
            frontend_package_path,
            '"@vue/test-utils":',
            "package.json does NOT have @vue/test-utils"
        ):
            results['passed'] += 1
        else:
            results['failed'] += 1
        
        if check_file_not_contains(
            frontend_package_path,
            '"@testing-library/vue":',
            "package.json does NOT have @testing-library/vue"
        ):
            results['passed'] += 1
        else:
            results['failed'] += 1
            
        if check_file_contains(
            frontend_package_path,
            '"react":',
            "package.json has React dependency"
        ):
            results['passed'] += 1
        else:
            results['failed'] += 1
            
    except Exception as e:
        check_fail(f"Error reading package.json: {e}")
        results['failed'] += 1
    
    # Check 6: FastAPI route path parameter fix
    print("\n4. Checking FastAPI route fixes...")
    if check_file_contains(
        project_root / "main.py",
        '@app.get(f"{API_PREFIX}/files/{{filename}}")',
        "main.py uses correct FastAPI path parameter syntax ({{filename}})"
    ):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # ========================================================================
    # IMPORT TESTS
    # ========================================================================
    print_header("IMPORT VALIDATION TESTS")
    
    print("1. Testing critical Python imports...")
    try:
        sys.path.insert(0, str(project_root))
        
        # Test session_manager import
        try:
            from session_manager import SessionStore
            check_pass("session_manager.SessionStore imports successfully")
            results['passed'] += 1
        except ImportError as e:
            check_fail(f"session_manager.SessionStore import failed: {e}")
            results['failed'] += 1
        
        # Test TelemetryEntry import
        try:
            from DRIVER.telemetry_logger import TelemetryEntry
            check_pass("DRIVER.telemetry_logger.TelemetryEntry imports successfully")
            results['passed'] += 1
        except ImportError as e:
            check_fail(f"DRIVER.telemetry_logger.TelemetryEntry import failed: {e}")
            results['failed'] += 1
            
    except Exception as e:
        check_warn(f"Could not perform import tests: {e}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_header("VERIFICATION SUMMARY")
    
    total = results['passed'] + results['failed'] + results['warnings']
    print(f"Total Checks: {total}")
    print(f"{GREEN}Passed: {results['passed']}{RESET}")
    print(f"{RED}Failed: {results['failed']}{RESET}")
    
    if results['failed'] == 0:
        print(f"\n{GREEN}{'='*70}")
        print(f"SUCCESS! All critical fixes verified.")
        print(f"{'='*70}{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}")
        print(f"FAILURE! {results['failed']} critical check(s) failed.")
        print(f"{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
