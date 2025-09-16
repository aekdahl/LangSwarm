#!/usr/bin/env python3
"""
Test the helpful guidance system for invalid tool method calls
"""

import asyncio
import sys
sys.path.insert(0, '.')

async def test_invalid_method_guidance():
    print("🧪 Testing helpful guidance for invalid method calls...")
    
    from langswarm.core.config import LangSwarmConfigLoader
    
    # Load the BigQuery tool
    loader = LangSwarmConfigLoader('langswarm/core/debug/test_configs/bigquery_debug.yaml')
    workflows, agents, brokers, tools, metadata = loader.load()
    
    # Find the BigQuery tool
    bigquery_tool = None
    for tool in tools:
        if getattr(tool, 'identifier', None) == 'bigquery_search':
            bigquery_tool = tool
            break
    
    if not bigquery_tool:
        print("❌ BigQuery tool not found")
        return False
    
    # Test invalid method calls
    test_cases = [
        "dataset_info",
        "search", 
        "find_documents",
        "get_data",
        "invalid_method"
    ]
    
    print(f"\n📋 Testing {len(test_cases)} invalid method calls...")
    
    for invalid_method in test_cases:
        print(f"\n🔍 Testing invalid method: '{invalid_method}'")
        
        try:
            # Try to call the invalid method
            result = bigquery_tool.server.call_task(invalid_method, {})
            
            # Check if we got helpful guidance
            if isinstance(result, dict):
                if result.get("success") is False and "guidance" in result:
                    print(f"✅ Got helpful guidance!")
                    print(f"   Error: {result.get('error')}")
                    print(f"   Guidance: {result.get('guidance')}")
                    if result.get('specific_suggestion'):
                        print(f"   Suggestion: {result.get('specific_suggestion')}")
                    print(f"   Available methods: {result.get('available_methods')}")
                else:
                    print(f"⚠️  Got response but no guidance: {result}")
            else:
                print(f"❌ Unexpected response type: {type(result)}")
                
        except Exception as e:
            print(f"❌ Exception occurred: {e}")
    
    print(f"\n✅ Guidance testing completed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_invalid_method_guidance())
