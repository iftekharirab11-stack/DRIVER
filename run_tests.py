#!/usr/bin/env python3
"""
Test Runner Script for Driver AI Application

Runs both backend (Python/pytest) and frontend (Vitest) tests.
"""

import subprocess
import sys
import os
import argparse

def run_backend_tests(coverage=False):
    """Run pytest on backend tests."""
    print("=" * 60)
    print("Running Backend Tests (pytest)")
    print("=" * 60)
    
    # Install Python test dependencies if needed
    print("\n[1/2] Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-test.txt"], 
                   capture_output=True)
    
    # Run pytest
    print("[2/2] Running tests...\n")
    cmd = [sys.executable, "-m", "pytest"]
    cmd += ["-v", "--tb=short"]
    if coverage:
        cmd += ["--cov=.", "--cov-report=term-missing", "--cov-report=html"]
    cmd += ["test_main.py", "test_integration.py", "test-schema.py"]
    
    result = subprocess.run(cmd)
    return result.returncode

def run_frontend_tests(coverage=False):
    """Run Vitest on frontend tests."""
    print("\n" + "=" * 60)
    print("Running Frontend Tests (Vitest)")
    print("=" * 60)
    
    os.chdir("project/frontend")
    
    # Install dependencies if needed
    print("\n[1/2] Installing test dependencies...")
    subprocess.run(["npm", "install", "-q"], capture_output=True)
    
    # Run vitest
    print("[2/2] Running tests...\n")
    cmd = ["npx", "vitest", "run"]
    if coverage:
        cmd += ["--coverage"]
    
    result = subprocess.run(cmd)
    os.chdir("../..")
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Run application tests")
    parser.add_argument("--backend-only", action="store_true", 
                       help="Run only backend tests")
    parser.add_argument("--frontend-only", action="store_true",
                       help="Run only frontend tests")
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage reports")
    args = parser.parse_args()
    
    exit_codes = []
    
    if not args.frontend_only:
        exit_codes.append(run_backend_tests(coverage=args.coverage))
    
    if not args.backend_only:
        exit_codes.append(run_frontend_tests(coverage=args.coverage))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for i, code in enumerate(exit_codes):
        if i == 0 and not args.frontend_only:
            name = "Backend"
        elif args.frontend_only and i == 0:
            name = "Frontend"
        else:
            name = "Frontend"
        
        status = "PASSED" if code == 0 else "FAILED"
        print(f"{name}: {status} (exit code: {code})")
    
    return max(exit_codes) if exit_codes else 0

if __name__ == "__main__":
    sys.exit(main())
