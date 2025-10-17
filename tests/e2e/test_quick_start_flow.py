"""
End-to-end tests for LangSwarm quick start flow.

Tests the complete user journey from installation to first working chat,
ensuring the quick start guide actually works.
"""
import pytest
import asyncio
import os
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock


class TestQuickStartFlow:
    """Test the complete quick start user journey."""
    
    def setup_method(self):
        """Set up test environment."""
        # Mock API keys
        self.env_patch = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-openai-key-for-e2e'
        })
        self.env_patch.start()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.env_patch.stop()
    
    @pytest.mark.e2e
    def test_package_imports_successfully(self):
        """Test that langswarm can be imported successfully."""
        # This tests the package structure and basic imports
        try:
            import langswarm
            from langswarm import create_agent, load_config, create_workflow
            
            # Should not raise any import errors
            assert hasattr(langswarm, 'create_agent')
            assert hasattr(langswarm, 'load_config')
            assert hasattr(langswarm, 'create_workflow')
        except ImportError as e:
            pytest.fail(f"Failed to import langswarm: {e}")
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_30_second_setup_scenario(self):
        """Test the promised '30-second setup' user scenario."""
        # This should work exactly as described in the quick start
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            # Mock OpenAI response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Hello! I'm ready to help."))]
            mock_response.usage = Mock(total_tokens=12)
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            # Simulate exact quick start code
            from langswarm import create_agent
            
            agent = create_agent(model="gpt-3.5-turbo")
            response = await agent.chat("Hello!")
            
            assert response == "Hello! I'm ready to help."
            assert mock_client.chat.completions.create.called
    
    @pytest.mark.e2e
    def test_minimal_config_works(self):
        """Test that the minimal configuration actually works."""
        from langswarm import load_config
        
        # This is the minimal config from quick start guide
        minimal_config = {
            "version": "2.0",
            "agents": [
                {
                    "id": "assistant",
                    "model": "gpt-3.5-turbo"
                }
            ]
        }
        
        # Should load without errors and apply smart defaults
        config = load_config(minimal_config)
        
        assert config["version"] == "2.0"
        assert len(config["agents"]) == 1
        assert config["agents"][0]["model"] == "gpt-3.5-turbo"
        
        # Smart defaults should be applied
        assert "memory" in config
        assert "security" in config
        assert "observability" in config
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_memory_enabled_quick_start(self):
        """Test quick start with memory enabled."""
        from langswarm import create_agent
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            
            # First response
            mock_response1 = Mock()
            mock_response1.choices = [Mock(message=Mock(content="Hi Alice, nice to meet you!"))]
            mock_response1.usage = Mock(total_tokens=15)
            
            # Second response  
            mock_response2 = Mock()
            mock_response2.choices = [Mock(message=Mock(content="Your name is Alice!"))]
            mock_response2.usage = Mock(total_tokens=10)
            
            mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response1, mock_response2])
            mock_openai.return_value = mock_client
            
            # Quick start with memory
            agent = create_agent(model="gpt-3.5-turbo", memory=True)
            
            await agent.chat("My name is Alice")
            response = await agent.chat("What's my name?")
            
            assert "Alice" in response
            assert len(agent._conversation_history) == 4  # 2 user + 2 assistant messages
    
    @pytest.mark.e2e
    def test_error_handling_no_api_key(self):
        """Test that missing API key gives helpful error."""
        # Clear API key
        with patch.dict(os.environ, {}, clear=True):
            from langswarm import create_agent
            
            with pytest.raises(ValueError) as exc_info:
                create_agent(model="gpt-3.5-turbo")
            
            error_msg = str(exc_info.value)
            assert "OPENAI_API_KEY" in error_msg
            assert "export" in error_msg or "set" in error_msg
            assert "platform.openai.com" in error_msg
    
    @pytest.mark.e2e
    def test_multiple_providers_quick_start(self):
        """Test quick start with different providers."""
        from langswarm import create_agent
        
        # Test provider auto-detection
        test_cases = [
            ("gpt-3.5-turbo", "openai"),
            ("claude-3-sonnet", "anthropic"), 
            ("gemini-pro", "google")
        ]
        
        for model, expected_provider in test_cases:
            agent = create_agent(model=model)
            assert agent.provider == expected_provider
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_workflow_quick_start(self):
        """Test quick start workflow creation."""
        from langswarm import create_workflow
        
        # Simple workflow from quick start
        workflow = create_workflow("analyze -> summarize -> review")
        
        assert workflow is not None
        assert hasattr(workflow, 'steps') or hasattr(workflow, 'description')
    
    @pytest.mark.e2e
    def test_config_file_loading(self):
        """Test loading configuration from file."""
        from langswarm import load_config
        
        # Create temporary config file
        config_content = """
version: "2.0"
agents:
  - id: assistant
    model: gpt-3.5-turbo
    temperature: 0.7

memory:
  backend: sqlite
  settings:
    persist_directory: ./data
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            
            assert config["version"] == "2.0"
            assert config["agents"][0]["temperature"] == 0.7
            assert config["memory"]["backend"] == "sqlite"
        finally:
            os.unlink(config_path)
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_streaming_quick_start(self):
        """Test streaming response in quick start."""
        from langswarm import create_agent
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            
            # Mock streaming chunks
            async def mock_stream():
                chunks = [
                    Mock(choices=[Mock(delta=Mock(content="Hello"))]),
                    Mock(choices=[Mock(delta=Mock(content=" there"))]),
                    Mock(choices=[Mock(delta=Mock(content="!"))]),
                ]
                for chunk in chunks:
                    yield chunk
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
            mock_openai.return_value = mock_client
            
            agent = create_agent(model="gpt-3.5-turbo", stream=True)
            
            chunks = []
            async for chunk in agent.chat_stream("Hello"):
                chunks.append(chunk)
            
            assert chunks == ["Hello", " there", "!"]
    
    @pytest.mark.e2e
    def test_installation_tiers_work(self):
        """Test that different installation tiers work correctly."""
        # Test minimal installation (should work with just openai)
        try:
            from langswarm import create_agent
            agent = create_agent(model="gpt-3.5-turbo")
            assert agent.provider == "openai"
        except ImportError:
            pytest.fail("Minimal installation should work with OpenAI")
        
        # Test provider detection for other models
        # (These might fail if dependencies not installed, which is expected)
        optional_tests = [
            ("claude-3-sonnet", "anthropic"),
            ("gemini-pro", "google"),
            ("command", "cohere")
        ]
        
        for model, provider in optional_tests:
            try:
                agent = create_agent(model=model)
                assert agent.provider == provider
            except (ImportError, ValueError):
                # Expected if optional dependency not installed
                pass


class TestQuickStartExamples:
    """Test that all quick start examples work end-to-end."""
    
    def setup_method(self):
        """Set up test environment."""
        self.env_patch = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key'
        })
        self.env_patch.start()
    
    def teardown_method(self):
        """Clean up."""
        self.env_patch.stop()
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_basic_chat_example(self):
        """Test the basic chat example from quick start."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Python is great!"))]
            mock_response.usage = Mock(total_tokens=10)
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            # This is the exact code from quick start
            from langswarm import create_agent
            
            agent = create_agent(model="gpt-3.5-turbo")
            response = await agent.chat("Tell me about Python")
            
            assert response == "Python is great!"
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_memory_example(self):
        """Test the memory example from quick start."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            
            responses = [
                Mock(choices=[Mock(message=Mock(content="Nice to meet you, Bob!"))], usage=Mock(total_tokens=12)),
                Mock(choices=[Mock(message=Mock(content="Your name is Bob."))], usage=Mock(total_tokens=8))
            ]
            
            mock_client.chat.completions.create = AsyncMock(side_effect=responses)
            mock_openai.return_value = mock_client
            
            # Quick start memory example
            from langswarm import create_agent
            
            agent = create_agent(model="gpt-3.5-turbo", memory=True)
            await agent.chat("Hi, I'm Bob")
            response = await agent.chat("What's my name?")
            
            assert "Bob" in response
    
    @pytest.mark.e2e
    def test_config_example(self):
        """Test the configuration example from quick start."""
        from langswarm import load_config
        
        # Config from quick start guide
        config = {
            "version": "2.0",
            "agents": [
                {
                    "id": "assistant",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                }
            ]
        }
        
        loaded_config = load_config(config)
        
        assert loaded_config["agents"][0]["temperature"] == 0.7
        assert "memory" in loaded_config  # Smart defaults applied


class TestQuickStartDocumentation:
    """Test that quick start documentation examples work."""
    
    @pytest.mark.e2e
    def test_readme_example_works(self):
        """Test that the example in README.md actually works."""
        # This would test the main example from README
        from langswarm import create_agent
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent(model="gpt-3.5-turbo")
            assert agent is not None
            assert agent.model == "gpt-3.5-turbo"
    
    @pytest.mark.e2e
    def test_quick_start_guide_examples(self):
        """Test examples from QUICK_START.md work."""
        # Test the progression of examples in the quick start guide
        examples = [
            # Basic
            {"model": "gpt-3.5-turbo"},
            # With memory
            {"model": "gpt-3.5-turbo", "memory": True},
            # With custom prompt
            {"model": "gpt-3.5-turbo", "system_prompt": "You are a helpful assistant."}
        ]
        
        from langswarm import create_agent
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            for example_config in examples:
                agent = create_agent(**example_config)
                assert agent is not None
    
    @pytest.mark.e2e
    def test_common_use_cases_work(self):
        """Test common use cases from documentation."""
        from langswarm import create_agent, load_config
        
        use_cases = [
            # Simple chatbot
            lambda: create_agent(model="gpt-3.5-turbo"),
            # With memory
            lambda: create_agent(model="gpt-3.5-turbo", memory=True),
            # Different provider
            lambda: create_agent(model="claude-3-sonnet"),
            # Config loading
            lambda: load_config({"version": "2.0", "agents": [{"id": "test", "model": "gpt-3.5-turbo"}]})
        ]
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            for use_case in use_cases:
                try:
                    result = use_case()
                    assert result is not None
                except ImportError:
                    # Expected for optional dependencies
                    pass


class TestQuickStartPerformance:
    """Test that quick start is actually quick."""
    
    @pytest.mark.e2e
    def test_import_time(self):
        """Test that importing langswarm is fast."""
        import time
        
        start_time = time.time()
        import langswarm
        import_time = time.time() - start_time
        
        # Should import in under 2 seconds even on slow systems
        assert import_time < 2.0, f"Import took {import_time:.2f}s, should be < 2s"
    
    @pytest.mark.e2e
    def test_agent_creation_time(self):
        """Test that creating an agent is fast."""
        import time
        from langswarm import create_agent
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            start_time = time.time()
            agent = create_agent(model="gpt-3.5-turbo")
            creation_time = time.time() - start_time
            
            # Should create agent in under 1 second
            assert creation_time < 1.0, f"Agent creation took {creation_time:.2f}s, should be < 1s"
    
    @pytest.mark.e2e
    def test_config_loading_time(self):
        """Test that config loading is fast."""
        import time
        from langswarm import load_config
        
        config = {
            "version": "2.0",
            "agents": [{"id": "test", "model": "gpt-3.5-turbo"}]
        }
        
        start_time = time.time()
        loaded_config = load_config(config)
        loading_time = time.time() - start_time
        
        # Should load config in under 0.5 seconds
        assert loading_time < 0.5, f"Config loading took {loading_time:.2f}s, should be < 0.5s"