#!/usr/bin/env python3
"""
Test to reproduce the user's similarity_threshold issue
"""

import asyncio
import sys
sys.path.insert(0, '.')

async def test_user_scenarios():
    print("🔍 Testing various user scenarios for similarity_threshold...")
    
    # Scenario 1: Direct tool usage (what user might be doing)
    print("\n📋 Scenario 1: Direct BigQuery tool usage")
    from langswarm.mcp.tools.bigquery_vector_search.main import similarity_search, SimilaritySearchInput
    
    # Test without any config (should use DEFAULT_CONFIG)
    result1 = await similarity_search(SimilaritySearchInput(query="test", limit=3))
    print(f"   No config passed - Results: {len(result1.results)}")
    
    # Test with empty config (should also use DEFAULT_CONFIG)  
    result2 = await similarity_search(SimilaritySearchInput(query="test", limit=3), config={})
    print(f"   Empty config passed - Results: {len(result2.results)}")
    
    # Test with explicit threshold
    result3 = await similarity_search(SimilaritySearchInput(query="test", limit=3, similarity_threshold=0.5))
    print(f"   Explicit threshold 0.5 - Results: {len(result3.results)}")
    
    # Scenario 2: Through agent workflow (what should work)
    print("\n📋 Scenario 2: Through configured agent workflow")
    from langswarm.core.config import LangSwarmConfigLoader
    
    loader = LangSwarmConfigLoader('langswarm/core/debug/test_configs/bigquery_debug.yaml')
    workflows, agents, brokers, tools, metadata = loader.load()
    
    agent = agents.get('bigquery_test_agent')
    if agent:
        try:
            response = agent.chat('Search for "test" with similarity_search, limit 3 results')
            print(f"   Agent workflow - Response length: {len(str(response))}")
            if "similarity" in str(response).lower():
                print("   ✅ Agent workflow returned results")
            else:
                print("   ⚠️  Agent workflow may not have returned results")
        except Exception as e:
            print(f"   ❌ Agent workflow failed: {e}")
    
    print("\n✅ All scenarios tested")

if __name__ == "__main__":
   
    asyncio.run(test_user_scenarios())
