"""
Tests for Knowledge Management System
Tests the web scraper service and BigQuery vector search MCP tool
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Test the web scraper service
class TestWebScrapingService:
    """Test the web scraping service with Crawl4AI integration"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock()
        settings.google_cloud_project = "test-project"
        settings.openai_api_key = "test-api-key"
        return settings
    
    @pytest.fixture
    def web_scraper(self, mock_settings):
        """Create web scraper instance for testing"""
        with patch.dict(os.environ, {'CRAWL4AI_BASE_URL': 'http://test-crawl4ai.com'}):
            from external.aaf.app.services.web_scraper import WebScrapingService
            return WebScrapingService(
                project_id="test-project",
                dataset_id="test_dataset",
                table_name="test_table",
                openai_api_key="test-key",
                crawl4ai_base_url="http://test-crawl4ai.com"
            )
    
    def test_init_with_crawl4ai_url(self):
        """Test web scraper initialization with Crawl4AI URL"""
        from external.aaf.app.services.web_scraper import WebScrapingService
        
        scraper = WebScrapingService(
            project_id="test-project",
            crawl4ai_base_url="http://test-crawl4ai.com",
            openai_api_key="test-key"
        )
        
        assert scraper.crawl4ai_base_url == "http://test-crawl4ai.com"
        assert scraper.project_id == "test-project"
    
    def test_init_without_crawl4ai_url_raises_error(self):
        """Test that missing Crawl4AI URL raises error"""
        from external.aaf.app.services.web_scraper import WebScrapingService
        
        with pytest.raises(ValueError, match="CRAWL4AI_BASE_URL"):
            WebScrapingService(
                project_id="test-project",
                openai_api_key="test-key"
            )
    
    @patch('external.aaf.app.services.web_scraper.requests.post')
    def test_call_crawl4ai_mcp_success(self, mock_post, web_scraper):
        """Test successful Crawl4AI MCP call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "content": "Test content",
                "title": "Test Title",
                "extracted_content": {
                    "title": "Test Title",
                    "content": "Test content",
                    "description": "Test description"
                }
            }
        }
        mock_post.return_value = mock_response
        
        result = web_scraper._call_crawl4ai_mcp("scrape", {"url": "http://test.com"})
        
        assert result["content"] == "Test content"
        assert result["title"] == "Test Title"
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://test-crawl4ai.com"
        assert "tools/call" in call_args[1]["json"]["method"]
    
    @patch('external.aaf.app.services.web_scraper.requests.post')
    def test_call_crawl4ai_mcp_error(self, mock_post, web_scraper):
        """Test Crawl4AI MCP call with error response"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": {"message": "Scraping failed"}
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="MCP error: {'message': 'Scraping failed'}"):
            web_scraper._call_crawl4ai_mcp("scrape", {"url": "http://test.com"})
    
    @patch('external.aaf.app.services.web_scraper.requests.post')
    async def test_scrape_url_success(self, mock_post, web_scraper):
        """Test successful URL scraping"""
        # Mock Crawl4AI response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "content": "This is test content from the webpage",
                "title": "Test Page Title",
                "extracted_content": {
                    "title": "Test Page Title",
                    "content": "This is test content from the webpage",
                    "description": "A test page description",
                    "key_points": ["Point 1", "Point 2"]
                },
                "metadata": {
                    "status_code": 200,
                    "response_time": 1.5
                }
            }
        }
        mock_post.return_value = mock_response
        
        result = await web_scraper._scrape_url("http://test.com")
        
        assert result is not None
        assert result["title"] == "Test Page Title"
        assert result["content"] == "This is test content from the webpage"
        assert result["metadata"]["scraper"] == "crawl4ai_mcp"
        assert result["metadata"]["description"] == "A test page description"
        assert result["metadata"]["key_points"] == ["Point 1", "Point 2"]
    
    @patch('external.aaf.app.services.web_scraper.requests.post')
    async def test_scrape_url_no_content(self, mock_post, web_scraper):
        """Test URL scraping with no content returned"""
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {}
        }
        mock_post.return_value = mock_response
        
        result = await web_scraper._scrape_url("http://test.com")
        
        assert result is None
    
    def test_chunk_text_small_content(self, web_scraper):
        """Test text chunking with small content"""
        text = "This is a small piece of text."
        chunks = web_scraper._chunk_text(text, chunk_size=100, overlap=20)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_large_content(self, web_scraper):
        """Test text chunking with large content"""
        text = "This is a sentence. " * 100  # Create long text
        chunks = web_scraper._chunk_text(text, chunk_size=200, overlap=50)
        
        assert len(chunks) > 1
        # Check that chunks have some overlap
        if len(chunks) > 1:
            # Find common text between consecutive chunks
            overlap_found = False
            for i in range(len(chunks) - 1):
                if any(word in chunks[i+1] for word in chunks[i].split()[-10:]):
                    overlap_found = True
                    break
            assert overlap_found, "Chunks should have some overlap"


# Test the BigQuery MCP tool
class TestBigQueryVectorSearch:
    """Test the BigQuery vector search MCP tool"""
    
    @pytest.fixture
    def mock_bigquery_client(self):
        """Mock BigQuery client"""
        with patch('langswarm.mcp.tools.bigquery_vector_search.main.bigquery') as mock_bq:
            mock_client = Mock()
            mock_bq.Client.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def vector_search_tool(self):
        """Create vector search tool instance"""
        with patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
            from langswarm.mcp.tools.bigquery_vector_search.main import similarity_search, SimilaritySearchInput
            return similarity_search
    
    def test_similarity_search_missing_embedding(self, vector_search_tool, mock_bigquery_client):
        """Test similarity search without query embedding"""
        input_data = {
            "query": "test query",
            "limit": 5,
            "similarity_threshold": 0.7
        }
        
        # Convert dict to Pydantic model
        from langswarm.mcp.tools.bigquery_vector_search.main import SimilaritySearchInput
        input_model = SimilaritySearchInput(**input_data)
        
        result = vector_search_tool(input_model)
        
        assert result.success == False
        assert "query_embedding is required" in result.error
    
    def test_similarity_search_with_embedding(self, vector_search_tool, mock_bigquery_client):
        """Test similarity search with query embedding"""
        # Mock BigQuery query results
        mock_row = Mock()
        mock_row.document_id = "doc_1"
        mock_row.content = "Test content"
        mock_row.url = "http://test.com"
        mock_row.title = "Test Title"
        mock_row.similarity = 0.85
        mock_row.created_at = datetime.now()
        mock_row.metadata = '{"test": "metadata"}'
        
        mock_job = Mock()
        mock_job.result.return_value = [mock_row]
        mock_bigquery_client.query.return_value = mock_job
        
        input_data = {
            "query": "test query",
            "query_embedding": [0.1, 0.2, 0.3],  # Mock embedding
            "limit": 5,
            "similarity_threshold": 0.7
        }
        
        from langswarm.mcp.tools.bigquery_vector_search.main import SimilaritySearchInput
        input_model = SimilaritySearchInput(**input_data)
        
        result = vector_search_tool(input_model)
        
        assert result.success == True
        assert result.total_results == 1
        assert len(result.results) == 1
        assert result.results[0]["document_id"] == "doc_1"
        assert result.results[0]["similarity"] == 0.85
    
    def test_list_datasets(self, mock_bigquery_client):
        """Test listing datasets"""
        from langswarm.mcp.tools.bigquery_vector_search.main import list_datasets, ListDatasetsInput
        
        # Mock dataset with embedding table
        mock_dataset = Mock()
        mock_dataset.dataset_id = "test_dataset"
        mock_dataset.location = "US"
        
        mock_table = Mock()
        mock_table.table_id = "embeddings"
        mock_table_ref = Mock()
        mock_table_ref.num_rows = 100
        mock_table_ref.created = datetime.now()
        mock_table_ref.schema = [
            Mock(name="document_id"),
            Mock(name="embedding"),
            Mock(name="content")
        ]
        
        mock_bigquery_client.list_datasets.return_value = [mock_dataset]
        mock_bigquery_client.list_tables.return_value = [mock_table]
        mock_bigquery_client.get_table.return_value = mock_table_ref
        
        input_model = ListDatasetsInput()
        result = list_datasets(input_model)
        
        assert result.success == True
        assert result.total_datasets == 1
        assert len(result.datasets) == 1
        assert result.datasets[0]["dataset_id"] == "test_dataset"
    
    def test_get_content(self, mock_bigquery_client):
        """Test getting content by document ID"""
        from langswarm.mcp.tools.bigquery_vector_search.main import get_content, GetContentInput
        
        # Mock query result
        mock_row = Mock()
        mock_row.document_id = "doc_1"
        mock_row.content = "Full document content"
        mock_row.url = "http://test.com"
        mock_row.title = "Test Document"
        mock_row.created_at = datetime.now()
        mock_row.metadata = '{"source": "test"}'
        
        mock_job = Mock()
        mock_job.result.return_value = [mock_row]
        mock_bigquery_client.query.return_value = mock_job
        
        input_model = GetContentInput(document_id="doc_1")
        result = get_content(input_model)
        
        assert result.success == True
        assert result.result["document_id"] == "doc_1"
        assert result.result["content"] == "Full document content"
    
    def test_get_content_not_found(self, mock_bigquery_client):
        """Test getting content for non-existent document"""
        from langswarm.mcp.tools.bigquery_vector_search.main import get_content, GetContentInput
        
        # Mock empty query result
        mock_job = Mock()
        mock_job.result.return_value = []
        mock_bigquery_client.query.return_value = mock_job
        
        input_model = GetContentInput(document_id="nonexistent")
        result = get_content(input_model)
        
        assert result.success == False
        assert "Document not found" in result.error


# Test the knowledge API endpoints
class TestKnowledgeAPI:
    """Test the knowledge management API endpoints"""
    
    @pytest.fixture
    def mock_web_scraper(self):
        """Mock web scraper service"""
        with patch('external.aaf.app.api.knowledge.scraper_service') as mock_service:
            yield mock_service
    
    @pytest.fixture
    def test_client(self):
        """Create test client for FastAPI"""
        from fastapi.testclient import TestClient
        from external.aaf.app.main import create_app
        
        app = create_app()
        return TestClient(app)
    
    def test_scrape_endpoint_success(self, test_client, mock_web_scraper):
        """Test successful scraping endpoint"""
        # Mock successful scraping
        mock_web_scraper.scrape_and_embed_url.return_value = {
            "success": True,
            "url": "http://test.com",
            "title": "Test Page",
            "chunks_processed": 3,
            "documents_stored": 3,
            "document_ids": ["doc_1", "doc_2", "doc_3"]
        }
        
        response = test_client.post(
            "/api/knowledge/scrape",
            json={"url": "http://test.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["chunks_processed"] == 3
    
    def test_scrape_endpoint_failure(self, test_client, mock_web_scraper):
        """Test scraping endpoint with failure"""
        # Mock failed scraping
        mock_web_scraper.scrape_and_embed_url.return_value = {
            "success": False,
            "error": "Failed to scrape URL"
        }
        
        response = test_client.post(
            "/api/knowledge/scrape",
            json={"url": "http://invalid-url.com"}
        )
        
        # Should still return 200 but with success=false
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "error" in data
    
    def test_list_urls_endpoint(self, test_client, mock_web_scraper):
        """Test list URLs endpoint"""
        # Mock stored URLs
        mock_web_scraper.get_stored_urls.return_value = [
            {
                "url": "http://test1.com",
                "title": "Test Page 1",
                "chunk_count": 3,
                "last_updated": "2024-01-15T10:30:00Z",
                "metadata": {"domain": "test1.com"}
            },
            {
                "url": "http://test2.com", 
                "title": "Test Page 2",
                "chunk_count": 2,
                "last_updated": "2024-01-14T15:45:00Z",
                "metadata": {"domain": "test2.com"}
            }
        ]
        
        response = test_client.get("/api/knowledge/urls")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["url"] == "http://test1.com"
    
    def test_stats_endpoint(self, test_client, mock_web_scraper):
        """Test knowledge stats endpoint"""
        # Mock stored URLs for stats
        mock_urls = [
            {"chunk_count": 3},
            {"chunk_count": 2},
            {"chunk_count": 5}
        ]
        mock_web_scraper.get_stored_urls.return_value = mock_urls
        
        response = test_client.get("/api/knowledge/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_urls"] == 3
        assert data["total_chunks"] == 10  # 3 + 2 + 5


# Integration tests
class TestKnowledgeIntegration:
    """Integration tests for the complete knowledge management system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test the complete flow from scraping to search"""
        # This would be a more complex integration test
        # For now, just test that all components can be imported
        
        try:
            from external.aaf.app.services.web_scraper import WebScrapingService
            from langswarm.mcp.tools.bigquery_vector_search.main import similarity_search
            from external.aaf.app.api.knowledge import router
            
            # If we get here, all imports work
            assert True
        except ImportError as e:
            pytest.fail(f"Import error in knowledge management system: {e}")
    
    def test_mcp_tool_registration(self):
        """Test that the BigQuery MCP tool is properly registered"""
        try:
            from langswarm.mcp.tools.bigquery_vector_search.main import server
            
            # Check that server has the expected tasks
            expected_tasks = ["similarity_search", "list_datasets", "get_content", "dataset_info"]
            actual_tasks = list(server.tasks.keys())
            
            for task in expected_tasks:
                assert task in actual_tasks, f"Task {task} not found in MCP server"
            
        except ImportError as e:
            pytest.fail(f"Could not import BigQuery MCP server: {e}")
    
    def test_configuration_loading(self):
        """Test that configuration files can be loaded"""
        import yaml
        
        # Test agents.yaml
        try:
            with open('/Users/alexanderekdahl/Docker/LangSwarm/langswarm/mcp/tools/bigquery_vector_search/agents.yaml', 'r') as f:
                agents_config = yaml.safe_load(f)
            
            assert 'agents' in agents_config
            assert len(agents_config['agents']) > 0
            
            # Check for required agents
            agent_ids = [agent['id'] for agent in agents_config['agents']]
            required_agents = ['input_normalizer', 'search_intent_classifier', 'search_response_formatter']
            
            for agent_id in required_agents:
                assert agent_id in agent_ids, f"Required agent {agent_id} not found"
            
        except Exception as e:
            pytest.fail(f"Could not load agents.yaml: {e}")
        
        # Test workflows.yaml
        try:
            with open('/Users/alexanderekdahl/Docker/LangSwarm/langswarm/mcp/tools/bigquery_vector_search/workflows.yaml', 'r') as f:
                workflows_config = yaml.safe_load(f)
            
            assert 'workflows' in workflows_config
            assert len(workflows_config['workflows']) > 0
            
            # Check for main workflow
            workflow_ids = [workflow['id'] for workflow in workflows_config['workflows']]
            assert 'intelligent_search_workflow' in workflow_ids
            
        except Exception as e:
            pytest.fail(f"Could not load workflows.yaml: {e}")


if __name__ == "__main__":
    print("Running Knowledge Management System Tests...")
    print("=" * 50)
    
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
