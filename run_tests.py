#!/usr/bin/env python3
"""
Test runner script for the licensing system.
Provides convenient commands to run different types of tests.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command '{cmd[0]}' not found. Please install pytest.")
        return 1


def install_test_deps():
    """Install test dependencies."""
    print("Installing test dependencies...")
    return run_command([sys.executable, "-m", "pip", "install", "-r", "tests/requirements-test.txt"])


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=licensing", "--cov-report=html", "--cov-report=term"])
    
    # Exclude integration tests by default
    cmd.extend(["-m", "not integration"])
    
    return run_command(cmd)


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/test_integration.py"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd)


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=licensing", "--cov-report=html", "--cov-report=term"])
    
    return run_command(cmd)


def run_specific_test(test_file, verbose=False):
    """Run a specific test file."""
    cmd = [sys.executable, "-m", "pytest", f"tests/{test_file}"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd)


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Test runner for licensing system")
    parser.add_argument("command", choices=[
        "install", "unit", "integration", "all", "specific", "coverage"
    ], help="Test command to run")
    
    parser.add_argument("--file", help="Specific test file to run (for 'specific' command)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    exit_code = 0
    
    if args.command == "install":
        exit_code = install_test_deps()
        
    elif args.command == "unit":
        exit_code = run_unit_tests(verbose=args.verbose)
        
    elif args.command == "integration":
        exit_code = run_integration_tests(verbose=args.verbose)
        
    elif args.command == "all":
        exit_code = run_all_tests(verbose=args.verbose)
        
    elif args.command == "coverage":
        exit_code = run_all_tests(verbose=args.verbose, coverage=True)
        
    elif args.command == "specific":
        if not args.file:
            print("Error: --file argument required for 'specific' command")
            exit_code = 1
        else:
            exit_code = run_specific_test(args.file, verbose=args.verbose)
    
    if exit_code == 0:
        print("\n✓ Tests completed successfully!")
    else:
        print(f"\n✗ Tests failed with exit code {exit_code}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
