#!/usr/bin/env python3
"""
LangSwarm End-to-End Test Runner

Intelligent test runner that automatically discovers and executes E2E tests
with real API integration, cloud resources, and comprehensive reporting.
"""

import asyncio
import json
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.e2e.framework.base import TestEnvironment, E2ETestSuite, test_environment
from tests.e2e.tests.orchestration_tests import (
    BasicOrchestrationTest, MultiProviderOrchestrationTest, 
    ParallelOrchestrationTest, ErrorRecoveryOrchestrationTest
)
from tests.e2e.tests.memory_tests import (
    SQLiteMemoryTest, ChromaDBMemoryTest, RedisMemoryTest, BigQueryMemoryTest
)
from tests.e2e.tests.integration_tests import (
    FullStackIntegrationTest, ErrorHandlingIntegrationTest
)


class E2ETestRunner:
    """Intelligent E2E test runner with auto-discovery and smart execution."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.test_classes = self._discover_tests()
        self.setup_logging()
    
    def setup_logging(self):
        """Set up comprehensive logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('e2e_test_run.log')
            ]
        )
        self.logger = logging.getLogger('e2e_runner')
    
    def _discover_tests(self) -> List[type]:
        """Auto-discover all E2E test classes."""
        return [
            # Orchestration tests
            BasicOrchestrationTest,
            MultiProviderOrchestrationTest,
            ParallelOrchestrationTest,
            ErrorRecoveryOrchestrationTest,
            
            # Memory tests
            SQLiteMemoryTest,
            ChromaDBMemoryTest,
            RedisMemoryTest,
            BigQueryMemoryTest,
            
            # Integration tests
            FullStackIntegrationTest,
            ErrorHandlingIntegrationTest,
        ]
    
    def filter_tests(self, 
                    category: Optional[str] = None,
                    providers: Optional[List[str]] = None,
                    max_cost: Optional[float] = None,
                    exclude_cloud: bool = False) -> List[type]:
        """Filter tests based on criteria."""
        filtered = []
        
        for test_class in self.test_classes:
            # Create dummy instance for inspection
            dummy_env = TestEnvironment()
            test_instance = test_class(dummy_env)
            
            # Category filter
            if category:
                test_name = test_instance.test_name.lower()
                if category.lower() not in test_name:
                    continue
            
            # Provider filter
            if providers:
                required = test_instance.required_providers
                if not any(p in providers for p in required):
                    continue
            
            # Cost filter
            if max_cost and test_instance.estimated_cost() > max_cost:
                continue
            
            # Cloud filter
            if exclude_cloud:
                required_resources = test_instance.required_resources
                cloud_resources = ["bigquery_dataset", "gcs_bucket", "aws_s3"]
                if any(r in cloud_resources for r in required_resources):
                    continue
            
            filtered.append(test_class)
        
        return filtered
    
    async def run_tests(self,
                       category: Optional[str] = None,
                       providers: Optional[List[str]] = None,
                       max_cost: Optional[float] = None,
                       exclude_cloud: bool = False,
                       parallel: bool = True,
                       dry_run: bool = False) -> Dict[str, Any]:
        """Run filtered E2E tests with comprehensive reporting."""
        
        print("🚀 LangSwarm End-to-End Test Runner")
        print("=" * 60)
        
        # Filter tests
        test_classes = self.filter_tests(category, providers, max_cost, exclude_cloud)
        
        if not test_classes:
            print("❌ No tests match the specified criteria")
            return {"error": "No matching tests"}
        
        print(f"📋 Found {len(test_classes)} tests to run")
        for test_class in test_classes:
            dummy_env = TestEnvironment()
            test = test_class(dummy_env)
            cost = test.estimated_cost()
            providers_req = ", ".join(test.required_providers) if test.required_providers else "None"
            print(f"  • {test.test_name} (${cost:.3f}, providers: {providers_req})")
        
        if dry_run:
            print("\n🔍 Dry run completed - no tests executed")
            return {"dry_run": True, "tests_found": len(test_classes)}
        
        # Estimate total cost
        total_cost = sum(test_class(TestEnvironment()).estimated_cost() for test_class in test_classes)
        print(f"\n💰 Estimated total cost: ${total_cost:.3f}")
        
        if total_cost > 1.0:  # $1 safety limit
            response = input(f"⚠️  High cost estimate (${total_cost:.3f}). Continue? [y/N]: ")
            if response.lower() != 'y':
                print("❌ Test run cancelled by user")
                return {"cancelled": True}
        
        # Run tests
        async with test_environment(self.config_path) as env:
            suite = E2ETestSuite(env)
            
            # Add tests to suite
            for test_class in test_classes:
                suite.add_test(test_class)
            
            print(f"\n🧪 Executing {len(test_classes)} tests...")
            print("-" * 60)
            
            start_time = time.time()
            results = await suite.run_all(parallel=parallel)
            end_time = time.time()
            
            suite.results = results
            
            # Generate report
            report = suite.generate_report()
            report["execution_time_s"] = end_time - start_time
            report["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Save detailed report
            self._save_report(report)
            
            # Print summary
            self._print_summary(report)
            
            return report
    
    def _save_report(self, report: Dict[str, Any]):
        """Save detailed test report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"e2e_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Detailed report saved to: {report_file}")
        print(f"📄 Detailed report: {report_file}")
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print test execution summary."""
        summary = report["summary"]
        performance = report["performance"]
        
        print("\n" + "=" * 60)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 60)
        
        # Results overview
        print(f"✅ Passed:  {summary['passed']:>3}")
        print(f"❌ Failed:  {summary['failed']:>3}")
        print(f"💥 Errors:  {summary['errors']:>3}")
        print(f"⏭️ Skipped: {summary['skipped']:>3}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        
        print("\n" + "-" * 40)
        
        # Performance metrics
        print(f"⏱️  Total Time:   {performance['total_duration_s']:.1f}s")
        print(f"💰 Total Cost:   ${performance['total_cost_usd']:.3f}")
        print(f"🎯 Total Tokens: {performance['total_tokens']:,}")
        print(f"⚡ Avg Duration: {performance['avg_duration_s']:.1f}s")
        
        # Status indicators
        if summary['success_rate'] >= 90:
            print("\n🎉 Excellent! LangSwarm is working great!")
        elif summary['success_rate'] >= 70:
            print("\n✅ Good! Most features are working correctly")
        elif summary['success_rate'] >= 50:
            print("\n⚠️  Warning: Some issues detected")
        else:
            print("\n🚨 Critical: Multiple failures detected")
        
        # Recommendations
        if summary['failed'] > 0 or summary['errors'] > 0:
            print("\n🔧 RECOMMENDATIONS:")
            
            failed_tests = [t for t in report["tests"] if t["status"] in ["FAIL", "ERROR"]]
            
            # Common failure patterns
            api_failures = [t for t in failed_tests if "api" in t.get("error", "").lower()]
            if api_failures:
                print("  • Check API keys and network connectivity")
            
            config_failures = [t for t in failed_tests if "config" in t.get("error", "").lower()]
            if config_failures:
                print("  • Verify configuration files and settings")
            
            memory_failures = [t for t in failed_tests if any(backend in t.get("test_name", "").lower() 
                                                            for backend in ["redis", "bigquery", "chroma"])]
            if memory_failures:
                print("  • Check database/memory backend connectivity")
            
            print("  • Review detailed logs in e2e_test_run.log")
            print("  • Check individual test artifacts in test_artifacts/")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LangSwarm End-to-End Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py                           # Run all tests
  python runner.py --category orchestration # Run orchestration tests only  
  python runner.py --providers openai       # Run tests requiring only OpenAI
  python runner.py --max-cost 0.50          # Limit cost to $0.50
  python runner.py --exclude-cloud          # Skip cloud resource tests
  python runner.py --dry-run                # Preview without executing
  python runner.py --sequential             # Run tests one by one
        """
    )
    
    parser.add_argument("--category", 
                       help="Filter tests by category (orchestration, memory, integration)")
    parser.add_argument("--providers", nargs="+",
                       help="Required providers (openai, anthropic, google, cohere)")
    parser.add_argument("--max-cost", type=float,
                       help="Maximum total cost in USD")
    parser.add_argument("--exclude-cloud", action="store_true",
                       help="Exclude tests requiring cloud resources")
    parser.add_argument("--sequential", action="store_true",
                       help="Run tests sequentially instead of in parallel")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show which tests would run without executing them")
    parser.add_argument("--config",
                       help="Path to test configuration file")
    
    args = parser.parse_args()
    
    # Create runner
    runner = E2ETestRunner(args.config)
    
    # Run tests
    try:
        report = asyncio.run(runner.run_tests(
            category=args.category,
            providers=args.providers,
            max_cost=args.max_cost,
            exclude_cloud=args.exclude_cloud,
            parallel=not args.sequential,
            dry_run=args.dry_run
        ))
        
        # Exit with appropriate code
        if report.get("dry_run") or report.get("cancelled"):
            sys.exit(0)
        elif "error" in report:
            sys.exit(1)
        else:
            summary = report.get("summary", {})
            failed = summary.get("failed", 0) + summary.get("errors", 0)
            sys.exit(1 if failed > 0 else 0)
            
    except KeyboardInterrupt:
        print("\n❌ Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()