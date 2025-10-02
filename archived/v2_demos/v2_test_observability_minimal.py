#!/usr/bin/env python3
"""
Minimal test for V2 observability system
"""

import asyncio
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.abspath('.'))

async def main():
    try:
        print("Testing V2 Observability System...")
        
        # Test basic imports
        from langswarm.v2.core.observability import (
            ObservabilityProvider, create_development_observability
        )
        print("✅ Basic imports successful")
        
        # Test provider creation
        provider = create_development_observability()
        print("✅ Provider created")
        
        # Test provider start
        await provider.start()
        print("✅ Provider started")
        
        # Test basic logging
        provider.logger.info("Test message", "test")
        print("✅ Logging works")
        
        # Test basic tracing
        with provider.tracer.start_span("test_operation") as span:
            if span:
                print(f"✅ Tracing works - span: {span.span_id}")
            else:
                print("⚠️ Tracing created no span (sampling?)")
        
        # Test basic metrics
        provider.metrics.increment_counter("test.counter", 1.0)
        print("✅ Metrics work")
        
        # Test provider stop
        await provider.stop()
        print("✅ Provider stopped")
        
        print("\n🎉 All basic observability tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
