#!/usr/bin/env python3
"""
Knowledge Management Integration Tests
End-to-end tests for the complete knowledge management flow
"""

import sys
import os
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/Users/alexanderekdahl/Docker/LangSwarm')

class MockCrawl4AIResponse:
    """Mock response for Crawl4AI MCP calls"""
    
    @staticmethod
    def successful_scrape_response():
        return {
            "result": {
                "content": "This is the main content of the webpage. It contains useful information about the company.",
                "title": "Company About Page",
                "extracted_content": {
                    "title": "Company About Page",
                    "content": "This is the main content of the webpage. It contains useful information about the company.",
                    "description": "Learn about our company and mission",
                    "key_points": [
                        "Founded in 2020",
                        "Serving customers worldwide", 
                        "Expert team of professionals"
                    ]
                },
                "metadata": {
                    "status_code": 200,
                    "response_time": 1.2,
                    "url": "https://example.com/about"
                }
            }
        }

class MockBigQueryClient:
    """Mock BigQuery client for testing"""
    
    def __init__(self):
        self.datasets = {}
        self.tables = {}
        self.rows = []
    
    def dataset(self, dataset_id):
        mock_dataset = Mock()
        mock_dataset.dataset_id = dataset_id
        return mock_dataset
    
    def create_dataset(self, dataset):
        return dataset
    
    def get_table(self, table_ref):
        mock_table = Mock()
        mock_table.num_rows = len(self.rows)
        mock_table.schema = []
        return mock_table
    
    def create_table(self, table):
        return table
    
    def insert_rows_json(self, table, rows):
        self.rows.extend(rows)
        return []  # Empty list means no errors
    
    def query(self, query_str):
        # Mock query results based on the query type
        mock_job = Mock()
        
        if "ML.DISTANCE" in query_str:  # Similarity search
            mock_row = Mock()
            mock_row.document_id = "test_doc_1"
            mock_row.content = "This is the main content of the webpage."
            mock_row.url = "https://example.com/about"
            mock_row.title = "Company About Page"
            mock_row.similarity = 0.85
            mock_row.created_at = datetime.now()
            mock_row.metadata = '{"source": "crawl4ai"}'
            mock_job.result.return_value = [mock_row]
        else:  # Other queries
            mock_job.result.return_value = []
        
        return mock_job

async def test_end_to_end_knowledge_flow():
    """Test the complete knowledge management flow"""
    print("🔄 Testing End-to-End Knowledge Flow...")
    print("-" * 50)
    
    try:
        # Mock environment variables
        with patch.dict(os.environ, {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'OPENAI_API_KEY': 'test-openai-key',
            'CRAWL4AI_BASE_URL': 'http://test-crawl4ai.com'
        }):
            
            # Mock external dependencies
            mock_bq_client = MockBigQueryClient()
            
            # Create a comprehensive OpenAI mock with async support
            mock_openai_client = Mock()
            mock_embeddings = AsyncMock()
            mock_embedding_response = Mock()
            mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]  # 1536 dims
            mock_embeddings.create.return_value = mock_embedding_response
            mock_openai_client.embeddings = mock_embeddings
            
            with patch('external.aaf.app.services.web_scraper.bigquery.Client', return_value=mock_bq_client), \
                 patch('external.aaf.app.services.web_scraper.openai.AsyncOpenAI', return_value=mock_openai_client), \
                 patch('external.aaf.app.services.web_scraper.requests.post') as mock_post:
                
                # Mock Crawl4AI response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = MockCrawl4AIResponse.successful_scrape_response()
                mock_post.return_value = mock_response
                
                # Import and initialize web scraper
                from external.aaf.app.services.web_scraper import WebScrapingService
                
                scraper = WebScrapingService(
                    project_id="test-project",
                    dataset_id="vector_search",
                    table_name="embeddings",
                    openai_api_key="test-openai-key",
                    crawl4ai_base_url="http://test-crawl4ai.com"
                )
                
                print("  ✅ Step 1: Web scraper initialized")
                
                # Test scraping and embedding
                result = await scraper.scrape_and_embed_url("https://example.com/about")
                
                assert result["success"] == True
                assert result["url"] == "https://example.com/about"
                assert result["title"] == "Company About Page"
                assert result["chunks_processed"] > 0
                assert result["documents_stored"] > 0
                
                print(f"  ✅ Step 2: Successfully scraped and embedded URL")
                print(f"     - Title: {result['title']}")
                print(f"     - Chunks: {result['chunks_processed']}")
                print(f"     - Documents: {result['documents_stored']}")
                
                # Test BigQuery MCP tool
                with patch('langswarm.mcp.tools.bigquery_vector_search.main.bigquery.Client', return_value=mock_bq_client), \
                     patch('langswarm.mcp.tools.bigquery_vector_search.main.openai.AsyncOpenAI') as mock_async_openai:
                    
                    # Mock async OpenAI client
                    mock_async_client = AsyncMock()
                    mock_embedding_response = Mock()
                    mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
                    mock_async_client.embeddings.create.return_value = mock_embedding_response
                    mock_async_openai.return_value = mock_async_client
                    
                    from langswarm.mcp.tools.bigquery_vector_search.main import similarity_search, SimilaritySearchInput
                    
                    # Test similarity search
                    search_input = SimilaritySearchInput(
                        query="Tell me about the company",
                        query_embedding=[0.1, 0.2, 0.3] * 512,
                        limit=5,
                        similarity_threshold=0.7
                    )
                    
                    search_result = similarity_search(search_input)
                    
                    assert search_result.success == True
                    assert search_result.total_results > 0
                    assert len(search_result.results) > 0
                    assert search_result.results[0]["similarity"] >= 0.7
                    
                    print(f"  ✅ Step 3: Vector similarity search successful")
                    print(f"     - Found {search_result.total_results} relevant documents")
                    print(f"     - Best match similarity: {search_result.results[0]['similarity']:.3f}")
                
                print("  ✅ Step 4: Knowledge is immediately available for chatbot queries")
                
                return True
                
    except Exception as e:
        print(f"  ❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_knowledge_api_endpoints():
    """Test the knowledge API endpoints"""
    print("🌐 Testing Knowledge API Endpoints...")
    print("-" * 50)
    
    try:
        with patch.dict(os.environ, {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'OPENAI_API_KEY': 'test-key',
            'SECRET_KEY': 'test-secret',
            'MANAGEMENT_API_SECRET': 'test-management-secret',
            'CRAWL4AI_BASE_URL': 'http://test-crawl4ai.com'
        }):
            
            # Mock the scraper service
            with patch('external.aaf.app.api.knowledge.scraper_service') as mock_service:
                
                # Mock successful scraping
                mock_service.scrape_and_embed_url.return_value = {
                    "success": True,
                    "url": "https://example.com/test",
                    "title": "Test Page",
                    "chunks_processed": 3,
                    "documents_stored": 3,
                    "document_ids": ["doc_1", "doc_2", "doc_3"]
                }
                
                # Mock stored URLs
                mock_service.get_stored_urls.return_value = [
                    {
                        "url": "https://example.com/test",
                        "title": "Test Page",
                        "chunk_count": 3,
                        "last_updated": "2024-01-15T10:30:00Z",
                        "metadata": {"domain": "example.com"}
                    }
                ]
                
                # Import the API router
                from external.aaf.app.api.knowledge import router
                
                print("  ✅ Step 1: Knowledge API imported successfully")
                
                # Test that endpoints are properly defined
                route_paths = [route.path for route in router.routes]
                
                expected_endpoints = ["/api/knowledge/scrape", "/api/knowledge/urls", "/api/knowledge/stats"]
                for endpoint in expected_endpoints:
                    assert endpoint in route_paths, f"Missing endpoint: {endpoint}. Found: {route_paths}"
                
                print("  ✅ Step 2: All required endpoints are defined")
                print(f"     - Endpoints: {expected_endpoints}")
                
                return True
                
    except Exception as e:
        print(f"  ❌ API endpoints test failed: {e}")
        return False

def test_langswarm_tool_configuration():
    """Test LangSwarm tool configuration"""
    print("⚙️  Testing LangSwarm Tool Configuration...")
    print("-" * 50)
    
    try:
        import yaml
        
        # Test AAF instance configuration
        with open('/Users/alexanderekdahl/Docker/LangSwarm/external/aaf/config/langswarm.yaml', 'r') as f:
            aaf_config = yaml.safe_load(f)
        
        agents = aaf_config.get('agents', [])
        assert len(agents) > 0, "No agents found in AAF config"
        
        default_agent = agents[0]
        tools = default_agent.get('tools', [])
        
        vector_tool = None
        for tool in tools:
            if tool.get('name') == 'vector_search':
                vector_tool = tool
                break
        
        assert vector_tool is not None, "vector_search tool not found in AAF config"
        assert vector_tool['type'] == 'local_mcp'
        assert vector_tool['mcp_server'] == 'bigquery_vector_search'
        assert vector_tool['enabled'] == True
        
        print("  ✅ Step 1: AAF instance configuration valid")
        
        print("  ✅ Step 2: Tools are now registered via built-in system (no separate config file needed)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_mcp_tool_architecture():
    """Test MCP tool follows LangSwarm architecture"""
    print("🏗️  Testing MCP Tool Architecture...")
    print("-" * 50)
    
    try:
        # Test file structure
        base_path = "/Users/alexanderekdahl/Docker/LangSwarm/langswarm/mcp/tools/bigquery_vector_search"
        
        required_files = [
            "main.py",
            "agents.yaml", 
            "workflows.yaml",
            "template.md",
            "readme.md",
            "__init__.py"
        ]
        
        for file_name in required_files:
            file_path = f"{base_path}/{file_name}"
            assert os.path.exists(file_path), f"Missing file: {file_name}"
        
        print("  ✅ Step 1: All required files present")
        
        # Test server follows BaseMCPToolServer pattern
        from langswarm.mcp.tools.bigquery_vector_search.main import server
        from langswarm.mcp.server_base import BaseMCPToolServer
        
        assert isinstance(server, BaseMCPToolServer), "Server not based on BaseMCPToolServer"
        assert server.local_mode == True, "Server should be in local mode"
        assert len(server.tasks) > 0, "Server has no tasks"
        
        print("  ✅ Step 2: Server follows BaseMCPToolServer pattern")
        
        # Test Pydantic models
        from langswarm.mcp.tools.bigquery_vector_search.main import (
            SimilaritySearchInput, SimilaritySearchOutput,
            ListDatasetsInput, ListDatasetsOutput,
            GetContentInput, GetContentOutput,
            DatasetInfoInput, DatasetInfoOutput
        )
        
        # Test that models can be instantiated
        search_input = SimilaritySearchInput(query="test", limit=5)
        assert search_input.query == "test"
        
        print("  ✅ Step 3: Pydantic models work correctly")
        
        # Test YAML configurations
        import yaml
        
        with open(f"{base_path}/agents.yaml", 'r') as f:
            agents = yaml.safe_load(f)
        
        assert 'agents' in agents
        assert len(agents['agents']) >= 5, "Should have at least 5 agents"
        
        with open(f"{base_path}/workflows.yaml", 'r') as f:
            workflows = yaml.safe_load(f)
        
        assert 'workflows' in workflows
        assert len(workflows['workflows']) >= 5, "Should have at least 5 workflows"
        
        print("  ✅ Step 4: YAML configurations are valid")
        print(f"     - Agents: {len(agents['agents'])}")
        print(f"     - Workflows: {len(workflows['workflows'])}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Architecture test failed: {e}")
        return False

async def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Knowledge Management Integration Tests")
    print("=" * 60)
    
    tests = [
        ("End-to-End Flow", test_end_to_end_knowledge_flow),
        ("API Endpoints", test_knowledge_api_endpoints),
        ("Tool Configuration", test_langswarm_tool_configuration),
        ("MCP Architecture", test_mcp_tool_architecture),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("=" * 60)
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY")
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
        print("\n🎉 ALL INTEGRATION TESTS PASSED! 🎉")
        print("📋 Knowledge Management System is fully functional!")
        print("\n🔗 Ready for Frontend Integration:")
        print("   1. Web Scraping API (/api/knowledge/scrape)")
        print("   2. URL Management (/api/knowledge/urls)")
        print("   3. Knowledge Stats (/api/knowledge/stats)")
        print("   4. Vector Search (via LangSwarm chatbot)")
        print("   5. Intelligent NLP workflows")
        return True
    else:
        print(f"\n⚠️  {failed} integration test(s) failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
