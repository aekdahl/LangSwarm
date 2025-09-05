#!/usr/bin/env python3
"""
Full circle test with real API keys - run this if you have them
"""

import os
import tempfile
import yaml
import asyncio

async def test_full_circle():
    """Test complete workflow with real keys"""
    
    # Check if we have real keys
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    gcp_project = os.environ.get('GOOGLE_CLOUD_PROJECT', '')
    
    if not openai_key.startswith('sk-'):
        print("❌ Need real OPENAI_API_KEY (starts with sk-)")
        return False
        
    if not gcp_project:
        print("❌ Need GOOGLE_CLOUD_PROJECT set")
        return False
    
    print(f"🔑 Using OpenAI key: {openai_key[:10]}...")
    print(f"🔑 Using GCP project: {gcp_project}")
    
    config = {
        "version": "1.0",
        "agents": [{
            "id": "test_agent",
            "agent_type": "langchain-openai",
            "model": "gpt-4",
            "system_prompt": "Use the bigquery_search tool to answer questions.",
            "tools": ["bigquery_search"]
        }],
        "tools": [{
            "id": "bigquery_search", 
            "type": "mcpbigquery_vector_search",
            "config": {
                "project_id": gcp_project,
                "dataset_id": "vector_search",  # User's dataset
                "table_name": "embeddings",     # User's table
                "similarity_threshold": 0.3,
                "max_results": 5
            }
        }]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        
        print("\n1. 🔧 Loading configuration...")
        loader = LangSwarmConfigLoader(config_path)
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        agent = agents["test_agent"]
        
        print("2. 🤖 Getting tool instance...")
        tool = None
        if hasattr(agent.tool_registry, 'get_tool'):
            tool = agent.tool_registry.get_tool("bigquery_search")
        else:
            registry_dict = getattr(agent.tool_registry, 'tools', {})
            for tool_name, tool_obj in registry_dict.items():
                if "bigquery_search" in tool_name:
                    tool = tool_obj
                    break
        
        if not tool:
            print("❌ Could not get tool instance")
            return False
            
        print("3. 🔍 Testing real search...")
        test_queries = [
            "What is Pingday?",
            "fiber network services",
            {"query": "internet connectivity", "limit": 3}
        ]
        
        for query in test_queries:
            print(f"\n   Query: {query}")
            try:
                result = tool.run(query)
                
                if isinstance(result, dict):
                    if result.get("success"):
                        results = result.get("results", [])
                        print(f"   ✅ SUCCESS: Found {len(results)} results")
                        
                        # Show first result
                        if results:
                            first = results[0]
                            print(f"   📄 Sample: {first.get('content', '')[:100]}...")
                            
                    else:
                        error = result.get("error", "Unknown error")
                        print(f"   ❌ ERROR: {error[:200]}...")
                        
                        # Diagnose error type
                        if "authentication" in error.lower():
                            print("   💡 Try: gcloud auth application-default login")
                        elif "not found" in error.lower():
                            print("   💡 Check: BigQuery dataset/table exists")
                        elif "permission" in error.lower():
                            print("   💡 Check: BigQuery IAM permissions")
                            
            except Exception as e:
                print(f"   ❌ EXCEPTION: {e}")
                
        print("\n🎯 FULL CIRCLE TEST COMPLETE!")
        return True
        
    finally:
        os.unlink(config_path)

if __name__ == "__main__":
    asyncio.run(test_full_circle())
