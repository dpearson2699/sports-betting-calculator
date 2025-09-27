#!/usr/bin/env python3
"""Test runner script for the betting framework"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=True):
    """Run tests with various options"""
    
    # Base pytest command
    cmd = ["uv", "run", "pytest"]
    
    # Add test type selection
    if test_type == "unit":
        cmd.append("tests/unit")
    elif test_type == "integration":
        cmd.append("tests/integration")
    elif test_type == "all":
        cmd.append("tests")
    else:
        cmd.append(test_type)  # Allow custom path
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=src", 
            "--cov-report=term-missing",
            "--cov-report=html:test-results/coverage"
        ])
    
    # Add markers for organized output
    cmd.extend(["-ra", "--tb=short"])
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def run_quick_tests():
    """Run only fast unit tests"""
    cmd = [
        "uv", "run", "pytest", 
        "tests/unit", 
        "-v", 
        "-m", "not slow",
        "--tb=short"
    ]
    print(f"Running quick tests: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def run_with_coverage():
    """Run tests with detailed coverage reporting"""
    cmd = [
        "uv", "run", "pytest",
        "tests",
        "--cov=src",
        "--cov-report=term-missing", 
        "--cov-report=html:test-results/coverage",
        "--cov-report=xml:test-results/coverage.xml",
        "-v"
    ]
    print(f"Running with coverage: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run betting framework tests")
    parser.add_argument(
        "test_type", 
        nargs="?", 
        default="all",
        choices=["all", "unit", "integration", "quick"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-cov", 
        action="store_true",
        help="Skip coverage reporting"
    )
    parser.add_argument(
        "--html", 
        action="store_true",
        help="Generate HTML coverage report"
    )
    
    args = parser.parse_args()
    
    if args.test_type == "quick":
        return run_quick_tests().returncode
    else:
        coverage = not args.no_cov
        return run_tests(args.test_type, args.verbose, coverage).returncode


if __name__ == "__main__":
    sys.exit(main())