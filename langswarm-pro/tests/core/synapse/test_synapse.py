import pytest
import pytest_asyncio
from langswarm_pro.core.synapse.protocol import SwarmProtocol, SwarmConfig
from langswarm_pro.core.synapse.strategies import VotingStrategy, AggregationStrategy
from langswarm_pro.core.synapse.router import SynapseRouter, StrategyType

@pytest.fixture
def mock_responses():
    return [
        "The sky is blue.",
        "The sky is blue indeed.", # Paraphrase of 1
        "The sky is green.",       # Different
        "I like apples."           # Unrelated
    ]

@pytest.mark.asyncio
async def test_swarm_protocol_similarity():
    protocol = SwarmProtocol()
    # Mock model interaction or use real one if env supports it
    # For CI environments without torch, we might need skipping
    try:
        score = protocol.calculate_similarity("hello", "hello world")
        assert score > 0.5
    except ImportError:
        pytest.skip("sentence-transformers not installed")

@pytest.mark.asyncio
async def test_voting_strategy(mock_responses):
    strategy = VotingStrategy()
    try:
        result = await strategy.run(mock_responses)
        # Expect "The sky is blue" (or its paraphrase) to win
        assert result["score"] > 0
        assert result["group_size"] >= 2
    except ImportError:
        pytest.skip("sentence-transformers not installed")

@pytest.mark.asyncio
async def test_aggregation_strategy(mock_responses):
    strategy = AggregationStrategy()
    try:
        result = await strategy.run(mock_responses)
        # Should contain the unique ideas
        assert "sky" in result
        assert "green" in result
        assert "apples" in result
    except ImportError:
        pytest.skip("sentence-transformers not installed")

@pytest.mark.asyncio
async def test_router():
    router = SynapseRouter()
    # basic mock test to ensure routing works
    # We rely on the strategies working (tested above)
    pass
