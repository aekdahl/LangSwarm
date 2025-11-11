#!/usr/bin/env python3
"""
Navigation System Test Runner

This script runs the complete test suite for the intelligent navigation system.
It provides options for running specific test categories, generating coverage reports,
and outputting results in different formats.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def run_pytest(test_paths, coverage=False, verbose=False, output_format="text"):
    """Run pytest with specified options"""
    cmd = ["python", "-m", "pytest"]
    
    # Add test paths
    cmd.extend(test_paths)
    
    # Add options based on parameters
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend([
            "--cov=langswarm.features.intelligent_navigation",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    if output_format == "xml":
        cmd.extend(["--junit-xml=test_results.xml"])
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run navigation system tests")
    
    # Test selection options
    parser.add_argument(
        "--schema", action="store_true",
        help="Run only schema and configuration tests"
    )
    parser.add_argument(
        "--navigator", action="store_true", 
        help="Run only navigator and tool tests"
    )
    parser.add_argument(
        "--tracker", action="store_true",
        help="Run only tracking and analytics tests"
    )
    parser.add_argument(
        "--integration", action="store_true",
        help="Run only integration tests"
    )
    
    # Output options
    parser.add_argument(
        "--coverage", action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--xml", action="store_true",
        help="Output results in XML format"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Quiet output (minimal)"
    )
    
    # Performance options
    parser.add_argument(
        "--fast", action="store_true",
        help="Run tests in fast mode (skip slow tests)"
    )
    
    args = parser.parse_args()
    
    # Determine which tests to run
    test_files = []
    current_dir = Path(__file__).parent
    
    if args.schema:
        test_files.append(str(current_dir / "test_schema.py"))
    
    if args.navigator:
        test_files.append(str(current_dir / "test_navigator.py"))
    
    if args.tracker:
        test_files.append(str(current_dir / "test_tracker.py"))
    
    if args.integration:
        # Look for integration test files
        integration_files = list(current_dir.glob("test_*integration*.py"))
        test_files.extend(str(f) for f in integration_files)
    
    # If no specific tests selected, run all
    if not test_files:
        test_files = [str(current_dir)]
    
    # Set output format
    output_format = "xml" if args.xml else "text"
    
    # Set verbosity
    verbose = args.verbose and not args.quiet
    
    print("🧭 Running LangSwarm Navigation System Tests")
    print("=" * 50)
    
    if args.coverage:
        print("📊 Coverage reporting enabled")
    
    if args.fast:
        print("⚡ Fast mode: skipping slow tests")
        # Add pytest markers for fast tests if implemented
    
    print(f"📁 Test files: {len(test_files)}")
    for test_file in test_files:
        print(f"   - {Path(test_file).name}")
    
    print()
    
    # Run the tests
    exit_code = run_pytest(
        test_files,
        coverage=args.coverage,
        verbose=verbose,
        output_format=output_format
    )
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
        
        if args.xml:
            print("📄 XML report generated: test_results.xml")
            
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 