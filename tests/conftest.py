"""
Pytest configuration and fixtures for LangSwarm tests.
"""
import pytest
import os
import asyncio
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

# Configure pytest for async tests
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_api_key():
    """Mock API key for testing without real credentials."""
    original = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "test-key-123"
    yield "test-key-123"
    if original:
        os.environ["OPENAI_API_KEY"] = original
    else:
        del os.environ["OPENAI_API_KEY"]

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [{
            "message": {
                "content": "This is a mock response",
                "role": "assistant"
            },
            "index": 0,
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }

@pytest.fixture
def mock_agent_responses():
    """Create a mock agent with predefined responses."""
    def _create_mock_agent(responses: List[str]):
        from langswarm.testing.helpers import MockAgent
        return MockAgent(responses)
    return _create_mock_agent

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "version": "2.0",
        "agents": [
            {
                "id": "assistant",
                "model": "gpt-3.5-turbo",
                "system_prompt": "You are a helpful assistant."
            },
            {
                "id": "researcher", 
                "model": "gpt-4",
                "system_prompt": "You research topics thoroughly."
            }
        ],
        "workflows": [
            "assistant -> user",
            "researcher -> assistant -> user"
        ]
    }

@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Create a temporary config file for testing."""
    import yaml
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_config, f)
    return config_file

@pytest.fixture
def examples_dir():
    """Path to examples directory."""
    from pathlib import Path
    return Path(__file__).parent.parent / "examples" / "simple"

# Markers for different test types
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "requires_api_key: requires real API key")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "unit: unit tests")