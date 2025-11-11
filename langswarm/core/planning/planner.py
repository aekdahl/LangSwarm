"""
Planner with Pre-Planning: Brainstorm → Verify Capabilities → Generate Plan

Includes capability verification before committing to a plan to enable
early escalation if required capabilities are missing.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .models import (
    TaskBrief, Plan, ActionContract, BrainstormResult, 
    CapabilityVerification, PlanPatch, Observation, RunState
)
from ..agents.registry import get_agent_registry
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class Planner:
    """
    Plans execution with three phases:
    1. Brainstorm: Explore possible action sequences
    2. Verify: Check we have tools/agents to execute
    3. Generate: Create concrete plan with action contracts
    
    Integrates with existing LangSwarm components:
    - Agent registry for available agents
    - Tool registry for available tools
    - LLM for plan generation
    """
    
    def __init__(self, llm_provider, agent_registry=None, tool_registry=None):
        """
        Initialize planner with LLM and registries.
        
        Args:
            llm_provider: LLM for plan generation (agent instance)
            agent_registry: LangSwarm agent registry (uses global if None)
            tool_registry: LangSwarm tool registry (creates if None)
        """
        self.llm = llm_provider
        self.agents = agent_registry or get_agent_registry()
        self.tools = tool_registry or ToolRegistry()
        self.pattern_library = PatternLibrary()
        self.planning_history = []
    
    async def brainstorm_actions(self, brief: TaskBrief) -> BrainstormResult:
        """
        Step 1: Brainstorm what actions might be needed.
        
        Uses LLM to explore possible approaches without committing to specifics.
        
        Args:
            brief: Task brief with objective and constraints
            
        Returns:
            BrainstormResult with suggested actions and alternatives
        """
        logger.info(f"Brainstorming actions for objective: {brief.objective}")
        
        # Build prompt for LLM
        prompt = self._build_brainstorm_prompt(brief)
        
        try:
            # Use LLM to brainstorm
            response = await self.llm.chat(prompt)
            
            # Parse response (in production, use structured outputs)
            brainstorm = self._parse_brainstorm_response(response)
            
            logger.info(
                f"Brainstormed {len(brainstorm.suggested_actions)} potential actions"
            )
            
            return brainstorm
            
        except Exception as e:
            logger.error(f"Brainstorming failed: {e}")
            
            # Return minimal fallback
            return BrainstormResult(
                suggested_actions=[{
                    "action": "execute_task",
                    "description": brief.objective
                }],
                reasoning="Fallback to simple execution",
                alternatives=[],
                estimated_steps=1
            )
    
    async def verify_capabilities(
        self,
        brainstorm: BrainstormResult,
        brief: TaskBrief
    ) -> CapabilityVerification:
        """
        Step 2: Verify we have tools/agents to execute brainstormed actions.
        
        Checks against agent and tool registries. Identifies gaps and
        suggests workarounds or escalates if capabilities are missing.
        
        Args:
            brainstorm: Brainstormed action ideas
            brief: Original task brief
            
        Returns:
            CapabilityVerification with available/missing capabilities
        """
        logger.info("Verifying capabilities for brainstormed actions")
        
        available = {
            "agents": [],
            "tools": []
        }
        missing = []
        workarounds = []
        
        # Check each suggested action
        for action in brainstorm.suggested_actions:
            action_type = action.get("type", "agent")
            required_capability = action.get("capability", action.get("action"))
            
            if action_type == "agent":
                # Check if we have an appropriate agent
                if self._has_agent_capability(required_capability):
                    available["agents"].append(required_capability)
                else:
                    missing.append(f"Agent for: {required_capability}")
                    # Suggest workaround
                    workaround = self._suggest_agent_workaround(required_capability)
                    if workaround:
                        workarounds.append(workaround)
            
            elif action_type == "tool":
                # Check if we have the tool
                if self._has_tool_capability(required_capability):
                    available["tools"].append(required_capability)
                else:
                    missing.append(f"Tool: {required_capability}")
                    # Suggest workaround
                    workaround = self._suggest_tool_workaround(required_capability)
                    if workaround:
                        workarounds.append(workaround)
        
        # Determine if escalation is required
        escalation_required = len(missing) > 0 and len(workarounds) == 0
        verified = len(missing) == 0 or len(workarounds) > 0
        
        result = CapabilityVerification(
            verified=verified,
            available_capabilities=available,
            missing_capabilities=missing,
            suggested_workarounds=workarounds,
            escalation_required=escalation_required
        )
        
        if escalation_required:
            logger.warning(
                f"Missing capabilities without workarounds: {missing}. Escalation required."
            )
        elif missing:
            logger.info(
                f"Missing capabilities but workarounds available: {workarounds}"
            )
        else:
            logger.info("All required capabilities available")
        
        return result
    
    async def generate_plan(
        self,
        brief: TaskBrief,
        brainstorm: BrainstormResult,
        capabilities: CapabilityVerification
    ) -> Plan:
        """
        Step 3: Generate concrete plan using verified capabilities.
        
        Creates DAG of action contracts with specific agents/tools,
        inputs/outputs, pre/postconditions, and fallbacks.
        
        Args:
            brief: Original task brief
            brainstorm: Brainstormed actions
            capabilities: Verified capabilities
            
        Returns:
            Plan with concrete action contracts
        """
        logger.info("Generating concrete plan from brainstorm and capabilities")
        
        plan_id = f"{brief.metadata.get('name', 'plan')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Build prompt for plan generation
        prompt = self._build_plan_generation_prompt(brief, brainstorm, capabilities)
        
        try:
            # Use LLM to generate plan
            response = await self.llm.chat(prompt)
            
            # Parse into Plan structure
            plan = self._parse_plan_response(response, brief, plan_id)
            
            logger.info(f"Generated plan {plan_id} with {len(plan.steps)} steps")
            
            # Record in history
            self.planning_history.append({
                "plan_id": plan_id,
                "version": 0,
                "timestamp": plan.created_at,
                "num_steps": len(plan.steps)
            })
            
            return plan
            
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            
            # Return minimal fallback plan
            return self._create_fallback_plan(brief, plan_id)
    
    async def generate_patch(
        self,
        plan: Plan,
        state: RunState,
        failure: Observation
    ) -> PlanPatch:
        """
        Generate plan patch to address failure or drift.
        
        Analyzes failure context and generates minimal patch operations.
        May re-verify capabilities if new actions are needed.
        
        Args:
            plan: Current plan
            state: Current run state
            failure: Observation that triggered replan
            
        Returns:
            PlanPatch with operations to fix the issue
        """
        logger.info(f"Generating patch for plan {plan.plan_id}@v{plan.version}")
        
        # Build prompt for patch generation
        prompt = self._build_patch_prompt(plan, state, failure)
        
        try:
            # Use LLM to generate patch
            response = await self.llm.chat(prompt)
            
            # Parse into PlanPatch
            patch = self._parse_patch_response(response, plan)
            
            logger.info(f"Generated patch {patch.patch_id} with {len(patch.ops)} operations")
            
            return patch
            
        except Exception as e:
            logger.error(f"Patch generation failed: {e}")
            
            # Return minimal patch (retry with adjusted params)
            return PlanPatch(
                patch_id=str(uuid.uuid4()),
                plan_id=plan.plan_id,
                from_version=plan.version,
                to_version=plan.version + 1,
                reason=f"Fallback patch for failure: {failure.notes}",
                ops=[{
                    "op": "param_update",
                    "target": failure.action_id,
                    "params": {"retry": True}
                }]
            )
    
    def _has_agent_capability(self, capability: str) -> bool:
        """Check if an agent with this capability exists"""
        try:
            # Try to find agent
            agents = self.agents.list_agents()
            return len(agents) > 0  # Simplified check
        except:
            return False
    
    def _has_tool_capability(self, capability: str) -> bool:
        """Check if a tool with this capability exists"""
        try:
            # Try to find tool
            tool = self.tools.get_tool(capability)
            return tool is not None
        except:
            return False
    
    def _suggest_agent_workaround(self, capability: str) -> Optional[str]:
        """Suggest workaround for missing agent capability"""
        # Use a general-purpose agent as fallback
        agents = self.agents.list_agents()
        if agents:
            return f"Use general agent instead: {agents[0]}"
        return None
    
    def _suggest_tool_workaround(self, capability: str) -> Optional[str]:
        """Suggest workaround for missing tool capability"""
        # Suggest similar tools or agent-based alternative
        return f"Use agent to perform: {capability}"
    
    def _build_brainstorm_prompt(self, brief: TaskBrief) -> str:
        """Build prompt for brainstorming"""
        return f"""
Brainstorm action sequence for this task:

Objective: {brief.objective}

Inputs available: {list(brief.inputs.keys())}
Required outputs: {list(brief.required_outputs.keys())}
Constraints: {brief.constraints}

Think about:
1. What actions are needed to accomplish this?
2. What is the logical sequence?
3. What are alternative approaches?
4. How many steps approximately?

Provide your brainstorm as a list of potential actions with descriptions.
"""
    
    def _build_plan_generation_prompt(
        self,
        brief: TaskBrief,
        brainstorm: BrainstormResult,
        capabilities: CapabilityVerification
    ) -> str:
        """Build prompt for plan generation"""
        return f"""
Generate a concrete execution plan:

Objective: {brief.objective}
Brainstormed actions: {brainstorm.suggested_actions}
Available agents: {capabilities.available_capabilities.get('agents', [])}
Available tools: {capabilities.available_capabilities.get('tools', [])}

Create a step-by-step plan with:
1. Step ID and intent
2. Agent or tool to use
3. Input data needed
4. Expected outputs
5. Dependencies between steps

Provide the plan as a structured sequence.
"""
    
    def _build_patch_prompt(
        self,
        plan: Plan,
        state: RunState,
        failure: Observation
    ) -> str:
        """Build prompt for patch generation"""
        failed_step = plan.get_step(failure.action_id)
        
        return f"""
Generate a patch to fix this execution failure:

Failed step: {failed_step.intent if failed_step else failure.action_id}
Failure reason: {failure.notes}
Current state: {len(state.artifacts)} steps completed

Suggest minimal changes to fix the issue:
1. Replace step with different approach?
2. Add validation step before/after?
3. Adjust parameters?
4. Change to alternate tool/agent?

Provide patch operations.
"""
    
    def _parse_brainstorm_response(self, response: str) -> BrainstormResult:
        """Parse LLM response into BrainstormResult"""
        # Simplified parsing
        actions = []
        lines = response.split('\n')
        
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('•'):
                actions.append({
                    "action": line.strip()[1:].strip(),
                    "description": line.strip()[1:].strip()
                })
        
        return BrainstormResult(
            suggested_actions=actions if actions else [{"action": "execute", "description": response[:100]}],
            reasoning=response,
            alternatives=[],
            estimated_steps=len(actions) if actions else 1
        )
    
    def _parse_plan_response(
        self,
        response: str,
        brief: TaskBrief,
        plan_id: str
    ) -> Plan:
        """Parse LLM response into Plan"""
        # Simplified plan creation
        steps = []
        dag = {}
        
        # Create simple sequential plan
        prev_step_id = None
        for i, line in enumerate(response.split('\n')[:10]):  # Max 10 steps
            if line.strip():
                step_id = f"step_{i+1}"
                step = ActionContract(
                    id=step_id,
                    intent=line.strip(),
                    agent_or_tool="default_agent",
                    inputs={"input": brief.inputs},
                    outputs={"output": "result"}
                )
                steps.append(step)
                
                # Add dependency on previous step
                dag[step_id] = [prev_step_id] if prev_step_id else []
                prev_step_id = step_id
        
        return Plan(
            plan_id=plan_id,
            version=0,
            task_brief=brief,
            steps=steps if steps else [self._create_default_step()],
            dag=dag if dag else {"step_1": []}
        )
    
    def _parse_patch_response(self, response: str, plan: Plan) -> PlanPatch:
        """Parse LLM response into PlanPatch"""
        # Simplified patch creation
        return PlanPatch(
            patch_id=str(uuid.uuid4()),
            plan_id=plan.plan_id,
            from_version=plan.version,
            to_version=plan.version + 1,
            reason="Generated from failure analysis",
            ops=[{
                "op": "param_update",
                "target": plan.steps[0].id if plan.steps else "step_1",
                "params": {"adjusted": True}
            }]
        )
    
    def _create_default_step(self) -> ActionContract:
        """Create a default step"""
        return ActionContract(
            id="step_1",
            intent="Execute task",
            agent_or_tool="default_agent",
            inputs={"input": "data"},
            outputs={"output": "result"}
        )
    
    def _create_fallback_plan(self, brief: TaskBrief, plan_id: str) -> Plan:
        """Create minimal fallback plan"""
        return Plan(
            plan_id=plan_id,
            version=0,
            task_brief=brief,
            steps=[self._create_default_step()],
            dag={"step_1": []}
        )


class PatternLibrary:
    """Library of common workflow patterns"""
    
    def __init__(self):
        self.patterns = {
            "sequential": "Execute steps in order: A → B → C",
            "parallel": "Execute steps concurrently: (A, B, C) → merge",
            "conditional": "Branch based on condition: A → (B | C)",
            "loop": "Repeat until condition: while(test) { A → B }",
            "map-reduce": "Process in parallel then aggregate: map(A) → reduce(B)"
        }
    
    def get_pattern(self, name: str) -> Optional[str]:
        """Get pattern description"""
        return self.patterns.get(name)




