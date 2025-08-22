#!/usr/bin/env python3
"""
BigQuery Memory Backend Setup Test
==================================

This script helps you test and verify your BigQuery memory backend setup for LangSwarm.

Usage:
    python test_bigquery_setup.py

Environment Variables Required:
    GOOGLE_APPLICATION_CREDENTIALS - Path to service account JSON file
    GOOGLE_CLOUD_PROJECT - Your Google Cloud project ID
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add current directory to path to import LangSwarm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def check_environment() -> bool:
    """Check if environment variables are properly set"""
    print_section("Environment Variables Check")
    
    required_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_PROJECT"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nTo fix this, run:")
        print("export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account.json'")
        print("export GOOGLE_CLOUD_PROJECT='your-project-id'")
        return False
    
    # Check if credentials file exists
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return False
    
    print("✅ All environment variables configured correctly")
    return True

def test_bigquery_import() -> bool:
    """Test if BigQuery client can be imported"""
    print_section("BigQuery Client Import Test")
    
    try:
        from google.cloud import bigquery
        print("✅ google-cloud-bigquery library installed")
        return True
    except ImportError as e:
        print(f"❌ BigQuery library not installed: {e}")
        print("\nTo fix this, run:")
        print("pip install google-cloud-bigquery")
        return False

def test_bigquery_connection() -> bool:
    """Test BigQuery connection and permissions"""
    print_section("BigQuery Connection Test")
    
    try:
        from google.cloud import bigquery
        
        # Create client
        client = bigquery.Client()
        print(f"✅ BigQuery client created for project: {client.project}")
        
        # Test basic query
        query = "SELECT 1 as test, CURRENT_TIMESTAMP() as timestamp"
        result = client.query(query).result()
        
        for row in result:
            print(f"✅ Connection test successful: {row.test}, {row.timestamp}")
            break
        
        return True
        
    except Exception as e:
        print(f"❌ BigQuery connection failed: {e}")
        print("\nCommon fixes:")
        print("1. Check your service account has BigQuery permissions")
        print("2. Enable BigQuery API: gcloud services enable bigquery.googleapis.com")
        print("3. Verify your project ID is correct")
        return False

def test_memory_config() -> bool:
    """Test LangSwarm memory configuration"""
    print_section("LangSwarm Memory Configuration Test")
    
    try:
        from langswarm.core.config import MemoryConfig
        
        # Test auto-detection
        config = MemoryConfig.setup_memory("production")
        print(f"✅ Memory configuration created")
        print(f"   Backend: {config.backend}")
        print(f"   Enabled: {config.enabled}")
        print(f"   Description: {config.get_tier_description()}")
        
        if config.backend == "bigquery":
            print("🎉 BigQuery automatically detected and selected!")
        else:
            print(f"ℹ️ Using {config.backend} backend (BigQuery not auto-selected)")
            print("   This might be because:")
            print("   - Environment variables not properly set")
            print("   - BigQuery library not installed")
            print("   - Other backends have higher priority")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory configuration failed: {e}")
        return False

def test_bigquery_adapter() -> bool:
    """Test BigQuery adapter directly"""
    print_section("BigQuery Adapter Test")
    
    try:
        from langswarm.memory.adapters._langswarm.bigquery.main import BigQueryAdapter
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        # Create adapter
        adapter = BigQueryAdapter(
            identifier="test_adapter",
            project_id=project_id,
            dataset_id="langswarm_test",
            table_id="test_memory"
        )
        
        print(f"✅ BigQuery adapter created")
        print(f"   Project: {adapter.project_id}")
        print(f"   Dataset: {adapter.dataset_id}")
        print(f"   Table: {adapter.table_id}")
        print(f"   Full table reference: {adapter.table_ref}")
        
        # Test capabilities
        capabilities = adapter.capabilities()
        print(f"✅ Adapter capabilities: {list(capabilities.keys())}")
        
        # Test adding a document
        test_doc = {
            "key": f"test_{datetime.now().isoformat()}",
            "text": "This is a test memory for BigQuery setup verification",
            "metadata": {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "setup_verification": True
            }
        }
        
        adapter.add_documents([test_doc])
        print("✅ Test document added successfully")
        
        # Test querying
        results = adapter.query("test memory", top_k=1)
        if results:
            print(f"✅ Query test successful: Found {len(results)} results")
            print(f"   Sample result: {results[0]['text'][:50]}...")
        else:
            print("⚠️ Query returned no results (might be expected)")
        
        return True
        
    except Exception as e:
        print(f"❌ BigQuery adapter test failed: {e}")
        return False

def test_end_to_end() -> bool:
    """Test end-to-end agent creation with BigQuery memory"""
    print_section("End-to-End Agent Test")
    
    try:
        from langswarm.core.agents.simple import create_chat_agent
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        # Create agent with explicit BigQuery configuration
        agent = create_chat_agent(
            agent_id="test_bigquery_agent",
            memory_config={
                "backend": "bigquery",
                "settings": {
                    "project_id": project_id,
                    "dataset_id": "langswarm_e2e_test",
                    "table_id": "agent_test_conversations"
                }
            }
        )
        
        print("✅ Agent with BigQuery memory created successfully")
        
        # Test conversation
        test_message = f"Hello! This is an end-to-end test at {datetime.now()}"
        response = agent.chat(test_message)
        
        print(f"✅ Conversation test completed")
        print(f"   User: {test_message}")
        print(f"   Agent: {response[:100]}..." if len(response) > 100 else f"   Agent: {response}")
        
        # Test memory recall
        recall_response = agent.chat("What did I just say to you?")
        print(f"✅ Memory recall test")
        print(f"   Recall response: {recall_response[:100]}..." if len(recall_response) > 100 else f"   Recall response: {recall_response}")
        
        # Cleanup
        agent.cleanup()
        print("✅ Agent cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False

def print_setup_summary():
    """Print setup instructions summary"""
    print_section("Setup Summary")
    
    print("📋 To set up BigQuery memory backend:")
    print("")
    print("1. **Install Dependencies:**")
    print("   pip install google-cloud-bigquery")
    print("")
    print("2. **Set Environment Variables:**")
    print("   export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account.json'")
    print("   export GOOGLE_CLOUD_PROJECT='your-project-id'")
    print("")
    print("3. **Use in LangSwarm:**")
    print("   # Option 1: Auto-detection")
    print("   memory: production")
    print("")
    print("   # Option 2: Explicit configuration")
    print("   memory:")
    print("     backend: bigquery")
    print("     settings:")
    print("       project_id: your-project-id")
    print("       dataset_id: langswarm_memory")
    print("")
    print("📚 For detailed setup instructions, see:")
    print("   docs/BIGQUERY_SETUP_GUIDE.md")

def main():
    """Run all tests"""
    print("🚀 BigQuery Memory Backend Setup Test")
    print("=====================================")
    print("This script will verify your BigQuery setup for LangSwarm memory backend.")
    
    # Track test results
    tests = [
        ("Environment Variables", check_environment),
        ("BigQuery Import", test_bigquery_import),
        ("BigQuery Connection", test_bigquery_connection),
        ("Memory Configuration", test_memory_config),
        ("BigQuery Adapter", test_bigquery_adapter),
        ("End-to-End Agent", test_end_to_end)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Print results summary
    print_section("Test Results Summary")
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your BigQuery memory backend is ready to use.")
        print("\n🚀 Next steps:")
        print("   1. Use 'memory: production' in your LangSwarm configuration")
        print("   2. Create agents and start building conversations")
        print("   3. Use BigQuery Console to analyze your agent data")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please fix the issues above.")
        print_setup_summary()

if __name__ == "__main__":
    main()