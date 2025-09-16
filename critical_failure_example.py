#!/usr/bin/env python3
"""
LangSwarm Critical Failure Handling Example

This example demonstrates how the debug system now detects and handles
critical failures that should halt execution immediately, preventing
cascading errors and providing clear diagnostic information.

Key features demonstrated:
1. Detection of critical failures (API keys, model issues, etc.)
2. Early termination when critical failures occur
3. Clear error messages with actionable suggestions
4. Distinction between critical and recoverable errors
"""

import asyncio
import os
from pathlib import Path

# Import LangSwarm debug system with critical failure handling
from langswarm.core.debug import (
    enable_debug_tracing,
    run_case_1,
    run_all_basic_cases,
    handle_critical_failure,
    is_critical_error,
    initialize_failure_handler,
    get_failure_handler
)


async def example_1_critical_failure_detection():
    """Example 1: Demonstrate critical failure detection"""
    print("🔧 Example 1: Critical Failure Detection")
    print("=" * 50)
    
    # Enable debug tracing
    enable_debug_tracing("critical_failure_demo.jsonl")
    
    # Initialize failure handler
    failure_handler = initialize_failure_handler()
    
    print("Testing different types of failures:\n")
    
    # Test 1: API Key Missing (Critical)
    error_msg = "API key for openai not found. Set OPENAI_API_KEY or pass the key explicitly."
    is_critical = is_critical_error(error_msg)
    should_continue = handle_critical_failure(error_msg, ValueError(error_msg), "openai")
    
    print(f"1. API Key Missing:")
    print(f"   Error: {error_msg}")
    print(f"   Critical: {'✅ YES' if is_critical else '❌ No'}")
    print(f"   Should continue: {'✅ YES' if should_continue else '❌ No'}")
    print()
    
    # Test 2: Network timeout (Critical)
    error_msg = "Connection timeout connecting to api.openai.com"
    is_critical = is_critical_error(error_msg)
    should_continue = handle_critical_failure(error_msg, ConnectionError(error_msg), "openai")
    
    print(f"2. Network Timeout:")
    print(f"   Error: {error_msg}")
    print(f"   Critical: {'✅ YES' if is_critical else '❌ No'}")
    print(f"   Should continue: {'✅ YES' if should_continue else '❌ No'}")
    print()
    
    # Test 3: Generic error (Recoverable)
    error_msg = "Temporary processing error, please try again"
    is_critical = is_critical_error(error_msg)
    should_continue = handle_critical_failure(error_msg, RuntimeError(error_msg), "agent")
    
    print(f"3. Generic Error:")
    print(f"   Error: {error_msg}")
    print(f"   Critical: {'✅ YES' if is_critical else '❌ No'}")
    print(f"   Should continue: {'✅ YES' if should_continue else '❌ No'}")
    print()
    
    # Show failure summary
    if failure_handler.has_critical_failures():
        summary = failure_handler.get_failure_summary()
        print(f"📊 Critical Failures Summary:")
        print(f"   Count: {summary['count']}")
        print(f"   Categories: {list(summary['categories'].keys())}")
        print(f"   First failure: {summary['first_failure']['component']} - {summary['first_failure']['category']}")


async def example_2_test_case_with_critical_failure():
    """Example 2: Run test case that will encounter critical failure"""
    print("\n🔧 Example 2: Test Case with Critical Failure")
    print("=" * 50)
    
    # Ensure no API key is set for this demo
    original_api_key = os.environ.get('OPENAI_API_KEY')
    if original_api_key:
        os.environ.pop('OPENAI_API_KEY', None)
        print("🔒 Temporarily removed OPENAI_API_KEY for demo purposes")
    
    try:
        # Run test case - should detect critical failure and halt
        print("🧪 Running Case 1 without API key (should detect critical failure):")
        result = await run_case_1()
        
        print(f"\n📊 Test Result:")
        print(f"   Success: {'✅' if result.success else '❌'} {result.success}")
        print(f"   Duration: {result.duration_ms:.1f}ms")
        print(f"   Events: {result.events_count}")
        
        if result.error_message:
            if "CRITICAL FAILURE" in result.error_message:
                print(f"   🚨 Critical Failure Detected: {result.error_message}")
                print(f"   ✅ System correctly halted execution")
            else:
                print(f"   Error: {result.error_message}")
    
    finally:
        # Restore API key if it was set
        if original_api_key:
            os.environ['OPENAI_API_KEY'] = original_api_key
            print("🔓 Restored OPENAI_API_KEY")


async def example_3_early_termination_in_test_suite():
    """Example 3: Demonstrate early termination in test suite"""
    print("\n🔧 Example 3: Early Termination in Test Suite")
    print("=" * 50)
    
    # Ensure no API key is set
    original_api_key = os.environ.get('OPENAI_API_KEY')
    if original_api_key:
        os.environ.pop('OPENAI_API_KEY', None)
        print("🔒 Temporarily removed OPENAI_API_KEY for demo")
    
    try:
        print("🚀 Running full test suite (should stop at first critical failure):")
        results = await run_all_basic_cases()
        
        print(f"\n📊 Test Suite Results:")
        for i, result in enumerate(results, 1):
            status = "✅ PASS" if result.success else "❌ FAIL"
            critical = "🚨 CRITICAL" if result.error_message and "CRITICAL FAILURE" in result.error_message else ""
            print(f"   Test {i}: {status} {result.case_name} {critical}")
        
        print(f"\n🎯 Expected behavior:")
        print(f"   - Test 1 should fail with critical failure (missing API key)")
        print(f"   - Remaining tests should be skipped to prevent cascading failures")
        print(f"   - User gets clear diagnostic information")
    
    finally:
        if original_api_key:
            os.environ['OPENAI_API_KEY'] = original_api_key
            print("🔓 Restored OPENAI_API_KEY")


async def example_4_with_valid_api_key():
    """Example 4: Show normal operation with valid API key"""
    print("\n🔧 Example 4: Normal Operation (if API key available)")
    print("=" * 50)
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  No OPENAI_API_KEY found - skipping this example")
        print("💡 Set OPENAI_API_KEY to see normal operation without critical failures")
        return
    
    print("🔑 OPENAI_API_KEY detected - running with real API")
    print("🧪 Running Case 1 with valid API key:")
    
    result = await run_case_1()
    
    print(f"\n📊 Test Result:")
    print(f"   Success: {'✅' if result.success else '❌'} {result.success}")
    print(f"   Duration: {result.duration_ms:.1f}ms")
    print(f"   Events: {result.events_count}")
    
    if result.error_message:
        if "CRITICAL FAILURE" in result.error_message:
            print(f"   🚨 Unexpected critical failure: {result.error_message}")
        else:
            print(f"   ⚠️  Non-critical error: {result.error_message}")
    else:
        print(f"   ✅ Test completed successfully with real API")


def show_critical_failure_examples():
    """Show examples of different critical failure patterns"""
    print("\n📚 Critical Failure Patterns")
    print("=" * 50)
    
    patterns = [
        ("Missing API Key", "API key for openai not found. Set OPENAI_API_KEY environment variable."),
        ("Invalid API Key", "Authentication failed: invalid API key provided"),
        ("Model Not Found", "Model 'gpt-5-ultra' not found or unavailable"),
        ("Network Issues", "Connection timeout connecting to api.openai.com"),
        ("Configuration Error", "Missing required parameter 'model' in agent configuration"),
        ("General Error", "Temporary processing error - this would be recoverable")
    ]
    
    print("Examples of error messages and their classification:\n")
    
    for name, error_msg in patterns:
        is_critical = is_critical_error(error_msg)
        status = "🚨 CRITICAL" if is_critical else "⚠️  RECOVERABLE"
        print(f"{status} {name}:")
        print(f"   Message: {error_msg}")
        print(f"   Action: {'Halt execution' if is_critical else 'Log and continue'}")
        print()


async def main():
    """Run all critical failure examples"""
    print("🎯 LangSwarm Critical Failure Handling Examples")
    print("=" * 60)
    print("This demonstrates how the debug system now detects critical failures")
    print("and halts execution to prevent cascading errors.\n")
    
    # Run examples
    await example_1_critical_failure_detection()
    await example_2_test_case_with_critical_failure()
    await example_3_early_termination_in_test_suite()
    await example_4_with_valid_api_key()
    
    show_critical_failure_examples()
    
    print("\n🎉 Critical Failure Examples Completed!")
    print("\n📋 Key Benefits:")
    print("   ✅ Early detection of critical issues (API keys, models, network)")
    print("   ✅ Clear diagnostic messages with actionable suggestions")
    print("   ✅ Prevents cascading failures in test suites")
    print("   ✅ Distinguishes critical from recoverable errors")
    print("   ✅ Structured logging of failure context")
    
    print("\n💡 Next Steps:")
    print("   1. Set required API keys (OPENAI_API_KEY, etc.)")
    print("   2. Run test cases to verify functionality")
    print("   3. Check debug logs for detailed failure analysis")
    print("   4. Integrate critical failure handling in your own code")


if __name__ == "__main__":
    asyncio.run(main())
