#!/usr/bin/env python3
"""
Demo of LangSwarm End-to-End Testing Framework

Shows how to run comprehensive E2E tests with real API integration,
monitoring, and debugging capabilities.
"""

import asyncio
import os
from tests.e2e.framework.base import test_environment, E2ETestSuite
from tests.e2e.tests.orchestration_tests import BasicOrchestrationTest
from tests.e2e.tests.memory_tests import SQLiteMemoryTest
from tests.e2e.debug.monitor import monitoring_context


async def demo_e2e_framework():
    """Demonstrate the E2E testing framework capabilities."""
    
    print("🚀 LangSwarm E2E Testing Framework Demo")
    print("=" * 50)
    
    # Check if we have API keys for real testing
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if not has_openai:
        print("⚠️  No OPENAI_API_KEY found")
        print("   Set it to test with real APIs:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("\n   Continuing with local tests only...\n")
    
    # Start monitoring context
    async with monitoring_context(monitor_interval=2.0) as monitoring:
        async with test_environment() as env:
            
            # Create test suite
            suite = E2ETestSuite(env)
            
            # Add tests based on available resources
            print("📋 Setting up test suite...")
            
            # Always add local tests
            suite.add_test(SQLiteMemoryTest)
            print("  ✅ Added SQLite memory test")
            
            # Add API tests if keys available
            if has_openai:
                suite.add_test(BasicOrchestrationTest)
                print("  ✅ Added orchestration test (real API)")
            else:
                print("  ⏭️  Skipped orchestration test (no API key)")
            
            # Run tests with monitoring
            print(f"\n🧪 Executing {len(suite.tests)} tests with monitoring...")
            print("-" * 50)
            
            results = await suite.run_all(parallel=False)  # Sequential for demo
            
            # Generate and display report
            report = suite.generate_report()
            
            print("\n📊 TEST RESULTS")
            print("-" * 30)
            
            summary = report["summary"]
            performance = report["performance"]
            
            print(f"✅ Passed:  {summary['passed']}")
            print(f"❌ Failed:  {summary['failed']}")
            print(f"💥 Errors:  {summary['errors']}")
            print(f"⏭️ Skipped: {summary['skipped']}")
            print(f"📈 Success: {summary['success_rate']:.1f}%")
            
            print(f"\n⏱️  Duration: {performance['total_duration_s']:.1f}s")
            print(f"💰 Cost:     ${performance['total_cost_usd']:.4f}")
            print(f"🎯 Tokens:   {performance['total_tokens']}")
            
            # Show monitoring summary
            monitor_summary = monitoring["monitor"].get_summary()
            if "error" not in monitor_summary:
                print(f"\n🖥️  SYSTEM MONITORING")
                print(f"CPU Peak:    {monitor_summary['cpu']['max']:.1f}%")
                print(f"Memory Peak: {monitor_summary['memory']['max']:.1f}%")
                print(f"Samples:     {monitor_summary['sample_count']}")
            
            # Show any alerts
            debugger = monitoring["debugger"]
            alerts = debugger.get_active_alerts(10)  # Last 10 minutes
            
            if alerts:
                print(f"\n🚨 ALERTS ({len(alerts)})")
                for alert in alerts[-3:]:  # Show last 3
                    print(f"   • {alert['message']}")
            else:
                print("\n✅ No system alerts detected")
            
            # Test details
            print(f"\n📝 TEST DETAILS")
            for test_result in report["tests"]:
                status_emoji = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "ERROR": "💥"}
                emoji = status_emoji.get(test_result["status"], "❓")
                
                duration = test_result["duration_ms"] / 1000
                cost = test_result["cost_estimate"]
                
                print(f"{emoji} {test_result['test_name']}")
                print(f"     Duration: {duration:.1f}s, Cost: ${cost:.4f}")
                
                if test_result["status"] in ["FAIL", "ERROR"] and test_result.get("errors"):
                    print(f"     Error: {test_result['errors'][0][:60]}...")
            
            return report


async def demo_test_filtering():
    """Demonstrate test filtering capabilities."""
    
    print("\n🔍 Test Filtering Demo")
    print("-" * 30)
    
    from tests.e2e.runner import E2ETestRunner
    
    runner = E2ETestRunner()
    
    # Show all available tests
    print("📋 All available tests:")
    for i, test_class in enumerate(runner.test_classes, 1):
        dummy_env = test_environment()
        async with dummy_env as env:
            test = test_class(env)
            providers = ", ".join(test.required_providers) if test.required_providers else "None"
            cost = test.estimated_cost()
            print(f"  {i}. {test.test_name}")
            print(f"     Providers: {providers}")
            print(f"     Cost: ${cost:.3f}")
    
    # Demo filtering
    print("\n🔧 Filtering examples:")
    
    # Filter by cost
    low_cost_tests = runner.filter_tests(max_cost=0.01)
    print(f"  Low cost tests (≤$0.01): {len(low_cost_tests)}")
    
    # Filter by provider
    openai_tests = runner.filter_tests(providers=["openai"])
    print(f"  OpenAI tests: {len(openai_tests)}")
    
    # Filter by category
    memory_tests = runner.filter_tests(category="memory")
    print(f"  Memory tests: {len(memory_tests)}")
    
    # Exclude cloud
    local_tests = runner.filter_tests(exclude_cloud=True)
    print(f"  Local tests (no cloud): {len(local_tests)}")


def main():
    """Main demo function."""
    try:
        print("🎯 Running E2E framework demo...\n")
        
        # Run main demo
        report = asyncio.run(demo_e2e_framework())
        
        # Run filtering demo
        asyncio.run(demo_test_filtering())
        
        print("\n🎉 Demo completed successfully!")
        print("\n💡 Next steps:")
        print("  • Run full test suite: python tests/e2e/runner.py")
        print("  • Filter tests: python tests/e2e/runner.py --category memory")
        print("  • Set API keys for full testing")
        print("  • Check test artifacts in test_artifacts/")
        print("  • Review monitoring logs in e2e_test_run.log")
        
        # Exit with appropriate code
        if report and report.get("summary"):
            failed = report["summary"].get("failed", 0) + report["summary"].get("errors", 0)
            return 0 if failed == 0 else 1
        
        return 0
        
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())