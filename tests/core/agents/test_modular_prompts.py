
import pytest
import os
from unittest.mock import MagicMock, patch
from langswarm.core.agents.base import BaseAgent, AgentConfiguration
from langswarm.core.agents.interfaces import ProviderType, AgentCapability

@pytest.fixture
def mock_config():
    return AgentConfiguration(
        provider=ProviderType.LITELLM,
        model="gpt-4o",
        api_key="sk-mock",
        system_prompt=None, # Explicitly None to test default construction
        tools_enabled=True # Enable tools to trigger fragments
    )

@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.validate_configuration.return_value = None
    return provider

@pytest.mark.asyncio
async def test_construct_system_prompt_default(mock_config, mock_provider):
    """Test that default prompt is constructed with all fragments when tools are enabled"""
    agent = BaseAgent("test-agent", mock_config, mock_provider)
    
    # Run construction directly (or via initialize)
    await agent._construct_system_prompt()
    
    prompt = agent.configuration.system_prompt
    
    # Verify core identity matches template
    assert "# Role & Identity" in prompt
    assert "LangSwarm framework" in prompt
    
    # Verify fragments were appended
    assert "# Clarification Capabilities" in prompt
    assert "# Error Recovery & Retries" in prompt
    assert "# Intent-Based Tool Execution" in prompt
    assert "# Cross-Workflow Communication" in prompt

@pytest.mark.asyncio
async def test_construct_system_prompt_smart_append(mock_config, mock_provider):
    """Test that custom user prompt is preserved and fragments are appended"""
    custom_prompt = "You are a specialized biology researcher."
    mock_config.system_prompt = custom_prompt
    
    agent = BaseAgent("test-agent", mock_config, mock_provider)
    await agent._construct_system_prompt()
    
    prompt = agent.configuration.system_prompt
    
    # Verify custom prompt is at the start
    assert prompt.startswith(custom_prompt)
    
    # Verify fragments were appended
    assert "# Clarification Capabilities" in prompt
    
    # Verify base template was NOT included (Smart Append only appends fragments)
    assert "# Role & Identity" not in prompt

@pytest.mark.asyncio
async def test_construct_system_prompt_no_tools(mock_config, mock_provider):
    """Test that clarification fragments are omitted if tools are disabled"""
    mock_config.tools_enabled = False
    
    agent = BaseAgent("test-agent", mock_config, mock_provider)
    await agent._construct_system_prompt()
    
    prompt = agent.configuration.system_prompt
    
    # Verify base template is present
    assert "# Role & Identity" in prompt
    
    # Verify tool-related fragments are MISSING
    assert "# Clarification Capabilities" not in prompt
    assert "# Intent-Based Tool Execution" not in prompt

@pytest.mark.asyncio
async def test_langfuse_readiness(mock_config, mock_provider):
    """
    Verify that the final constructed prompt is stored in self.configuration,
    which is where Langfuse/LiteLLM reads it from.
    """
    agent = BaseAgent("test-agent", mock_config, mock_provider)
    
    # Simulate partial initialization where prompt is built
    await agent._construct_system_prompt()
    
    # Check that configuration object is mutated in place
    assert agent.configuration.system_prompt is not None, "System prompt should be populated"
    assert len(agent.configuration.system_prompt) > 100, "System prompt should contain full content"
