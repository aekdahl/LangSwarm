"""
Executor for Action Contracts

Executes steps using existing LangSwarm agents and tools, returning
standardized Observations with metrics.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional

from .models import ActionContract, Observation, RunState, ObservationStatus
from ..agents.registry import get_agent_registry
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class Executor:
    """
    Executes action contracts using LangSwarm infrastructure.
    
    Integrates with:
    - Existing agent registry (OpenAI, Anthropic, etc.)
    - Existing tool registry (MCP tools)
    - Existing observability system
    - Existing error handling
    """
    
    def __init__(self, agent_registry=None, tool_registry=None):
        """
        Initialize executor with registries.
        
        Args:
            agent_registry: LangSwarm agent registry (uses global if None)
            tool_registry: LangSwarm tool registry (creates if None)
        """
        self.agents = agent_registry or get_agent_registry()
        self.tools = tool_registry or ToolRegistry()
        self.execution_history = []
    
    async def execute_step(
        self, 
        step: ActionContract, 
        state: RunState
    ) -> Observation:
        """
        Execute a single step and return standardized observation.
        
        Args:
            step: Action contract defining what to execute
            state: Current run state with artifacts
            
        Returns:
            Observation with status, artifacts, metrics, quality, and policy info
        """
        start_time = time.time()
        trace_id = str(uuid.uuid4())
        
        logger.info(f"Executing step '{step.id}': {step.intent}")
        
        try:
            # Resolve input data from state artifacts
            input_data = self._resolve_inputs(step.inputs, state)
            
            # Determine if this is an agent or tool execution
            if self._is_agent(step.agent_or_tool):
                result = await self._execute_agent(
                    step.agent_or_tool, 
                    input_data, 
                    step
                )
            else:
                result = await self._execute_tool(
                    step.agent_or_tool, 
                    input_data, 
                    step
                )
            
            # Calculate metrics
            elapsed_ms = (time.time() - start_time) * 1000
            metrics = {
                "latency_ms": elapsed_ms,
                "tokens_in": result.get("tokens_in", 0),
                "tokens_out": result.get("tokens_out", 0),
                "cost_usd": result.get("cost_usd", 0.0)
            }
            
            # Extract quality metrics
            quality = {
                "confidence": result.get("confidence", 1.0),
                "error_rate": result.get("error_rate", 0.0),
                "tests": result.get("tests", {})
            }
            
            # Check for policy violations
            policy = {
                "violations": self._check_policy(result, step)
            }
            
            # Determine status
            if result.get("error"):
                status = ObservationStatus.HARD_FAIL
            elif quality.get("error_rate", 0) > 0.1:
                status = ObservationStatus.SOFT_FAIL
            else:
                status = ObservationStatus.OK
            
            # Create observation
            observation = Observation(
                action_id=step.id,
                status=status,
                artifacts=result.get("artifacts", {}),
                metrics=metrics,
                quality=quality,
                policy=policy,
                notes=result.get("notes", ""),
                trace_id=trace_id
            )
            
            # Track execution
            self.execution_history.append({
                "step_id": step.id,
                "trace_id": trace_id,
                "status": status.value,
                "latency_ms": elapsed_ms
            })
            
            return observation
            
        except Exception as e:
            logger.error(f"Step '{step.id}' failed with error: {e}")
            
            # Return failure observation
            elapsed_ms = (time.time() - start_time) * 1000
            
            return Observation(
                action_id=step.id,
                status=ObservationStatus.HARD_FAIL,
                artifacts={},
                metrics={"latency_ms": elapsed_ms, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0},
                quality={"confidence": 0.0, "error_rate": 1.0, "tests": {}},
                policy={"violations": []},
                notes=f"Execution failed: {str(e)}",
                trace_id=trace_id
            )
    
    def estimate_remaining_cost(
        self, 
        plan, 
        cursor: int
    ) -> Dict[str, float]:
        """
        Estimate cost/latency for remaining steps.
        
        Args:
            plan: Current plan
            cursor: Current step index
            
        Returns:
            Dict with usd, tokens, time_sec estimates
        """
        remaining_steps = plan.steps[cursor:]
        
        total_usd = sum(
            step.cost_estimate.get("usd", 0.0) 
            for step in remaining_steps
        )
        
        total_tokens = sum(
            step.cost_estimate.get("tokens_in", 0) + step.cost_estimate.get("tokens_out", 0)
            for step in remaining_steps
        )
        
        total_time_sec = sum(
            step.latency_budget_sec 
            for step in remaining_steps
        )
        
        return {
            "usd": total_usd,
            "tokens": total_tokens,
            "time_sec": total_time_sec
        }
    
    def _resolve_inputs(
        self, 
        input_spec: Dict[str, Any], 
        state: RunState
    ) -> Dict[str, Any]:
        """
        Resolve input data from specifications and state artifacts.
        
        Handles template references like {{ step_id.field }}
        """
        resolved = {}
        
        for key, spec in input_spec.items():
            if isinstance(spec, str) and "{{" in spec and "}}" in spec:
                # Template reference
                resolved[key] = self._resolve_template(spec, state)
            elif isinstance(spec, dict) and "from_step" in spec:
                # Reference to previous step artifact
                step_id = spec["from_step"]
                field = spec.get("field")
                if step_id in state.artifacts:
                    artifact = state.artifacts[step_id]
                    resolved[key] = artifact.get(field) if field else artifact
            else:
                # Literal value
                resolved[key] = spec
        
        return resolved
    
    def _resolve_template(self, template: str, state: RunState) -> Any:
        """
        Resolve template expression like {{ step_id.field }}
        """
        import re
        
        # Extract variable reference
        match = re.search(r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}', template)
        if not match:
            return template
        
        var_path = match.group(1)
        parts = var_path.split('.')
        
        # Resolve from state artifacts
        if parts[0] in state.artifacts:
            value = state.artifacts[parts[0]]
            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return template
            return value
        
        return template
    
    def _is_agent(self, name: str) -> bool:
        """Check if name refers to an agent"""
        try:
            agent = self.agents.get_agent(name)
            return agent is not None
        except:
            return False
    
    async def _execute_agent(
        self, 
        agent_name: str, 
        input_data: Dict[str, Any],
        step: ActionContract
    ) -> Dict[str, Any]:
        """Execute using an agent"""
        try:
            agent = self.agents.get_agent(agent_name)
            if not agent:
                raise ValueError(f"Agent '{agent_name}' not found")
            
            # Execute agent
            message = input_data.get("input", input_data.get("message", str(input_data)))
            response = await agent.chat(message)
            
            return {
                "artifacts": {"response": response, "raw_input": input_data},
                "tokens_in": getattr(agent, '_last_tokens_in', 0),
                "tokens_out": getattr(agent, '_last_tokens_out', 0),
                "cost_usd": getattr(agent, '_last_cost', 0.0),
                "confidence": 0.9,
                "notes": f"Executed agent '{agent_name}'"
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "error": str(e),
                "artifacts": {},
                "notes": f"Agent execution failed: {e}"
            }
    
    async def _execute_tool(
        self, 
        tool_name: str, 
        input_data: Dict[str, Any],
        step: ActionContract
    ) -> Dict[str, Any]:
        """Execute using a tool"""
        try:
            tool = self.tools.get_tool(tool_name)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found")
            
            # Execute tool
            result = await tool.execute(input_data)
            
            return {
                "artifacts": result if isinstance(result, dict) else {"result": result},
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
                "confidence": 1.0,
                "notes": f"Executed tool '{tool_name}'"
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "error": str(e),
                "artifacts": {},
                "notes": f"Tool execution failed: {e}"
            }
    
    def _check_policy(
        self, 
        result: Dict[str, Any], 
        step: ActionContract
    ) -> List[str]:
        """Check for policy violations"""
        violations = []
        
        # Check for destructive operations
        if step.side_effects and "destructive" in step.side_effects:
            violations.append("destructive_operation_attempted")
        
        # Check for PII exposure (placeholder)
        if "pii" in str(result.get("artifacts", {})).lower():
            logger.warning("Potential PII detected in artifacts")
        
        return violations




