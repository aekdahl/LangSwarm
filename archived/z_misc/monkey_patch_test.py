#!/usr/bin/env python3
"""
Test monkey patch overhead specifically
"""

import time
import statistics
from langswarm.core.debug import enable_debug_tracing, disable_debug_tracing

def test_monkey_patch_overhead():
    """Test the overhead of monkey-patched methods when debug=False"""
    print("🔍 Testing Monkey Patch Overhead When Debug=False")
    print("=" * 60)
    
    # Import after setup to test monkey patching
    from langswarm.core.wrappers.generic import AgentWrapper
    
    iterations = 1000
    
    # Test without monkey patching first (baseline)
    print("📊 Baseline: No Monkey Patching")
    
    # Create a simple mock agent for testing
    class MockAgent:
        def chat(self, query):
            time.sleep(0.001)  # Simulate work
            return f"Response to: {query}"
    
    mock_agent = MockAgent()
    
    # Baseline test
    baseline_times = []
    for run in range(3):
        start = time.time()
        for i in range(iterations):
            result = mock_agent.chat(f"Query {i}")
        baseline_time = (time.time() - start) * 1000
        baseline_times.append(baseline_time)
        print(f"   Run {run+1}: {baseline_time:.2f}ms")
    
    baseline_avg = statistics.mean(baseline_times)
    
    # Test with monkey patching but debug DISABLED
    print(f"\n📊 Monkey Patched (Debug DISABLED)")
    disable_debug_tracing()  # Ensure debug is off
    
    # Enable tracing (applies monkey patches) then disable
    enable_debug_tracing("/tmp/test.jsonl")
    disable_debug_tracing()
    
    # Now test the monkey-patched version with debug disabled
    patched_times = []
    for run in range(3):
        start = time.time()
        for i in range(iterations):
            # The method is now monkey-patched but should early return
            result = mock_agent.chat(f"Query {i}")
        patched_time = (time.time() - start) * 1000
        patched_times.append(patched_time)
        print(f"   Run {run+1}: {patched_time:.2f}ms")
    
    patched_avg = statistics.mean(patched_times)
    
    # Analysis
    overhead = patched_avg - baseline_avg
    overhead_percent = (overhead / baseline_avg) * 100 if baseline_avg > 0 else 0
    
    print(f"\n🎯 MONKEY PATCH OVERHEAD (debug=False):")
    print(f"  • Baseline average: {baseline_avg:.2f}ms")
    print(f"  • Patched average: {patched_avg:.2f}ms")
    print(f"  • Overhead: {overhead:.2f}ms ({overhead_percent:.1f}%)")
    print(f"  • Per-call overhead: {overhead/iterations:.6f}ms")
    
    if overhead_percent < 1:
        print(f"  ✅ Negligible overhead - safe for production")
    elif overhead_percent < 5:
        print(f"  ✅ Low overhead - acceptable for production")
    else:
        print(f"  ⚠️  Measurable overhead - consider impact")

if __name__ == "__main__":
    test_monkey_patch_overhead()
