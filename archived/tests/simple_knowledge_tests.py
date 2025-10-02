#!/usr/bin/env python3
"""
Simple Knowledge Management Tests
Basic validation tests that can run without external dependencies
"""

import sys
import os
import json
import yaml
from unittest.mock import Mock, patch
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/Users/alexanderekdahl/Docker/LangSwarm')

def test_imports():
    """Test that all knowledge management components can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test web scraper import
        from external.aaf.app.services.web_scraper import WebScrapingService
        print("  ✅ Web scraper service imported successfully")
        
        # Test BigQuery MCP tool import  
        from langswarm.mcp.tools.bigquery_vector_search.main import server, similarity_search
        print("  ✅ BigQuery MCP tool imported successfully")
        
        # Test knowledge API import with mock environment
        with patch.dict(os.environ, {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'OPENAI_API_KEY': 'test-key',
            'SECRET_KEY': 'test-secret',
            'MANAGEMENT_API_SECRET': 'test-management-secret',
            'CRAWL4AI_BASE_URL': 'http://test-crawl4ai.com'
        }):
            from external.aaf.app.api.knowledge import router
            print("  ✅ Knowledge API router imported successfully")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Test failed with exception: {e}")
        return False

def test_web_scraper_initialization():
    """Test web scraper can be initialized"""
    print("🧪 Testing web scraper initialization...")
    
    try:
        from external.aaf.app.services.web_scraper import WebScrapingService
        
        # Mock BigQuery and OpenAI clients to avoid actual initialization
        with patch('external.aaf.app.services.web_scraper.bigquery') as mock_bq, \
             patch('external.aaf.app.services.web_scraper.openai') as mock_openai:
            
            # Test with required parameters
            scraper = WebScrapingService(
                project_id="test-project",
                dataset_id="test_dataset", 
                table_name="test_table",
                openai_api_key="test-key",
                crawl4ai_base_url="http://test-crawl4ai.com"
            )
            
            assert scraper.project_id == "test-project"
            assert scraper.dataset_id == "test_dataset"
            assert scraper.crawl4ai_base_url == "http://test-crawl4ai.com"
            assert scraper._table_initialized == False
            
            print("  ✅ Web scraper initialization successful")
            return True
    except Exception as e:
        print(f"  ❌ Web scraper initialization failed: {e}")
        return False

def test_web_scraper_missing_url():
    """Test web scraper fails without Crawl4AI URL"""
    print("🧪 Testing web scraper validation...")
    
    try:
        from external.aaf.app.services.web_scraper import WebScrapingService
        
        try:
            # This should fail - no CRAWL4AI_BASE_URL
            scraper = WebScrapingService(
                project_id="test-project",
                openai_api_key="test-key"
            )
            print("  ❌ Should have failed without CRAWL4AI_BASE_URL")
            return False
        except ValueError as e:
            if "CRAWL4AI_BASE_URL" in str(e):
                print("  ✅ Correctly validates missing CRAWL4AI_BASE_URL")
                return True
            else:
                print(f"  ❌ Wrong error: {e}")
                return False
    except Exception as e:
        print(f"  ❌ Validation test failed: {e}")
        return False

def test_mcp_server_structure():
    """Test BigQuery MCP server has correct structure"""
    print("🧪 Testing MCP server structure...")
    
    try:
        from langswarm.mcp.tools.bigquery_vector_search.main import server
        
        # Check server properties
        assert hasattr(server, 'name')
        assert hasattr(server, 'description')
        assert hasattr(server, 'tasks')
        
        # Check expected tasks exist
        expected_tasks = ["similarity_search", "list_datasets", "get_content", "dataset_info"]
        actual_tasks = list(server.tasks.keys())
        
        for task in expected_tasks:
            if task not in actual_tasks:
                print(f"  ❌ Missing expected task: {task}")
                return False
        
        print(f"  ✅ MCP server has all {len(expected_tasks)} expected tasks")
        return True
    except Exception as e:
        print(f"  ❌ MCP server structure test failed: {e}")
        return False

def test_configuration_files():
    """Test that YAML configuration files are valid"""
    print("🧪 Testing configuration files...")
    
    base_path = "/Users/alexanderekdahl/Docker/LangSwarm/langswarm/mcp/tools/bigquery_vector_search"
    
    # Test agents.yaml
    try:
        with open(f"{base_path}/agents.yaml", 'r') as f:
            agents_config = yaml.safe_load(f)
        
        assert 'agents' in agents_config
        assert len(agents_config['agents']) > 0
        
        # Check for required agents
        agent_ids = [agent['id'] for agent in agents_config['agents']]
        required_agents = ['input_normalizer', 'search_intent_classifier', 'search_response_formatter']
        
        for agent_id in required_agents:
            if agent_id not in agent_ids:
                print(f"  ❌ Missing required agent: {agent_id}")
                return False
        
        print(f"  ✅ agents.yaml valid with {len(agent_ids)} agents")
    except Exception as e:
        print(f"  ❌ agents.yaml test failed: {e}")
        return False
    
    # Test workflows.yaml
    try:
        with open(f"{base_path}/workflows.yaml", 'r') as f:
            workflows_config = yaml.safe_load(f)
        
        assert 'workflows' in workflows_config
        assert len(workflows_config['workflows']) > 0
        
        # Check for main workflow
        workflow_ids = [workflow['id'] for workflow in workflows_config['workflows']]
        if 'intelligent_search_workflow' not in workflow_ids:
            print("  ❌ Missing intelligent_search_workflow")
            return False
        
        print(f"  ✅ workflows.yaml valid with {len(workflow_ids)} workflows")
        return True
    except Exception as e:
        print(f"  ❌ workflows.yaml test failed: {e}")
        return False

def test_pydantic_models():
    """Test that Pydantic models work correctly"""
    print("🧪 Testing Pydantic models...")
    
    try:
        from langswarm.mcp.tools.bigquery_vector_search.main import (
            SimilaritySearchInput, SimilaritySearchOutput, 
            ListDatasetsInput, GetContentInput
        )
        
        # Test SimilaritySearchInput
        search_input = SimilaritySearchInput(
            query="test query",
            limit=5,
            similarity_threshold=0.8
        )
        assert search_input.query == "test query"
        assert search_input.limit == 5
        
        # Test SimilaritySearchOutput
        search_output = SimilaritySearchOutput(
            success=True,
            query="test query",
            results=[],
            total_results=0,
            dataset="test.table"
        )
        assert search_output.success == True
        
        # Test other models
        list_input = ListDatasetsInput(pattern="test")
        assert list_input.pattern == "test"
        
        get_input = GetContentInput(document_id="doc_123")
        assert get_input.document_id == "doc_123"
        
        print("  ✅ All Pydantic models work correctly")
        return True
    except Exception as e:
        print(f"  ❌ Pydantic models test failed: {e}")
        return False

def test_chunking_logic():
    """Test text chunking functionality"""
    print("🧪 Testing text chunking logic...")
    
    try:
        from external.aaf.app.services.web_scraper import WebScrapingService
        
        # Mock BigQuery and OpenAI clients
        with patch('external.aaf.app.services.web_scraper.bigquery') as mock_bq, \
             patch('external.aaf.app.services.web_scraper.openai') as mock_openai:
            
            # Create a minimal scraper just for testing chunking
            scraper = WebScrapingService(
                project_id="test",
                crawl4ai_base_url="http://test.com",
                openai_api_key="test"
            )
            
            # Test small text (should return single chunk)
            small_text = "This is a small piece of text."
            chunks = scraper._chunk_text(small_text, chunk_size=100, overlap=20)
            
            assert len(chunks) == 1
            assert chunks[0] == small_text
            
            # Test larger text (should return multiple chunks)
            large_text = "This is a sentence. " * 50  # 1000+ characters
            chunks = scraper._chunk_text(large_text, chunk_size=200, overlap=50)
            
            assert len(chunks) > 1
            
            # Check that all chunks are reasonable length
            for chunk in chunks:
                assert len(chunk) <= 250  # Allow some variance for sentence boundaries
            
            print(f"  ✅ Text chunking works correctly ({len(chunks)} chunks from large text)")
            return True
    except Exception as e:
        print(f"  ❌ Chunking logic test failed: {e}")
        return False

def test_mock_similarity_search():
    """Test similarity search with mocked BigQuery"""
    print("🧪 Testing similarity search logic...")
    
    try:
        from langswarm.mcp.tools.bigquery_vector_search.main import similarity_search, SimilaritySearchInput
        
        # Test without embedding (should fail gracefully)
        input_data = SimilaritySearchInput(
            query="test query",
            limit=5,
            similarity_threshold=0.7
        )
        
        # Mock the environment
        with patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
            result = similarity_search(input_data)
        
        # Should fail because no embedding provided
        assert result.success == False
        assert "query_embedding is required" in result.error
        
        print("  ✅ Similarity search correctly handles missing embedding")
        return True
    except Exception as e:
        print(f"  ❌ Similarity search test failed: {e}")
        return False

def test_langswarm_integration():
    """Test LangSwarm integration configuration"""
    print("🧪 Testing LangSwarm integration...")
    
    try:
        # Test that the tool can be found in LangSwarm config
        config_path = "/Users/alexanderekdahl/Docker/LangSwarm/external/aaf/config/langswarm.yaml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for vector search tool in configuration
        agents = config.get('agents', [])
        if not agents:
            print("  ❌ No agents found in langswarm.yaml")
            return False
        
        default_agent = agents[0]  # First agent should be the default
        tools = default_agent.get('tools', [])
        
        vector_search_tool = None
        for tool in tools:
            if tool.get('name') == 'vector_search':
                vector_search_tool = tool
                break
        
        if not vector_search_tool:
            print("  ❌ vector_search tool not found in langswarm.yaml")
            return False
        
        assert vector_search_tool['type'] == 'local_mcp'
        assert vector_search_tool['mcp_server'] == 'bigquery_vector_search'
        assert vector_search_tool['enabled'] == True
        
        print("  ✅ LangSwarm configuration includes vector search tool")
        return True
    except Exception as e:
        print(f"  ❌ LangSwarm integration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Starting Knowledge Management System Tests")
    print("=" * 60)
    
    tests = [
        ("Component Imports", test_imports),
        ("Web Scraper Init", test_web_scraper_initialization),
        ("Web Scraper Validation", test_web_scraper_missing_url),
        ("MCP Server Structure", test_mcp_server_structure),
        ("Configuration Files", test_configuration_files),
        ("Pydantic Models", test_pydantic_models),
        ("Text Chunking", test_chunking_logic),
        ("Similarity Search", test_mock_similarity_search),
        ("LangSwarm Integration", test_langswarm_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print("-" * 40)
    print(f"Total Tests: {len(results)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Knowledge Management System is ready! 🎉")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
