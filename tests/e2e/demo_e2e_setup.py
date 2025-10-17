#!/usr/bin/env python3
"""
LangSwarm E2E Setup Demo

Quick demonstration of the E2E testing framework setup and basic test execution.
This script shows how to use the framework without requiring full cloud setup.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the framework to path
sys.path.insert(0, str(Path(__file__).parent))

async def demo_basic_setup():
    """Demonstrate basic E2E framework setup."""
    print("🚀 LangSwarm E2E Framework Demo")
    print("=" * 40)
    
    try:
        # Import framework components
        from framework.base import TestEnvironment, E2ETestSuite
        from tests.memory_tests import SQLiteMemoryTest
        
        print("✅ Framework imports successful")
        
        # Create test environment
        print("\n🔧 Setting up test environment...")
        env = TestEnvironment()
        
        # Check basic requirements
        api_keys_available = any([
            env.get_api_key("openai"),
            env.get_api_key("anthropic")
        ])
        
        print(f"📋 Environment check:")
        print(f"   API Keys: {'✅ Available' if api_keys_available else '❌ Missing'}")
        print(f"   Config: ✅ Loaded")
        
        # Create test suite
        print("\n🧪 Creating test suite...")
        suite = E2ETestSuite(env)
        
        # Add a basic test (SQLite doesn't require external services)
        suite.add_test(SQLiteMemoryTest)
        print("   ✅ Added SQLite memory test")
        
        # Show what would run
        print("\n📊 Test suite contents:")
        for i, test in enumerate(suite.tests, 1):
            cost = test.estimated_cost()
            providers = ", ".join(test.required_providers) or "None"
            resources = ", ".join(test.required_resources) or "None"
            
            skip_reason = test.should_skip()
            status = "🟡 SKIP" if skip_reason else "🟢 READY"
            
            print(f"   {i}. {test.test_name}")
            print(f"      Status: {status}")
            print(f"      Cost: ${cost:.3f}")
            print(f"      Providers: {providers}")
            print(f"      Resources: {resources}")
            
            if skip_reason:
                print(f"      Skip reason: {skip_reason}")
        
        # Run a basic test if possible
        if not suite.tests[0].should_skip():
            print("\n🏃 Running basic test...")
            
            try:
                result = await suite.tests[0].execute()
                
                print(f"   Test: {result.test_name}")
                print(f"   Status: {result.status}")
                print(f"   Duration: {result.metrics.duration_ms/1000:.2f}s")
                print(f"   Cost: ${result.metrics.cost_estimate:.4f}")
                
                if result.status == "PASS":
                    print("   🎉 Test passed!")
                else:
                    print(f"   ❌ Test failed: {result.metrics.errors}")
                    
            except Exception as e:
                print(f"   ❌ Test execution failed: {e}")
        else:
            print("\n⏭️  Skipping test execution (requirements not met)")
        
        print("\n📋 Next steps:")
        if not api_keys_available:
            print("   1. Set API keys: export OPENAI_API_KEY='your-key'")
        print("   2. Run setup: ./quick_setup.sh")
        print("   3. Run tests: make test-basic")
        print("   4. View results: make show-results")
        
        # Cleanup
        await env.cleanup()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Fix:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Ensure you're in the tests/e2e directory")
        return False
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

def show_framework_overview():
    """Show overview of the E2E framework."""
    print("\n📚 Framework Overview")
    print("=" * 40)
    
    framework_info = {
        "🏗️ Base Framework": [
            "TestEnvironment - Resource management",
            "BaseE2ETest - Abstract test class", 
            "E2ETestSuite - Test orchestration",
            "TestMetrics - Performance tracking"
        ],
        "🧪 Test Categories": [
            "Orchestration - Multi-agent workflows",
            "Memory - Backend storage systems",
            "Integration - Full stack testing"
        ],
        "☁️ Cloud Resources": [
            "BigQuery - Vector search at scale",
            "Redis - Caching and search",
            "ChromaDB - Vector database",
            "GCP - Service accounts and auth"
        ],
        "🔍 Monitoring": [
            "SystemMonitor - Real-time metrics",
            "TestDatabase - Historical analysis",
            "RealTimeDebugger - Alert system",
            "Artifact storage - Logs and results"
        ]
    }
    
    for category, items in framework_info.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  • {item}")

def main():
    """Main demo function."""
    try:
        # Show framework overview
        show_framework_overview()
        
        # Run basic setup demo
        success = asyncio.run(demo_basic_setup())
        
        if success:
            print("\n🎯 Demo completed successfully!")
            print("The E2E framework is ready for use.")
        else:
            print("\n⚠️  Demo encountered issues.")
            print("Check the error messages above for troubleshooting.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()