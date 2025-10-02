"""
Enhanced Workflow Steps with Advanced Tool & Agent Integration

These steps leverage the integration components to provide sophisticated
tool and agent coordination within workflows.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone

from ..base import BaseWorkflowStep
from ..interfaces import WorkflowContext, StepResult, StepStatus, StepType
from .interfaces import (
    DiscoveryStrategy, CoordinationMode, CacheStrategy, ContextScope,
    LoadBalancingStrategy, ToolDescriptor, AgentSession, CacheEntry,
    ContextSnapshot, LoadBalancerConfig
)
from .implementations import (
    DynamicToolDiscovery, AgentCoordinator, WorkflowCache,
    ContextPreserver, LoadBalancer
)


class AdvancedAgentStep(BaseWorkflowStep):
    """Enhanced agent step with memory, coordination, and context preservation"""
    
    def __init__(
        self,
        step_id: str,
        agent_id: str,
        input_data: Union[str, Dict[str, Any], Callable],
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        # Enhanced features
        preserve_context: bool = True,
        context_scope: ContextScope = ContextScope.STEP,
        coordination_mode: CoordinationMode = CoordinationMode.SEQUENTIAL,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=StepType.AGENT,
            _name=name or f"Advanced Agent: {agent_id}",
            _description=description,
            _dependencies=dependencies or [],
            _timeout=timeout
        )
        self.agent_id = agent_id
        self.input_data = input_data
        self.preserve_context = preserve_context
        self.context_scope = context_scope
        self.coordination_mode = coordination_mode
        self.memory_config = memory_config or {}
        
        # Initialize integration components
        self._context_preserver = None
        self._agent_coordinator = None
    
    async def _get_context_preserver(self) -> ContextPreserver:
        """Get or create context preserver"""
        if not self._context_preserver:
            self._context_preserver = ContextPreserver({
                "storage_backend": "sqlite",
                "compression_enabled": True,
                "max_context_age_hours": 24
            })
            await self._context_preserver.initialize()
        return self._context_preserver
    
    async def _get_agent_coordinator(self) -> AgentCoordinator:
        """Get or create agent coordinator"""
        if not self._agent_coordinator:
            self._agent_coordinator = AgentCoordinator({
                "coordination_timeout": 300,
                "failure_retry_count": 3,
                "sync_checkpoint_interval": 60
            })
            await self._agent_coordinator.initialize()
        return self._agent_coordinator
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Execute agent with enhanced capabilities"""
        # Get integration components
        coordinator = await self._get_agent_coordinator()
        
        # Create agent session
        agent_session = await coordinator.create_session(
            agent_id=self.agent_id,
            user_id=context.variables.get("user_id"),
            workflow_id=context.workflow_id,
            coordination_mode=self.coordination_mode
        )
        
        try:
            # Restore context if enabled
            if self.preserve_context:
                await self._restore_agent_context(context, agent_session)
            
            # Resolve input data
            agent_input = await self._resolve_input_data(context)
            
            # Execute agent
            from langswarm.core.agents import get_agent
            agent = await get_agent(self.agent_id)
            
            if not agent:
                raise ValueError(f"Agent '{self.agent_id}' not found")
            
            # Execute with session context
            response = await agent.send_message(
                str(agent_input),
                session_id=agent_session.session_id
            )
            
            result = response.content
            
            # Save context if enabled
            if self.preserve_context:
                await self._save_agent_context(context, agent_session, result)
            
            return result
            
        finally:
            # Update session activity
            agent_session.update_activity()
    
    async def _resolve_input_data(self, context: WorkflowContext) -> Any:
        """Resolve input data with template support"""
        if callable(self.input_data):
            return self.input_data(context)
        elif isinstance(self.input_data, str):
            return self._resolve_template(self.input_data, context)
        else:
            return self.input_data
    
    def _resolve_template(self, template: str, context: WorkflowContext) -> str:
        """Enhanced template resolution"""
        result = template
        
        # Replace context variables: ${variable_name}
        for var_name, var_value in context.variables.items():
            result = result.replace(f"${{{var_name}}}", str(var_value))
        
        # Replace step outputs: ${step_id}
        for step_id, output in context.step_outputs.items():
            result = result.replace(f"${{{step_id}}}", str(output))
        
        return result
    
    async def _restore_agent_context(
        self,
        context: WorkflowContext,
        agent_session: AgentSession
    ) -> None:
        """Restore agent conversation context"""
        if not self.preserve_context:
            return
        
        try:
            context_preserver = await self._get_context_preserver()
            
            # Get recent context for this agent
            context_history = await context_preserver.get_context_history(
                agent_session_id=agent_session.session_id,
                limit=5
            )
            
            if context_history:
                # Merge recent contexts
                snapshot_ids = [snap.snapshot_id for snap in context_history[-3:]]
                if snapshot_ids:
                    merged_snapshot_id = await context_preserver.merge_contexts(
                        snapshot_ids=snapshot_ids,
                        merge_strategy="union"
                    )
                    
                    # Restore merged context
                    await context_preserver.restore_context(
                        snapshot_id=merged_snapshot_id,
                        merge_strategy="append"
                    )
        
        except Exception as e:
            # Context restoration is optional - don't fail the step
            context.metadata.setdefault("warnings", []).append(
                f"Failed to restore agent context: {e}"
            )
    
    async def _save_agent_context(
        self,
        context: WorkflowContext,
        agent_session: AgentSession,
        result: Any
    ) -> None:
        """Save agent conversation context"""
        if not self.preserve_context:
            return
        
        try:
            context_preserver = await self._get_context_preserver()
            
            # Prepare context data
            context_data = {
                "messages": [
                    {"role": "user", "content": str(self.input_data)},
                    {"role": "assistant", "content": str(result)}
                ],
                "variables": context.variables.copy(),
                "metadata": {
                    "step_id": self.step_id,
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Save context snapshot
            await context_preserver.save_context(
                agent_session_id=agent_session.session_id,
                workflow_execution_id=context.execution_id,
                step_id=self.step_id,
                context_data=context_data,
                scope=self.context_scope
            )
        
        except Exception as e:
            # Context saving is optional - don't fail the step
            context.metadata.setdefault("warnings", []).append(
                f"Failed to save agent context: {e}"
            )


class CachedToolStep(BaseWorkflowStep):
    """Tool step with intelligent result caching and optimization"""
    
    def __init__(
        self,
        step_id: str,
        tool_name: str,
        parameters: Union[Dict[str, Any], Callable],
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        # Caching configuration
        cache_strategy: CacheStrategy = CacheStrategy.SEMANTIC,
        cache_ttl_seconds: Optional[int] = 3600,
        similarity_threshold: float = 0.9,
        cache_tags: Optional[List[str]] = None,
        warm_cache: bool = False
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=StepType.TOOL,
            _name=name or f"Cached Tool: {tool_name}",
            _description=description,
            _dependencies=dependencies or [],
            _timeout=timeout
        )
        self.tool_name = tool_name
        self.parameters = parameters
        self.cache_strategy = cache_strategy
        self.cache_ttl_seconds = cache_ttl_seconds
        self.similarity_threshold = similarity_threshold
        self.cache_tags = cache_tags or []
        self.warm_cache = warm_cache
        
        # Initialize cache component
        self._workflow_cache = None
    
    async def _get_workflow_cache(self) -> WorkflowCache:
        """Get or create workflow cache"""
        if not self._workflow_cache:
            self._workflow_cache = WorkflowCache({
                "backend": "redis",
                "redis_url": "redis://localhost:6379",
                "default_ttl": self.cache_ttl_seconds,
                "max_cache_size": 10000,
                "enable_compression": True
            })
            await self._workflow_cache.initialize()
        return self._workflow_cache
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Execute tool with caching"""
        cache = await self._get_workflow_cache()
        
        # Resolve parameters
        tool_params = await self._resolve_parameters(context)
        
        # Check cache first
        cached_result = await cache.get_cached_result(
            tool_id=self.tool_name,
            input_data=tool_params,
            similarity_threshold=self.similarity_threshold
        )
        
        if cached_result:
            # Cache hit - update access statistics
            cached_result.update_access()
            context.metadata.setdefault("cache_hits", 0)
            context.metadata["cache_hits"] += 1
            
            return cached_result.result_data
        
        # Cache miss - execute tool
        context.metadata.setdefault("cache_misses", 0)
        context.metadata["cache_misses"] += 1
        
        # Get and execute tool
        from langswarm.tools import get_tool_registry
        registry = get_tool_registry()
        tool = registry.get_tool(self.tool_name)
        
        if not tool:
            raise ValueError(f"Tool '{self.tool_name}' not found")
        
        # Execute tool
        start_time = time.time()
        result = await tool.execution.execute("execute", tool_params)
        execution_time = time.time() - start_time
        
        # Store result in cache
        cache_key = await cache.store_result(
            tool_id=self.tool_name,
            input_data=tool_params,
            result_data=result,
            ttl_seconds=self.cache_ttl_seconds,
            tags=self.cache_tags + [f"step:{self.step_id}"]
        )
        
        # Update tool performance metrics
        context.metadata.setdefault("tool_metrics", {})
        context.metadata["tool_metrics"][self.tool_name] = {
            "execution_time": execution_time,
            "cache_key": cache_key,
            "cached": False
        }
        
        return result
    
    async def _resolve_parameters(self, context: WorkflowContext) -> Dict[str, Any]:
        """Resolve tool parameters"""
        if callable(self.parameters):
            return self.parameters(context)
        else:
            # Create a copy and resolve templates
            resolved_params = {}
            for key, value in self.parameters.items():
                if isinstance(value, str):
                    resolved_params[key] = self._resolve_template(value, context)
                else:
                    resolved_params[key] = value
            return resolved_params
    
    def _resolve_template(self, template: str, context: WorkflowContext) -> str:
        """Resolve template variables in parameter values"""
        result = template
        
        # Replace context variables
        for var_name, var_value in context.variables.items():
            result = result.replace(f"${{{var_name}}}", str(var_value))
        
        # Replace step outputs
        for step_id, output in context.step_outputs.items():
            result = result.replace(f"${{{step_id}}}", str(output))
        
        return result


class CoordinatedAgentStep(BaseWorkflowStep):
    """Step that coordinates multiple agents for collaborative execution"""
    
    def __init__(
        self,
        step_id: str,
        agent_ids: List[str],
        task_data: Union[str, Dict[str, Any], Callable],
        coordination_mode: CoordinationMode = CoordinationMode.COLLABORATIVE,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        # Coordination configuration
        distribution_strategy: str = "balanced",
        sync_checkpoints: bool = True,
        failure_recovery: str = "reassign"
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=StepType.AGENT,
            _name=name or f"Coordinated Agents: {len(agent_ids)} agents",
            _description=description,
            _dependencies=dependencies or [],
            _timeout=timeout
        )
        self.agent_ids = agent_ids
        self.task_data = task_data
        self.coordination_mode = coordination_mode
        self.distribution_strategy = distribution_strategy
        self.sync_checkpoints = sync_checkpoints
        self.failure_recovery = failure_recovery
        
        # Initialize coordinator
        self._agent_coordinator = None
    
    async def _get_agent_coordinator(self) -> AgentCoordinator:
        """Get or create agent coordinator"""
        if not self._agent_coordinator:
            self._agent_coordinator = AgentCoordinator({
                "coordination_timeout": self.timeout or 300,
                "failure_retry_count": 3,
                "sync_checkpoint_interval": 60 if self.sync_checkpoints else 0
            })
            await self._agent_coordinator.initialize()
        return self._agent_coordinator
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Execute coordinated agent collaboration"""
        coordinator = await self._get_agent_coordinator()
        
        # Create agent sessions
        agent_sessions = []
        for agent_id in self.agent_ids:
            session = await coordinator.create_session(
                agent_id=agent_id,
                user_id=context.variables.get("user_id"),
                workflow_id=context.workflow_id,
                coordination_mode=self.coordination_mode
            )
            agent_sessions.append(session)
        
        try:
            # Resolve task data
            task = await self._resolve_task_data(context)
            
            # Execute coordination based on mode
            if self.coordination_mode == CoordinationMode.PARALLEL:
                result = await self._execute_parallel(coordinator, agent_sessions, task, context)
            elif self.coordination_mode == CoordinationMode.SEQUENTIAL:
                result = await self._execute_sequential(coordinator, agent_sessions, task, context)
            elif self.coordination_mode == CoordinationMode.HIERARCHICAL:
                result = await self._execute_hierarchical(coordinator, agent_sessions, task, context)
            elif self.coordination_mode == CoordinationMode.CONSENSUS:
                result = await self._execute_consensus(coordinator, agent_sessions, task, context)
            else:  # COLLABORATIVE
                result = await self._execute_collaborative(coordinator, agent_sessions, task, context)
            
            return result
            
        except Exception as e:
            # Handle coordination failure
            for session in agent_sessions:
                await coordinator.handle_agent_failure(
                    failed_session=session,
                    recovery_strategy=self.failure_recovery
                )
            raise
    
    async def _resolve_task_data(self, context: WorkflowContext) -> Dict[str, Any]:
        """Resolve task data for agents"""
        if callable(self.task_data):
            return self.task_data(context)
        elif isinstance(self.task_data, str):
            return {"message": self._resolve_template(self.task_data, context)}
        else:
            return self.task_data
    
    def _resolve_template(self, template: str, context: WorkflowContext) -> str:
        """Resolve template variables"""
        result = template
        for var_name, var_value in context.variables.items():
            result = result.replace(f"${{{var_name}}}", str(var_value))
        for step_id, output in context.step_outputs.items():
            result = result.replace(f"${{{step_id}}}", str(output))
        return result
    
    async def _execute_parallel(
        self,
        coordinator: AgentCoordinator,
        sessions: List[AgentSession],
        task: Dict[str, Any],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Execute agents in parallel"""
        # Create work items for parallel execution
        work_items = [{"agent_session": session, "task": task} for session in sessions]
        
        # Distribute work
        work_distribution = await coordinator.distribute_work(
            work_items=work_items,
            available_sessions=sessions,
            distribution_strategy=self.distribution_strategy
        )
        
        # Execute in parallel
        tasks = []
        for session_id, assigned_work in work_distribution.items():
            for work_item in assigned_work:
                task_coro = self._execute_single_agent(
                    work_item["agent_session"],
                    work_item["task"]
                )
                tasks.append(task_coro)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        agent_results = {}
        for i, (session, result) in enumerate(zip(sessions, results)):
            if isinstance(result, Exception):
                agent_results[session.agent_id] = {"error": str(result)}
            else:
                agent_results[session.agent_id] = result
        
        return {
            "coordination_mode": "parallel",
            "agent_results": agent_results,
            "summary": self._summarize_results(agent_results)
        }
    
    async def _execute_sequential(
        self,
        coordinator: AgentCoordinator,
        sessions: List[AgentSession],
        task: Dict[str, Any],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Execute agents sequentially"""
        agent_results = {}
        accumulated_context = task.copy()
        
        for session in sessions:
            try:
                # Execute agent with accumulated context
                result = await self._execute_single_agent(session, accumulated_context)
                agent_results[session.agent_id] = result
                
                # Add result to accumulated context for next agent
                accumulated_context["previous_results"] = agent_results
                
                # Synchronization checkpoint if enabled
                if self.sync_checkpoints:
                    await coordinator.synchronize_agents(
                        sessions=[session],
                        checkpoint_data={"step": session.agent_id, "result": result}
                    )
                
            except Exception as e:
                agent_results[session.agent_id] = {"error": str(e)}
                
                # Handle failure based on recovery strategy
                if self.failure_recovery == "stop":
                    break
                # For "reassign" or "continue", keep going
        
        return {
            "coordination_mode": "sequential",
            "agent_results": agent_results,
            "final_context": accumulated_context,
            "summary": self._summarize_results(agent_results)
        }
    
    async def _execute_hierarchical(
        self,
        coordinator: AgentCoordinator,
        sessions: List[AgentSession],
        task: Dict[str, Any],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Execute agents in hierarchical master-worker pattern"""
        if not sessions:
            return {}
        
        # First agent is the master
        master_session = sessions[0]
        worker_sessions = sessions[1:]
        
        # Master breaks down the task
        master_task = {
            **task,
            "role": "master",
            "worker_count": len(worker_sessions),
            "instruction": "Break down this task for workers and coordinate their efforts"
        }
        
        master_result = await self._execute_single_agent(master_session, master_task)
        
        # Extract subtasks for workers (simplified - would need more sophisticated parsing)
        subtasks = self._extract_subtasks(master_result, len(worker_sessions))
        
        # Execute workers in parallel
        worker_tasks = []
        for i, worker_session in enumerate(worker_sessions):
            worker_task = {
                **subtasks[i] if i < len(subtasks) else task,
                "role": "worker",
                "master_instructions": master_result
            }
            worker_tasks.append(self._execute_single_agent(worker_session, worker_task))
        
        worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # Master consolidates results
        consolidation_task = {
            **task,
            "role": "master",
            "action": "consolidate",
            "worker_results": [
                result if not isinstance(result, Exception) else {"error": str(result)}
                for result in worker_results
            ]
        }
        
        final_result = await self._execute_single_agent(master_session, consolidation_task)
        
        return {
            "coordination_mode": "hierarchical",
            "master_result": master_result,
            "worker_results": worker_results,
            "final_result": final_result,
            "summary": final_result
        }
    
    async def _execute_consensus(
        self,
        coordinator: AgentCoordinator,
        sessions: List[AgentSession],
        task: Dict[str, Any],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Execute agents with consensus decision making"""
        # Each agent provides their perspective
        individual_results = []
        
        for session in sessions:
            agent_task = {
                **task,
                "instruction": "Provide your perspective on this task. Be specific about your approach and reasoning."
            }
            result = await self._execute_single_agent(session, agent_task)
            individual_results.append({
                "agent_id": session.agent_id,
                "perspective": result
            })
        
        # Consensus round - agents review all perspectives
        consensus_results = []
        
        for session in sessions:
            consensus_task = {
                **task,
                "all_perspectives": individual_results,
                "instruction": "Review all perspectives and provide a consensus view. Identify common ground and resolve differences."
            }
            result = await self._execute_single_agent(session, consensus_task)
            consensus_results.append({
                "agent_id": session.agent_id,
                "consensus_view": result
            })
        
        # Final synthesis (use first agent as synthesizer)
        if sessions:
            synthesis_task = {
                **task,
                "individual_perspectives": individual_results,
                "consensus_views": consensus_results,
                "instruction": "Synthesize all perspectives and consensus views into a final decision."
            }
            final_consensus = await self._execute_single_agent(sessions[0], synthesis_task)
        else:
            final_consensus = "No agents available for consensus"
        
        return {
            "coordination_mode": "consensus",
            "individual_perspectives": individual_results,
            "consensus_views": consensus_results,
            "final_consensus": final_consensus,
            "summary": final_consensus
        }
    
    async def _execute_collaborative(
        self,
        coordinator: AgentCoordinator,
        sessions: List[AgentSession],
        task: Dict[str, Any],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Execute agents in collaborative problem solving"""
        # Use the coordinator's collaboration method
        collaboration_result = await coordinator.coordinate_agents(
            sessions=sessions,
            task=task,
            mode=CoordinationMode.COLLABORATIVE
        )
        
        return {
            "coordination_mode": "collaborative",
            "coordination_result": collaboration_result,
            "summary": collaboration_result.get("final_result", "Collaboration completed")
        }
    
    async def _execute_single_agent(
        self,
        session: AgentSession,
        task: Dict[str, Any]
    ) -> Any:
        """Execute a single agent with task data"""
        from langswarm.core.agents import get_agent
        
        agent = await get_agent(session.agent_id)
        if not agent:
            raise ValueError(f"Agent '{session.agent_id}' not found")
        
        # Convert task to message
        if isinstance(task, dict):
            message = task.get("message", str(task))
        else:
            message = str(task)
        
        response = await agent.send_message(message, session_id=session.session_id)
        return response.content
    
    def _extract_subtasks(self, master_result: Any, worker_count: int) -> List[Dict[str, Any]]:
        """Extract subtasks from master's breakdown (simplified implementation)"""
        # This is a simplified implementation - in practice, would need
        # more sophisticated parsing of the master's response
        subtasks = []
        result_str = str(master_result)
        
        # Try to split the result into parts for workers
        lines = result_str.split('\n')
        tasks_per_worker = max(1, len(lines) // worker_count)
        
        for i in range(worker_count):
            start_idx = i * tasks_per_worker
            end_idx = min(start_idx + tasks_per_worker, len(lines))
            
            subtask_content = '\n'.join(lines[start_idx:end_idx])
            if subtask_content.strip():
                subtasks.append({"message": subtask_content})
        
        # Ensure we have enough subtasks
        while len(subtasks) < worker_count:
            subtasks.append({"message": "Assist with the main task as assigned."})
        
        return subtasks
    
    def _summarize_results(self, agent_results: Dict[str, Any]) -> str:
        """Create a summary of agent results"""
        successful_agents = [
            agent_id for agent_id, result in agent_results.items()
            if not isinstance(result, dict) or "error" not in result
        ]
        
        failed_agents = [
            agent_id for agent_id, result in agent_results.items()
            if isinstance(result, dict) and "error" in result
        ]
        
        summary = f"Coordination completed with {len(successful_agents)} successful agents"
        if failed_agents:
            summary += f" and {len(failed_agents)} failed agents"
        
        return summary


class LoadBalancedStep(BaseWorkflowStep):
    """Step that load balances execution across multiple targets"""
    
    def __init__(
        self,
        step_id: str,
        target_type: str,  # "agent" or "tool"
        target_ids: List[str],
        execution_data: Union[str, Dict[str, Any], Callable],
        load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        # Load balancing configuration
        health_check_enabled: bool = True,
        failure_threshold: int = 3,
        recovery_time: int = 60
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=StepType.TOOL if target_type == "tool" else StepType.AGENT,
            _name=name or f"Load Balanced {target_type.title()}: {len(target_ids)} targets",
            _description=description,
            _dependencies=dependencies or [],
            _timeout=timeout
        )
        self.target_type = target_type
        self.target_ids = target_ids
        self.execution_data = execution_data
        self.load_balancing_strategy = load_balancing_strategy
        self.health_check_enabled = health_check_enabled
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        
        # Initialize load balancer
        self._load_balancer = None
    
    async def _get_load_balancer(self) -> LoadBalancer:
        """Get or create load balancer"""
        if not self._load_balancer:
            config = LoadBalancerConfig(
                strategy=self.load_balancing_strategy,
                health_check_interval=30 if self.health_check_enabled else 0,
                failure_threshold=self.failure_threshold,
                recovery_time=self.recovery_time
            )
            
            self._load_balancer = LoadBalancer(config)
            await self._load_balancer.initialize()
        return self._load_balancer
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Execute with load balancing"""
        load_balancer = await self._get_load_balancer()
        
        # Resolve execution data
        exec_data = await self._resolve_execution_data(context)
        
        # Select target using load balancing
        request_context = {
            "step_id": self.step_id,
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "data_size": len(str(exec_data)),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        selected_target = await load_balancer.select_target(
            targets=self.target_ids,
            request_context=request_context
        )
        
        if not selected_target:
            raise ValueError("No healthy targets available for load balancing")
        
        try:
            # Execute on selected target
            start_time = time.time()
            
            if self.target_type == "agent":
                result = await self._execute_agent(selected_target, exec_data, context)
            else:  # tool
                result = await self._execute_tool(selected_target, exec_data, context)
            
            execution_time = time.time() - start_time
            
            # Update target health (successful execution)
            await load_balancer.update_target_health(
                target_id=selected_target,
                health_score=1.0,
                performance_metrics={
                    "execution_time": execution_time,
                    "success": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Store load balancing metrics in context
            context.metadata.setdefault("load_balancing", {})
            context.metadata["load_balancing"][self.step_id] = {
                "selected_target": selected_target,
                "execution_time": execution_time,
                "strategy": self.load_balancing_strategy.value,
                "success": True
            }
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Update target health (failed execution)
            await load_balancer.update_target_health(
                target_id=selected_target,
                health_score=0.0,
                performance_metrics={
                    "execution_time": execution_time,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Store failure metrics
            context.metadata.setdefault("load_balancing", {})
            context.metadata["load_balancing"][self.step_id] = {
                "selected_target": selected_target,
                "execution_time": execution_time,
                "strategy": self.load_balancing_strategy.value,
                "success": False,
                "error": str(e)
            }
            
            raise
    
    async def _resolve_execution_data(self, context: WorkflowContext) -> Any:
        """Resolve execution data"""
        if callable(self.execution_data):
            return self.execution_data(context)
        elif isinstance(self.execution_data, str):
            return self._resolve_template(self.execution_data, context)
        else:
            return self.execution_data
    
    def _resolve_template(self, template: str, context: WorkflowContext) -> str:
        """Resolve template variables"""
        result = template
        for var_name, var_value in context.variables.items():
            result = result.replace(f"${{{var_name}}}", str(var_value))
        for step_id, output in context.step_outputs.items():
            result = result.replace(f"${{{step_id}}}", str(output))
        return result
    
    async def _execute_agent(
        self,
        agent_id: str,
        exec_data: Any,
        context: WorkflowContext
    ) -> Any:
        """Execute agent with load balancing"""
        from langswarm.core.agents import get_agent
        
        agent = await get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found")
        
        message = str(exec_data)
        response = await agent.send_message(message)
        return response.content
    
    async def _execute_tool(
        self,
        tool_name: str,
        exec_data: Any,
        context: WorkflowContext
    ) -> Any:
        """Execute tool with load balancing"""
        from langswarm.tools import get_tool_registry
        
        registry = get_tool_registry()
        tool = registry.get_tool(tool_name)
        
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Convert exec_data to tool parameters
        if isinstance(exec_data, dict):
            params = exec_data
        else:
            params = {"input": exec_data}
        
        result = await tool.execution.execute("execute", params)
        return result


class ContextAwareStep(BaseWorkflowStep):
    """Step that maintains and utilizes context across workflow execution"""
    
    def __init__(
        self,
        step_id: str,
        step_type: StepType,
        execution_logic: Callable[[WorkflowContext], Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        # Context configuration
        context_scope: ContextScope = ContextScope.WORKFLOW,
        preserve_history: bool = True,
        context_compression: bool = True,
        max_context_age_hours: int = 24
    ):
        super().__init__(
            _step_id=step_id,
            _step_type=step_type,
            _name=name or f"Context Aware Step: {step_id}",
            _description=description,
            _dependencies=dependencies or [],
            _timeout=timeout
        )
        self.execution_logic = execution_logic
        self.context_scope = context_scope
        self.preserve_history = preserve_history
        self.context_compression = context_compression
        self.max_context_age_hours = max_context_age_hours
        
        # Initialize context preserver
        self._context_preserver = None
    
    async def _get_context_preserver(self) -> ContextPreserver:
        """Get or create context preserver"""
        if not self._context_preserver:
            self._context_preserver = ContextPreserver({
                "storage_backend": "sqlite",
                "compression_enabled": self.context_compression,
                "max_context_age_hours": self.max_context_age_hours
            })
            await self._context_preserver.initialize()
        return self._context_preserver
    
    async def _execute_impl(self, context: WorkflowContext) -> Any:
        """Execute with context awareness"""
        # Restore context if enabled
        if self.preserve_history:
            await self._restore_context(context)
        
        # Execute the step logic with enhanced context
        result = await self._execute_with_context(context)
        
        # Save context if enabled
        if self.preserve_history:
            await self._save_context(context, result)
        
        return result
    
    async def _execute_with_context(self, context: WorkflowContext) -> Any:
        """Execute step logic with context support"""
        if asyncio.iscoroutinefunction(self.execution_logic):
            return await self.execution_logic(context)
        else:
            return self.execution_logic(context)
    
    async def _restore_context(self, context: WorkflowContext) -> None:
        """Restore previous context"""
        try:
            context_preserver = await self._get_context_preserver()
            
            # Create a unique session ID for this workflow execution
            session_id = f"{context.workflow_id}_{context.execution_id}"
            
            # Get recent context history
            context_history = await context_preserver.get_context_history(
                agent_session_id=session_id,
                limit=10
            )
            
            if context_history:
                # Merge recent contexts into current context
                for snapshot in context_history[-3:]:  # Use last 3 snapshots
                    # Merge variables (newer values take precedence)
                    context.variables.update(snapshot.variables)
                    
                    # Add historical metadata
                    context.metadata.setdefault("context_history", []).append({
                        "snapshot_id": snapshot.snapshot_id,
                        "created_at": snapshot.created_at.isoformat(),
                        "scope": snapshot.scope.value,
                        "completeness_score": snapshot.completeness_score
                    })
        
        except Exception as e:
            # Context restoration is optional - don't fail the step
            context.metadata.setdefault("warnings", []).append(
                f"Failed to restore context: {e}"
            )
    
    async def _save_context(self, context: WorkflowContext, result: Any) -> None:
        """Save current context"""
        try:
            context_preserver = await self._get_context_preserver()
            
            # Create session ID for this workflow execution
            session_id = f"{context.workflow_id}_{context.execution_id}"
            
            # Prepare context data
            context_data = {
                "variables": context.variables.copy(),
                "step_outputs": context.step_outputs.copy(),
                "metadata": context.metadata.copy(),
                "current_step": {
                    "step_id": self.step_id,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Save context snapshot
            snapshot_id = await context_preserver.save_context(
                agent_session_id=session_id,
                workflow_execution_id=context.execution_id,
                step_id=self.step_id,
                context_data=context_data,
                scope=self.context_scope
            )
            
            # Add snapshot ID to context for reference
            context.metadata.setdefault("context_snapshots", []).append({
                "step_id": self.step_id,
                "snapshot_id": snapshot_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        except Exception as e:
            # Context saving is optional - don't fail the step
            context.metadata.setdefault("warnings", []).append(
                f"Failed to save context: {e}"
            )