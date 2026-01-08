from typing import List, Dict, Any, Union
from enum import Enum
from .protocol import SwarmConfig
from .strategies import VotingStrategy, AggregationStrategy

class StrategyType(str, Enum):
    VOTING = "voting"
    AGGREGATION = "aggregation"

class SynapseRouter:
    """
    Directs queries to the appropriate Swarm strategy.
    """
    def __init__(self, config: SwarmConfig = SwarmConfig()):
        self.config = config
        self.voting = VotingStrategy(config)
        self.aggregation = AggregationStrategy(config)

    async def route(self, strategy: StrategyType, responses: List[str]) -> Union[Dict[str, Any], str]:
        """
        Route to the selected strategy.
        """
        if strategy == StrategyType.VOTING:
            return await self.voting.run(responses)
        elif strategy == StrategyType.AGGREGATION:
            return await self.aggregation.run(responses)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
