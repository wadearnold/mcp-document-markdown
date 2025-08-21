#!/usr/bin/env python3
"""
Test runner for modular PDF converter
"""
import unittest
import sys
import os
from pathlib import Path
import argparse
from typing import List, Optional

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


class TestRunner:
    """Custom test runner with enhanced reporting"""
    
    def __init__(self, verbosity: int = 2):
        self.verbosity = verbosity
        self.test_results = []
    
    def discover_tests(self, test_dir: str, pattern: str = "test_*.py") -> unittest.TestSuite:
        """Discover tests in the specified directory"""
        loader = unittest.TestLoader()
        suite = loader.discover(test_dir, pattern=pattern, top_level_dir=str(Path(__file__).parent))
        return suite
    
    def run_tests(self, test_suite: unittest.TestSuite) -> unittest.TestResult:
        """Run the test suite and return results"""
        runner = unittest.TextTestRunner(verbosity=self.verbosity, stream=sys.stdout)
        result = runner.run(test_suite)
        return result
    
    def run_unit_tests(self) -> unittest.TestResult:
        """Run all unit tests"""
        print("=" * 70)
        print("RUNNING UNIT TESTS")
        print("=" * 70)
        
        unit_tests = self.discover_tests("tests/unit")
        return self.run_tests(unit_tests)
    
    def run_integration_tests(self) -> unittest.TestResult:
        """Run all integration tests"""
        print("=" * 70)
        print("RUNNING INTEGRATION TESTS")
        print("=" * 70)
        
        integration_tests = self.discover_tests("tests/integration")
        return self.run_tests(integration_tests)
    
    def run_all_tests(self) -> List[unittest.TestResult]:
        """Run all tests"""
        results = []
        
        # Run unit tests
        unit_result = self.run_unit_tests()
        results.append(("Unit Tests", unit_result))
        
        print("\n")
        
        # Run integration tests
        integration_result = self.run_integration_tests()
        results.append(("Integration Tests", integration_result))
        
        return results
    
    def print_summary(self, results: List[tuple]) -> None:
        """Print test summary"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        
        for test_type, result in results:
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            total_skipped += len(result.skipped)
            
            status = "PASSED" if (len(result.failures) == 0 and len(result.errors) == 0) else "FAILED"
            print(f"{test_type}: {result.testsRun} tests, {status}")
            
            if result.failures:
                print(f"  Failures: {len(result.failures)}")
            if result.errors:
                print(f"  Errors: {len(result.errors)}")
            if result.skipped:
                print(f"  Skipped: {len(result.skipped)}")
        
        print(f"\nTOTAL: {total_tests} tests")
        print(f"Passed: {total_tests - total_failures - total_errors}")
        print(f"Failed: {total_failures}")
        print(f"Errors: {total_errors}")
        print(f"Skipped: {total_skipped}")
        
        # Overall status
        if total_failures == 0 and total_errors == 0:
            print("\n✅ ALL TESTS PASSED!")
            return True
        else:
            print(f"\n❌ {total_failures + total_errors} TESTS FAILED!")
            return False


def run_specific_test(test_name: str, verbosity: int = 2) -> bool:
    """Run a specific test module"""
    try:
        # Import and run specific test
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_name)
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        return len(result.failures) == 0 and len(result.errors) == 0
    except Exception as e:
        print(f"Error running test {test_name}: {e}")
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are available"""
    print("Checking dependencies...")
    
    required_modules = [
        'utils.token_counter',
        'utils.text_utils', 
        'utils.file_utils',
        'processors.chunking_engine',
        'processors.concept_mapper'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            missing.append(module)
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Some tests may fail due to missing dependencies.")
        return False
    
    print("✅ All core dependencies available")
    return True


def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="Run tests for modular PDF converter")
    parser.add_argument(
        "--unit", action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration", action="store_true", 
        help="Run only integration tests"
    )
    parser.add_argument(
        "--test", type=str,
        help="Run specific test (e.g., tests.unit.test_token_counter)"
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=2,
        help="Increase verbosity (use -v, -vv, or -vvv)"
    )
    parser.add_argument(
        "--check-deps", action="store_true",
        help="Check dependencies before running tests"
    )
    parser.add_argument(
        "--no-summary", action="store_true",
        help="Skip test summary report"
    )
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_deps:
        deps_ok = check_dependencies()
        if not deps_ok:
            print("\\nWARNING: Some dependencies are missing!")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return 1
        print()
    
    # Create test runner
    runner = TestRunner(verbosity=args.verbose)
    
    # Run specific test
    if args.test:
        print(f"Running specific test: {args.test}")
        success = run_specific_test(args.test, args.verbose)
        return 0 if success else 1
    
    # Run tests based on arguments
    if args.unit:
        result = runner.run_unit_tests()
        success = len(result.failures) == 0 and len(result.errors) == 0
    elif args.integration:
        result = runner.run_integration_tests()
        success = len(result.failures) == 0 and len(result.errors) == 0
    else:
        # Run all tests
        results = runner.run_all_tests()
        if not args.no_summary:
            success = runner.print_summary(results)
        else:
            success = all(len(r[1].failures) == 0 and len(r[1].errors) == 0 for r in results)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)