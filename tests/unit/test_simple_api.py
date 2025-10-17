"""
Unit tests for LangSwarm simple API.

Tests the simplified API wrapper that makes basic usage easier.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import os

from langswarm import create_agent, Agent, create_workflow, load_config

class TestCreateAgent:
    """Test create_agent function."""
    
    def test_create_agent_basic(self, mock_api_key):
        """Test basic agent creation."""
        agent = create_agent(model="gpt-3.5-turbo")
        assert isinstance(agent, Agent)
        assert agent.model == "gpt-3.5-turbo"
        assert agent.provider == "openai"
    
    def test_create_agent_with_memory(self, mock_api_key):
        """Test agent creation with memory enabled."""
        agent = create_agent(model="gpt-4", memory=True)
        assert agent.memory_enabled == True
        assert agent._conversation_history == []
    
    def test_create_agent_with_tools(self, mock_api_key):
        """Test agent creation with tools."""
        tools = ["filesystem", "web_search"]
        agent = create_agent(model="gpt-3.5-turbo", tools=tools)
        assert agent.tools == tools
    
    def test_create_agent_custom_system_prompt(self, mock_api_key):
        """Test agent with custom system prompt."""
        prompt = "You are a pirate assistant. Always speak like a pirate."
        agent = create_agent(model="gpt-3.5-turbo", system_prompt=prompt)
        assert agent.system_prompt == prompt
    
    def test_create_agent_without_api_key(self):
        """Test error when API key is missing."""
        # Ensure no API key is set
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            create_agent(model="gpt-3.5-turbo")

class TestProviderDetection:
    """Test automatic provider detection from model names."""
    
    @pytest.mark.parametrize("model,expected_provider", [
        # OpenAI models
        ("gpt-3.5-turbo", "openai"),
        ("gpt-4", "openai"),
        ("gpt-4-turbo", "openai"),
        ("gpt-4o", "openai"),
        # Anthropic models
        ("claude-3-opus", "anthropic"),
        ("claude-3-sonnet", "anthropic"),
        ("claude-3-haiku", "anthropic"),
        # Google models
        ("gemini-pro", "google"),
        ("gemini-ultra", "google"),
        ("palm-2", "google"),
        # Cohere models
        ("command", "cohere"),
        ("command-light", "cohere"),
        # Mistral models
        ("mistral-tiny", "mistral"),
        ("mistral-medium", "mistral"),
        ("mixtral-8x7b", "mistral"),
        # Unknown models default to openai
        ("unknown-model", "openai"),
    ])
    def test_provider_detection(self, model, expected_provider, mock_api_key):
        """Test that providers are correctly detected from model names."""
        agent = create_agent(model=model)
        assert agent.provider == expected_provider

class TestAgentChat:
    """Test agent chat functionality."""
    
    @pytest.mark.asyncio
    async def test_chat_basic(self, mock_api_key):
        """Test basic chat functionality."""
        agent = create_agent(model="gpt-3.5-turbo")
        
        # Mock the OpenAI client
        with patch.object(agent._agent['client'].chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Hello! How can I help?"))]
            mock_response.usage = Mock(total_tokens=15)
            mock_create.return_value = mock_response
            
            response = await agent.chat("Hello!")
            assert response == "Hello! How can I help?"
            assert agent._usage_stats["request_count"] == 1
    
    @pytest.mark.asyncio
    async def test_chat_with_memory(self, mock_api_key):
        """Test chat with memory enabled."""
        agent = create_agent(model="gpt-3.5-turbo", memory=True)
        
        with patch.object(agent._agent['client'].chat.completions, 'create') as mock_create:
            # First message
            mock_response1 = Mock()
            mock_response1.choices = [Mock(message=Mock(content="Hi Alice!"))]
            mock_response1.usage = Mock(total_tokens=10)
            
            # Second message
            mock_response2 = Mock()
            mock_response2.choices = [Mock(message=Mock(content="Your name is Alice."))]
            mock_response2.usage = Mock(total_tokens=15)
            
            mock_create.side_effect = [mock_response1, mock_response2]
            
            # First interaction
            await agent.chat("My name is Alice")
            assert len(agent._conversation_history) == 2  # user + assistant
            
            # Second interaction
            response = await agent.chat("What's my name?")
            assert "Alice" in response
            assert len(agent._conversation_history) == 4  # 2 more messages

class TestCostTracking:
    """Test cost tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_usage_stats_tracking(self, mock_api_key):
        """Test that usage stats are properly tracked."""
        agent = create_agent(model="gpt-3.5-turbo", track_costs=True)
        
        with patch.object(agent._agent['client'].chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Test response"))]
            mock_response.usage = Mock(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )
            mock_create.return_value = mock_response
            
            await agent.chat("Test message")
            
            stats = agent.get_usage_stats()
            assert stats["total_tokens"] == 15
            assert stats["request_count"] == 1
            assert stats["estimated_cost"] > 0

class TestStreamingResponses:
    """Test streaming response functionality."""
    
    @pytest.mark.asyncio
    async def test_chat_stream(self, mock_api_key):
        """Test streaming chat responses."""
        agent = create_agent(model="gpt-3.5-turbo", stream=True)
        
        # Mock streaming response
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))]),
            Mock(choices=[Mock(delta=Mock(content=" there"))]),
            Mock(choices=[Mock(delta=Mock(content="!"))]),
            Mock(choices=[Mock(delta=Mock(content=None))]),
        ]
        
        with patch.object(agent._agent['client'].chat.completions, 'create') as mock_create:
            mock_create.return_value = iter(mock_chunks)
            
            chunks = []
            async for chunk in agent.chat_stream("Hi"):
                chunks.append(chunk)
            
            assert chunks == ["Hello", " there", "!"]
            assert agent._usage_stats["request_count"] == 1


class TestWorkflowCreation:
    """Test workflow creation from simple API."""
    
    def test_create_workflow_from_string(self):
        """Test creating workflow from string description."""
        workflow = create_workflow("agent1 -> agent2 -> user")
        
        assert workflow is not None
        assert hasattr(workflow, 'steps') or hasattr(workflow, 'description')
    
    def test_create_workflow_from_list(self):
        """Test creating workflow from step list."""
        steps = [
            {"agent": "gpt-3.5-turbo", "task": "analyze"},
            {"agent": "gpt-4", "task": "summarize"}
        ]
        workflow = create_workflow(steps)
        
        assert workflow is not None
        assert hasattr(workflow, 'steps')
    
    def test_create_workflow_with_conditions(self):
        """Test workflow with conditional routing."""
        steps = [
            {"agent": "gpt-3.5-turbo", "task": "analyze"},
            {"condition": "quality_score > 0.8", "then": "approve", "else": "review"}
        ]
        workflow = create_workflow(steps)
        
        assert workflow is not None


class TestConfigLoading:
    """Test configuration loading and validation."""
    
    def test_load_config_from_dict(self):
        """Test loading config from dictionary."""
        config_dict = {
            "version": "2.0",
            "agents": [{"id": "assistant", "model": "gpt-3.5-turbo"}]
        }
        
        config = load_config(config_dict)
        
        assert config is not None
        assert config["version"] == "2.0"
        assert len(config["agents"]) == 1
        # Smart defaults should be applied
        assert "memory" in config
        assert "security" in config
    
    def test_load_config_validation_enabled(self):
        """Test config validation catches errors."""
        # Invalid config - missing model
        invalid_config = {
            "version": "2.0",
            "agents": [{"id": "assistant"}]
        }
        
        with pytest.raises(ValueError) as exc_info:
            load_config(invalid_config, validate=True)
        
        error_msg = str(exc_info.value)
        assert "model" in error_msg or "provider" in error_msg
    
    def test_load_config_from_yaml_string(self):
        """Test loading config from YAML content."""
        yaml_content = """
version: "2.0"
agents:
  - id: assistant
    model: gpt-3.5-turbo
"""
        config = load_config(yaml_content, format="yaml")
        
        assert config["version"] == "2.0"
        assert len(config["agents"]) == 1
    
    @patch('builtins.open')
    def test_load_config_from_file(self, mock_open):
        """Test loading config from file path."""
        mock_open.return_value.__enter__.return_value.read.return_value = """
version: "2.0"
agents:
  - id: assistant
    model: gpt-3.5-turbo
"""
        
        config = load_config("test_config.yaml")
        
        assert config["version"] == "2.0"
        assert len(config["agents"]) == 1
        mock_open.assert_called_once_with("test_config.yaml", 'r')


class TestErrorHandling:
    """Test error handling in simple API."""
    
    def test_missing_api_key_error(self):
        """Test helpful error when API key is missing."""
        # Clear all API key env vars
        env_backup = {}
        api_key_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
        
        for var in api_key_vars:
            if var in os.environ:
                env_backup[var] = os.environ[var]
                del os.environ[var]
        
        try:
            with pytest.raises(ValueError) as exc_info:
                create_agent(model="gpt-3.5-turbo")
            
            error_msg = str(exc_info.value)
            assert "API key" in error_msg or "OPENAI_API_KEY" in error_msg
        finally:
            # Restore environment
            for var, value in env_backup.items():
                os.environ[var] = value
    
    def test_invalid_model_graceful_degradation(self):
        """Test that invalid models fall back gracefully."""
        # Should not crash, should use default provider
        agent = create_agent(model="completely-unknown-model-12345")
        assert agent.provider == "openai"  # Default fallback
    
    def test_configuration_validation_errors(self):
        """Test that config validation provides helpful errors."""
        with pytest.raises(ValueError) as exc_info:
            load_config({}, validate=True)
        
        error_msg = str(exc_info.value)
        assert "version" in error_msg or "agents" in error_msg


class TestIntegrationWithMainAPI:
    """Test that simple API integrates well with main LangSwarm API."""
    
    def test_simple_agent_is_compatible_with_main_api(self, mock_api_key):
        """Test that agents from simple API work with main API."""
        agent = create_agent(model="gpt-3.5-turbo")
        
        # Should have all expected attributes of main Agent class
        assert isinstance(agent, Agent)
        assert hasattr(agent, 'chat')
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'provider')
    
    def test_config_from_simple_api_works_with_main_config(self):
        """Test that configs from simple API work with main config system."""
        config = load_config({
            "version": "2.0",
            "agents": [{"id": "test", "model": "gpt-3.5-turbo"}]
        })
        
        # Should have all the smart defaults applied
        assert "security" in config
        assert "observability" in config
        assert "memory" in config
        assert config["security"]["api_key_validation"] == True