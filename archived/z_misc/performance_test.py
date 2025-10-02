#!/usr/bin/env python3
"""
Performance Test for LangSwarm Debug Tracing System
Tests performance impact when debug=True vs debug=False
"""

import time
import statistics
from typing import List, Dict, Any
from langswarm.core.debug import enable_debug_tracing, disable_debug_tracing, get_debug_tracer

def test_function_calls(iterations: int = 1000) -> float:
    """Test performance of function calls that would be traced"""
    start_time = time.time()
    
    for i in range(iterations):
        # Simulate typical LangSwarm operations
        dummy_agent_call(f"Query {i}")
        dummy_tool_call("test_tool", {"param": i})
        dummy_config_load()
    
    return (time.time() - start_time) * 1000  # Return milliseconds

def dummy_agent_call(query: str):
    """Simulates an agent chat call"""
    tracer = get_debug_tracer()
    if tracer and tracer.enabled:
        with tracer.trace_operation("agent", "chat", f"Processing: {query}"):
            # Simulate work
            time.sleep(0.001)  # 1ms of "work"
            tracer.log_event("INFO", "agent", "response", f"Processed {query}")
    else:
        # Simulate work without tracing
        time.sleep(0.001)

def dummy_tool_call(tool_name: str, params: Dict[str, Any]):
    """Simulates a tool call"""
    tracer = get_debug_tracer()
    if tracer and tracer.enabled:
        tracer.log_event("INFO", "tool", "call", f"Calling {tool_name}", data=params)
    # Simulate tool work
    time.sleep(0.0005)

def dummy_config_load():
    """Simulates config loading"""
    tracer = get_debug_tracer()
    if tracer and tracer.enabled:
        with tracer.trace_operation("config", "load", "Loading config"):
            tracer.log_event("INFO", "config", "agents", "Loading agents")
            tracer.log_event("INFO", "config", "tools", "Loading tools")

def run_performance_test():
    """Run comprehensive performance test"""
    print("🚀 LangSwarm Debug Tracing Performance Test")
    print("=" * 60)
    
    iterations = 100
    runs = 5
    
    # Test 1: Debug DISABLED
    print(f"\n📊 Test 1: Debug DISABLED ({iterations} iterations, {runs} runs)")
    disable_debug_tracing()
    
    disabled_times = []
    for run in range(runs):
        duration = test_function_calls(iterations)
        disabled_times.append(duration)
        print(f"   Run {run+1}: {duration:.2f}ms")
    
    disabled_avg = statistics.mean(disabled_times)
    disabled_std = statistics.stdev(disabled_times) if len(disabled_times) > 1 else 0
    
    # Test 2: Debug ENABLED  
    print(f"\n📊 Test 2: Debug ENABLED ({iterations} iterations, {runs} runs)")
    enable_debug_tracing("/tmp/perf_test_debug.jsonl")
    
    enabled_times = []
    for run in range(runs):
        duration = test_function_calls(iterations)
        enabled_times.append(duration)
        print(f"   Run {run+1}: {duration:.2f}ms")
    
    enabled_avg = statistics.mean(enabled_times)
    enabled_std = statistics.stdev(enabled_times) if len(enabled_times) > 1 else 0
    
    # Analysis
    print("\n" + "=" * 60)
    print("📈 PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    print(f"Debug DISABLED:")
    print(f"  • Average: {disabled_avg:.2f}ms ± {disabled_std:.2f}ms")
    print(f"  • Per operation: {disabled_avg/iterations:.4f}ms")
    
    print(f"\nDebug ENABLED:")
    print(f"  • Average: {enabled_avg:.2f}ms ± {enabled_std:.2f}ms") 
    print(f"  • Per operation: {enabled_avg/iterations:.4f}ms")
    
    overhead = enabled_avg - disabled_avg
    overhead_percent = (overhead / disabled_avg) * 100 if disabled_avg > 0 else 0
    
    print(f"\n🎯 OVERHEAD ANALYSIS:")
    print(f"  • Absolute overhead: {overhead:.2f}ms")
    print(f"  • Percentage overhead: {overhead_percent:.1f}%")
    print(f"  • Per operation overhead: {overhead/iterations:.4f}ms")
    
    # Production recommendations
    print(f"\n💡 PRODUCTION RECOMMENDATIONS:")
    if overhead_percent < 5:
        print(f"  ✅ SAFE for production (< 5% overhead)")
    elif overhead_percent < 15:
        print(f"  ⚠️  CAUTION for production (5-15% overhead)")
    else:
        print(f"  ❌ NOT recommended for production (> 15% overhead)")
        
    print(f"\n📊 EARLY RETURN EFFICIENCY TEST:")
    # Test early return efficiency
    disable_debug_tracing()
    start = time.time()
    
    tracer = get_debug_tracer()
    for i in range(10000):
        if tracer and tracer.enabled:
            # This should never execute
            tracer.log_event("INFO", "test", "op", "message")
    
    early_return_time = (time.time() - start) * 1000
    print(f"  • 10,000 early returns: {early_return_time:.2f}ms")
    print(f"  • Per early return: {early_return_time/10000:.6f}ms")
    
    disable_debug_tracing()

if __name__ == "__main__":
    run_performance_test()
