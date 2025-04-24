import pytest
from unittest.mock import MagicMock
from langswarm.core.wrappers.generic import AgentWrapper


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.identifier = "test_agent"
    return agent


def test_agent_wrapper_initialization(mock_agent):
    wrapper = AgentWrapper(
        name="test_agent",
        agent=mock_agent,
        model="gpt-4",
    )
    assert wrapper.name == "test_agent"
    assert wrapper.agent == mock_agent
    assert wrapper.model == "gpt-4"
    assert wrapper.model_details["name"] == "gpt-4"
    assert isinstance(wrapper.model_details, dict)
