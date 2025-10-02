"""
LangSwarm V2 Synapse Tool Adapter

Adapter for Synapse tools (consensus, branching, routing, voting, aggregation)
to provide V2 interface compatibility.
"""

from typing import Any, Dict, List, Optional
import logging

from ..interfaces import ToolType, ToolCapability
from ..base import ToolSchema
from .base import LegacyToolAdapter

logger = logging.getLogger(__name__)


class SynapseToolAdapter(LegacyToolAdapter):
    """
    Adapter for Synapse tools to V2 interface.
    
    Synapse tools typically have:
    - run(payload={}, action="query") method
    - Consensus, branching, routing, voting, or aggregation functionality
    - Agent-based processing
    """
    
    def __init__(self, synapse_tool: Any, **kwargs):
        # Determine tool type based on class name
        tool_type = self._determine_synapse_type(synapse_tool)
        
        super().__init__(
            legacy_tool=synapse_tool,
            tool_type=ToolType.WORKFLOW,  # Synapse tools are workflow tools
            capabilities=[
                ToolCapability.READ,
                ToolCapability.EXECUTE,
                ToolCapability.ASYNC
            ],
            **kwargs
        )
        
        self._adapter_type = "synapse"
        self._synapse_type = tool_type
        
        # Add workflow capability tag
        self.add_tag("workflow")
        self.add_tag("synapse")
        self.add_tag(tool_type)
        
        # Add Synapse-specific methods
        self._add_synapse_methods()
        
        self._logger.info(f"Adapted Synapse tool: {self.metadata.id} ({tool_type})")
    
    def _determine_synapse_type(self, tool: Any) -> str:
        """Determine the type of Synapse tool"""
        class_name = tool.__class__.__name__.lower()
        
        if 'consensus' in class_name:
            return "consensus"
        elif 'branching' in class_name:
            return "branching"
        elif 'routing' in class_name:
            return "routing"
        elif 'voting' in class_name:
            return "voting"
        elif 'aggregation' in class_name:
            return "aggregation"
        else:
            return "unknown"
    
    def _add_synapse_methods(self):
        """Add Synapse-specific method schemas"""
        # Main query method
        query_schema = ToolSchema(
            name="query",
            description=f"Execute {self._synapse_type} query with multiple agents",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Query to process through the synapse workflow"
                },
                "agents": {
                    "type": "array",
                    "description": "Optional list of agent configurations",
                    "items": {"type": "object"}
                },
                "options": {
                    "type": "object",
                    "description": "Additional workflow options"
                }
            },
            returns={
                "type": "object",
                "description": f"Results from {self._synapse_type} workflow",
                "properties": {
                    "result": {"type": "any", "description": "Primary result"},
                    "metadata": {"type": "object", "description": "Execution metadata"}
                }
            },
            required=["query"],
            examples=[
                {
                    "query": "What is the best approach for this problem?",
                    "options": {"confidence_threshold": 0.8}
                }
            ]
        )
        self._metadata.add_method(query_schema)
        
        # Help method
        help_schema = ToolSchema(
            name="help",
            description=f"Get help information for {self._synapse_type} tool",
            parameters={},
            returns={
                "type": "string",
                "description": "Help information"
            },
            required=[]
        )
        self._metadata.add_method(help_schema)
        
        # Add type-specific methods
        if self._synapse_type == "consensus":
            self._add_consensus_methods()
        elif self._synapse_type == "branching":
            self._add_branching_methods()
        elif self._synapse_type == "routing":
            self._add_routing_methods()
        elif self._synapse_type == "voting":
            self._add_voting_methods()
        elif self._synapse_type == "aggregation":
            self._add_aggregation_methods()
    
    def _add_consensus_methods(self):
        """Add consensus-specific methods"""
        consensus_schema = ToolSchema(
            name="consensus",
            description="Reach consensus among multiple agents",
            parameters={
                "query": {"type": "string", "description": "Query for consensus"},
                "agents": {"type": "array", "description": "Agent configurations"},
                "threshold": {"type": "number", "description": "Consensus threshold (0.0-1.0)", "default": 0.7}
            },
            returns={
                "type": "object",
                "description": "Consensus result",
                "properties": {
                    "consensus": {"type": "string", "description": "Agreed-upon result"},
                    "confidence": {"type": "number", "description": "Confidence score"},
                    "votes": {"type": "array", "description": "Individual agent responses"}
                }
            },
            required=["query", "agents"]
        )
        self._metadata.add_method(consensus_schema)
    
    def _add_branching_methods(self):
        """Add branching-specific methods"""
        branch_schema = ToolSchema(
            name="branch",
            description="Generate multiple diverse responses from different agents",
            parameters={
                "query": {"type": "string", "description": "Query for branching"},
                "agents": {"type": "array", "description": "Agent configurations"},
                "diversity": {"type": "number", "description": "Diversity factor", "default": 0.8}
            },
            returns={
                "type": "object",
                "description": "Branching result",
                "properties": {
                    "branches": {"type": "array", "description": "Diverse responses"},
                    "diversity_score": {"type": "number", "description": "Achieved diversity"}
                }
            },
            required=["query", "agents"]
        )
        self._metadata.add_method(branch_schema)
    
    def _add_routing_methods(self):
        """Add routing-specific methods"""
        route_schema = ToolSchema(
            name="route",
            description="Route query to appropriate agent based on routing logic",
            parameters={
                "query": {"type": "string", "description": "Query to route"},
                "agents": {"type": "object", "description": "Available agents"},
                "routing_strategy": {"type": "string", "description": "Routing strategy", "default": "auto"}
            },
            returns={
                "type": "object",
                "description": "Routing result",
                "properties": {
                    "selected_agent": {"type": "string", "description": "Selected agent ID"},
                    "response": {"type": "string", "description": "Agent response"},
                    "routing_confidence": {"type": "number", "description": "Routing confidence"}
                }
            },
            required=["query", "agents"]
        )
        self._metadata.add_method(route_schema)
    
    def _add_voting_methods(self):
        """Add voting-specific methods"""
        vote_schema = ToolSchema(
            name="vote",
            description="Collect votes from multiple agents and determine winner",
            parameters={
                "query": {"type": "string", "description": "Query for voting"},
                "options": {"type": "array", "description": "Voting options"},
                "agents": {"type": "array", "description": "Voting agents"},
                "voting_method": {"type": "string", "description": "Voting method", "default": "majority"}
            },
            returns={
                "type": "object",
                "description": "Voting result",
                "properties": {
                    "winner": {"type": "string", "description": "Winning option"},
                    "votes": {"type": "object", "description": "Vote counts"},
                    "margin": {"type": "number", "description": "Victory margin"}
                }
            },
            required=["query", "options", "agents"]
        )
        self._metadata.add_method(vote_schema)
    
    def _add_aggregation_methods(self):
        """Add aggregation-specific methods"""
        aggregate_schema = ToolSchema(
            name="aggregate",
            description="Aggregate responses from multiple agents",
            parameters={
                "query": {"type": "string", "description": "Query for aggregation"},
                "agents": {"type": "array", "description": "Agent configurations"},
                "aggregation_method": {"type": "string", "description": "Aggregation method", "default": "weighted"}
            },
            returns={
                "type": "object",
                "description": "Aggregation result",
                "properties": {
                    "aggregated_result": {"type": "string", "description": "Combined result"},
                    "individual_responses": {"type": "array", "description": "Individual responses"},
                    "weights": {"type": "object", "description": "Response weights"}
                }
            },
            required=["query", "agents"]
        )
        self._metadata.add_method(aggregate_schema)
    
    def run(self, input_data: Any = None, **kwargs) -> Any:
        """
        Execute Synapse tool with enhanced parameter handling.
        
        Synapse tools typically expect run(payload={}, action="query")
        """
        try:
            # Extract action and payload from input
            if isinstance(input_data, dict):
                action = input_data.get("action", kwargs.get("action", "query"))
                payload = input_data.get("payload", input_data.get("parameters", {}))
            else:
                action = kwargs.get("action", "query")
                payload = kwargs
                
                # If input_data is a string, treat it as a query
                if isinstance(input_data, str):
                    payload["query"] = input_data
            
            # Call the Synapse tool
            if hasattr(self._legacy_tool, 'run'):
                return self._legacy_tool.run(payload=payload, action=action)
            else:
                # Fallback to direct method call
                if hasattr(self._legacy_tool, action):
                    method = getattr(self._legacy_tool, action)
                    return method(**payload)
                else:
                    raise ValueError(f"Synapse tool does not support action: {action}")
                    
        except Exception as e:
            self._logger.error(f"Synapse tool execution failed: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check for Synapse tools"""
        base_health = super().health_check()
        
        base_health.update({
            "synapse_type": self._synapse_type,
            "workflow_capabilities": [cap.value for cap in self.metadata.capabilities],
        })
        
        # Check if Synapse tool has agents
        if hasattr(self._legacy_tool, 'consensus'):
            consensus = getattr(self._legacy_tool, 'consensus')
            if hasattr(consensus, 'clients'):
                base_health["agent_count"] = len(consensus.clients)
        elif hasattr(self._legacy_tool, 'branching'):
            branching = getattr(self._legacy_tool, 'branching')
            if hasattr(branching, 'clients'):
                base_health["agent_count"] = len(branching.clients)
        elif hasattr(self._legacy_tool, 'routing'):
            routing = getattr(self._legacy_tool, 'routing')
            if hasattr(routing, 'bots'):
                base_health["agent_count"] = len(routing.bots)
        
        return base_health
