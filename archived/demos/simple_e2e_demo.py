#!/usr/bin/env python3
"""
Simple E2E Framework Demo

Basic demonstration of the testing framework without complex dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path  
sys.path.insert(0, str(Path(__file__).parent))

from tests.e2e.framework.base import BaseE2ETest, TestEnvironment, test_environment


class SimpleTest(BaseE2ETest):
    """Simple test that doesn't require external dependencies."""
    
    @property
    def test_name(self) -> str:
        return "Simple Framework Test"
    
    @property
    def required_providers(self) -> list:
        return []
    
    @property
    def required_resources(self) -> list:
        return []
    
    def estimated_cost(self) -> float:
        return 0.0
    
    async def run_test(self) -> dict:
        """Run a simple test."""
        self.logger.info("Running simple test")
        
        # Simulate some work
        await asyncio.sleep(0.1)
        
        # Save test artifact
        self.save_artifact("test_output", "This is a test output")
        
        return {
            "success": True,
            "test_type": "simple",
            "framework_working": True,
            "artifacts_created": True
        }
    
    async def validate_result(self, result: dict) -> bool:
        """Validate the test result."""
        return result.get("success", False) and result.get("framework_working", False)


async def demo_simple_test():
    """Demo the basic framework functionality."""
    
    print("🚀 Simple E2E Framework Demo")
    print("=" * 40)
    
    try:
        async with test_environment() as env:
            
            # Create and run a simple test
            test = SimpleTest(env)
            
            print(f"📋 Test: {test.test_name}")
            print(f"💰 Cost: ${test.estimated_cost():.3f}")
            print(f"🆔 Test ID: {test.test_id}")
            
            # Execute test
            print("\n🧪 Executing test...")
            result = await test.execute()
            
            # Display results
            print(f"\n📊 Result: {result.status}")
            print(f"⏱️  Duration: {result.metrics.duration_ms:.0f}ms")
            print(f"🔍 Details: {len(result.details)} items")
            
            if result.artifacts:
                print(f"📄 Artifacts: {list(result.artifacts.keys())}")
            
            if result.status == "PASS":
                print("✅ Test passed successfully!")
            else:
                print(f"❌ Test failed: {result.details}")
            
            # Show framework capabilities
            print(f"\n🔧 Framework Features Demonstrated:")
            print(f"  • Test execution lifecycle")
            print(f"  • Metrics collection") 
            print(f"  • Artifact storage")
            print(f"  • Error handling")
            print(f"  • Logging integration")
            
            return result.status == "PASS"
            
    except Exception as e:
        print(f"💥 Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def demo_test_discovery():
    """Demo test discovery and filtering."""
    
    print("\n🔍 Test Discovery Demo")
    print("-" * 30)
    
    try:
        from tests.e2e.runner import E2ETestRunner
        
        runner = E2ETestRunner()
        
        print(f"📋 Found {len(runner.test_classes)} test classes:")
        
        # Create dummy environment for inspection
        async with test_environment() as env:
            for i, test_class in enumerate(runner.test_classes[:5], 1):  # Show first 5
                try:
                    test = test_class(env)
                    print(f"  {i}. {test.test_name}")
                    print(f"     Providers: {test.required_providers or 'None'}")
                    print(f"     Resources: {test.required_resources or 'None'}")
                    print(f"     Cost: ${test.estimated_cost():.3f}")
                except Exception as e:
                    print(f"  {i}. {test_class.__name__} (Error: {e})")
        
        # Demo filtering
        print(f"\n🔧 Filtering capabilities:")
        
        free_tests = runner.filter_tests(max_cost=0.0)
        print(f"  • Free tests: {len(free_tests)}")
        
        local_tests = runner.filter_tests(exclude_cloud=True)
        print(f"  • Local tests: {len(local_tests)}")
        
        return True
        
    except Exception as e:
        print(f"Discovery demo failed: {e}")
        return False


def main():
    """Main demo function."""
    
    try:
        print("🎯 Starting E2E Framework Demo\n")
        
        # Run simple test demo
        test_success = asyncio.run(demo_simple_test())
        
        # Run discovery demo
        discovery_success = asyncio.run(demo_test_discovery())
        
        print(f"\n🎉 Demo Results:")
        print(f"  • Simple test: {'✅ PASS' if test_success else '❌ FAIL'}")
        print(f"  • Discovery: {'✅ PASS' if discovery_success else '❌ FAIL'}")
        
        if test_success and discovery_success:
            print(f"\n🚀 E2E Framework is working correctly!")
            print(f"\n💡 Next steps:")
            print(f"  • Set OPENAI_API_KEY for API integration tests")
            print(f"  • Run: python tests/e2e/runner.py --dry-run")
            print(f"  • Explore test artifacts in test_artifacts/")
            return 0
        else:
            print(f"\n⚠️  Some issues detected in framework")
            return 1
            
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())