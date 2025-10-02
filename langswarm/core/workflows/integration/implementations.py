"""
Advanced Tool & Agent Integration Implementations for V2 Workflows

Concrete implementations providing enhanced integration capabilities.
"""

import asyncio
import hashlib
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, Set

from .interfaces import (
    IToolDiscovery, IAgentCoordinator, IWorkflowCache, IContextPreserver, ILoadBalancer,
    ToolDescriptor, AgentSession, CacheEntry, ContextSnapshot, LoadBalancerConfig,
    DiscoveryStrategy, CoordinationMode, CacheStrategy, ContextScope, LoadBalancingStrategy,
    ToolDiscoveryEvent, AgentCoordinationEvent, CacheEvent, ContextEvent, LoadBalancingEvent
)

from ..interfaces import WorkflowContext, StepResult
from ...error import V2Error, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class DynamicToolDiscovery(IToolDiscovery):
    """
    Dynamic tool discovery and integration system
    """
    
    def __init__(self):
        self._registered_tools: Dict[str, ToolDescriptor] = {}
        self._capability_index: Dict[str, Set[str]] = defaultdict(set)
        self._discovery_stats = {
            "tools_discovered": 0,
            "discovery_requests": 0,
            "cache_hits": 0,
            "avg_discovery_time": 0.0
        }
        self._discovery_cache: Dict[str, List[ToolDescriptor]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_cleanup = time.time()
    
    async def discover_tools(
        self,
        context: WorkflowContext,
        required_capabilities: Optional[List[str]] = None,
        strategy: DiscoveryStrategy = DiscoveryStrategy.AUTOMATIC
    ) -> List[ToolDescriptor]:
        """Discover tools based on workflow context and requirements"""
        start_time = time.time()
        self._discovery_stats["discovery_requests"] += 1
        
        # Create cache key
        cache_key = self._create_discovery_cache_key(context, required_capabilities, strategy)
        
        # Check cache first
        cached_result = self._get_cached_discovery(cache_key)
        if cached_result:
            self._discovery_stats["cache_hits"] += 1
            return cached_result
        
        discovered_tools = []
        
        try:
            if strategy == DiscoveryStrategy.AUTOMATIC:
                discovered_tools = await self._automatic_discovery(context, required_capabilities)
            elif strategy == DiscoveryStrategy.ON_DEMAND:
                discovered_tools = await self._on_demand_discovery(required_capabilities)
            elif strategy == DiscoveryStrategy.PRE_LOADED:
                discovered_tools = await self._pre_loaded_discovery()
            elif strategy == DiscoveryStrategy.ADAPTIVE:
                discovered_tools = await self._adaptive_discovery(context, required_capabilities)
            elif strategy == DiscoveryStrategy.SEMANTIC:
                discovered_tools = await self._semantic_discovery(context, required_capabilities)
            
            # Update cache
            self._cache_discovery_result(cache_key, discovered_tools)
            
            # Update stats
            discovery_time = time.time() - start_time
            self._update_discovery_stats(discovery_time, len(discovered_tools))
            
            logger.info(f"Discovered {len(discovered_tools)} tools using {strategy.value} strategy in {discovery_time:.3f}s")
            
            return discovered_tools
            
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            raise V2Error(
                f"Tool discovery failed with strategy {strategy.value}",
                category=ErrorCategory.WORKFLOW,
                severity=ErrorSeverity.MEDIUM,
                details={"strategy": strategy.value, "error": str(e)}
            )
    
    async def _automatic_discovery(
        self,
        context: WorkflowContext,
        required_capabilities: Optional[List[str]]
    ) -> List[ToolDescriptor]:
        """Automatic discovery based on context analysis"""
        discovered = []
        
        # Analyze context for hints about needed tools
        context_keywords = self._extract_keywords_from_context(context)
        
        # Find tools matching context keywords
        for tool_id, tool_descriptor in self._registered_tools.items():
            if self._matches_context_keywords(tool_descriptor, context_keywords):
                discovered.append(tool_descriptor)
        
        # Add tools matching required capabilities
        if required_capabilities:
            capability_tools = await self._find_tools_by_capabilities(required_capabilities)
            discovered.extend([t for t in capability_tools if t not in discovered])
        
        # Score and sort by relevance
        scored_tools = [(tool, self._calculate_relevance_score(tool, context)) for tool in discovered]
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        
        return [tool for tool, score in scored_tools[:20]]  # Top 20 most relevant
    
    async def _on_demand_discovery(
        self,
        required_capabilities: Optional[List[str]]
    ) -> List[ToolDescriptor]:
        """On-demand discovery for specific capabilities"""
        if not required_capabilities:
            return list(self._registered_tools.values())
        
        return await self._find_tools_by_capabilities(required_capabilities)
    
    async def _pre_loaded_discovery(self) -> List[ToolDescriptor]:
        """Pre-loaded tools discovery"""
        # Return all registered tools marked as pre-loaded
        pre_loaded = [
            tool for tool in self._registered_tools.values()
            if tool.metadata.get('pre_loaded', False)
        ]
        
        if not pre_loaded:
            # If no pre-loaded tools, return top-performing tools
            sorted_tools = sorted(
                self._registered_tools.values(),
                key=lambda t: (t.success_rate, -t.avg_execution_time or 0),
                reverse=True
            )
            pre_loaded = sorted_tools[:10]  # Top 10 performing tools
        
        return pre_loaded
    
    async def _adaptive_discovery(
        self,
        context: WorkflowContext,
        required_capabilities: Optional[List[str]]
    ) -> List[ToolDescriptor]:
        """Adaptive discovery using ML-like approach"""
        # Simple adaptive logic - in production would use ML models
        discovered = []
        
        # Get usage patterns from context metadata
        usage_patterns = context.metadata.get('tool_usage_patterns', {})
        
        # Score tools based on historical usage and context
        for tool_id, tool_descriptor in self._registered_tools.items():
            score = 0.0
            
            # Historical usage score
            if tool_id in usage_patterns:
                score += usage_patterns[tool_id] * 0.4
            
            # Performance score
            score += tool_descriptor.success_rate * 0.3
            
            # Capability match score
            if required_capabilities:
                matched_caps = set(tool_descriptor.capabilities) & set(required_capabilities)
                score += (len(matched_caps) / len(required_capabilities)) * 0.3
            
            if score > 0.3:  # Minimum threshold
                discovered.append((tool_descriptor, score))
        
        # Sort by score and return top tools
        discovered.sort(key=lambda x: x[1], reverse=True)
        return [tool for tool, score in discovered[:15]]
    
    async def _semantic_discovery(
        self,
        context: WorkflowContext,
        required_capabilities: Optional[List[str]]
    ) -> List[ToolDescriptor]:
        """Semantic discovery based on tool descriptions and context"""
        # In production, would use embeddings and semantic similarity
        # For now, use keyword matching with enhanced scoring
        
        context_text = self._extract_text_from_context(context)
        context_words = set(context_text.lower().split())
        
        if required_capabilities:
            context_words.update(cap.lower() for cap in required_capabilities)
        
        semantic_matches = []
        
        for tool_descriptor in self._registered_tools.values():
            # Create tool text for semantic matching
            tool_text = f"{tool_descriptor.tool_name} {tool_descriptor.metadata.get('description', '')}"
            tool_text += " " + " ".join(tool_descriptor.capabilities)
            tool_words = set(tool_text.lower().split())
            
            # Calculate semantic similarity (Jaccard similarity)
            intersection = len(context_words & tool_words)
            union = len(context_words | tool_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.1:  # Minimum similarity threshold
                semantic_matches.append((tool_descriptor, similarity))
        
        # Sort by similarity and return top matches
        semantic_matches.sort(key=lambda x: x[1], reverse=True)
        return [tool for tool, similarity in semantic_matches[:12]]
    
    def _extract_keywords_from_context(self, context: WorkflowContext) -> List[str]:
        """Extract keywords from workflow context"""
        keywords = []
        
        # Extract from variable names and values
        for key, value in context.variables.items():
            keywords.append(key)
            if isinstance(value, str):
                keywords.extend(value.split())
        
        # Extract from step outputs
        for key, value in context.step_outputs.items():
            keywords.append(key)
            if isinstance(value, dict):
                keywords.extend(str(v).split() for v in value.values() if isinstance(v, str))
        
        return [k.lower() for k in keywords if len(k) > 2]
    
    def _extract_text_from_context(self, context: WorkflowContext) -> str:
        """Extract all text content from context"""
        text_parts = []
        
        # Add variable values as text
        for value in context.variables.values():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, (dict, list)):
                text_parts.append(json.dumps(value, default=str))
        
        # Add metadata text
        for value in context.metadata.values():
            if isinstance(value, str):
                text_parts.append(value)
        
        return " ".join(text_parts)
    
    def _matches_context_keywords(self, tool_descriptor: ToolDescriptor, keywords: List[str]) -> bool:
        """Check if tool matches context keywords"""
        tool_text = (tool_descriptor.tool_name + " " + 
                    " ".join(tool_descriptor.capabilities) + " " +
                    tool_descriptor.metadata.get('description', '')).lower()
        
        matches = sum(1 for keyword in keywords if keyword in tool_text)
        return matches >= max(1, len(keywords) * 0.2)  # At least 20% keyword match
    
    def _calculate_relevance_score(self, tool_descriptor: ToolDescriptor, context: WorkflowContext) -> float:
        """Calculate tool relevance score for context"""
        score = 0.0
        
        # Base score from tool performance
        score += tool_descriptor.success_rate * 0.3
        score += (1 - (tool_descriptor.avg_execution_time or 1) / 10) * 0.2  # Prefer faster tools
        score += tool_descriptor.confidence_score * 0.2
        
        # Context-specific scoring
        keywords = self._extract_keywords_from_context(context)
        keyword_matches = sum(1 for keyword in keywords 
                             if keyword in tool_descriptor.tool_name.lower() or 
                             any(keyword in cap.lower() for cap in tool_descriptor.capabilities))
        
        if keywords:
            score += (keyword_matches / len(keywords)) * 0.3
        
        return min(score, 1.0)
    
    async def _find_tools_by_capabilities(self, capabilities: List[str]) -> List[ToolDescriptor]:
        """Find tools matching specific capabilities"""
        matching_tools = []
        
        for capability in capabilities:
            if capability in self._capability_index:
                tool_ids = self._capability_index[capability]
                for tool_id in tool_ids:
                    if tool_id in self._registered_tools:
                        tool = self._registered_tools[tool_id]
                        if tool not in matching_tools:
                            matching_tools.append(tool)
        
        return matching_tools
    
    def _create_discovery_cache_key(
        self,
        context: WorkflowContext,
        capabilities: Optional[List[str]],
        strategy: DiscoveryStrategy
    ) -> str:
        """Create cache key for discovery request"""
        key_parts = [
            context.workflow_id,
            str(sorted(capabilities or [])),
            strategy.value,
            str(sorted(context.variables.keys()))
        ]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()
    
    def _get_cached_discovery(self, cache_key: str) -> Optional[List[ToolDescriptor]]:
        """Get cached discovery result"""
        self._cleanup_cache_if_needed()
        
        if cache_key in self._discovery_cache:
            return self._discovery_cache[cache_key]
        return None
    
    def _cache_discovery_result(self, cache_key: str, tools: List[ToolDescriptor]):
        """Cache discovery result"""
        self._discovery_cache[cache_key] = tools
    
    def _cleanup_cache_if_needed(self):
        """Cleanup expired cache entries"""
        current_time = time.time()
        if current_time - self._last_cache_cleanup > self._cache_ttl:
            # Simple cleanup - in production would track timestamps
            if len(self._discovery_cache) > 100:  # Max cache size
                # Remove oldest 50% of entries
                keys_to_remove = list(self._discovery_cache.keys())[:len(self._discovery_cache) // 2]
                for key in keys_to_remove:
                    del self._discovery_cache[key]
            
            self._last_cache_cleanup = current_time
    
    def _update_discovery_stats(self, discovery_time: float, tools_found: int):
        """Update discovery statistics"""
        self._discovery_stats["tools_discovered"] += tools_found
        
        # Update rolling average
        current_avg = self._discovery_stats["avg_discovery_time"]
        request_count = self._discovery_stats["discovery_requests"]
        new_avg = (current_avg * (request_count - 1) + discovery_time) / request_count
        self._discovery_stats["avg_discovery_time"] = new_avg
    
    async def register_tool(self, tool_descriptor: ToolDescriptor) -> bool:
        """Register a discovered tool"""
        try:
            self._registered_tools[tool_descriptor.tool_id] = tool_descriptor
            
            # Update capability index
            for capability in tool_descriptor.capabilities:
                self._capability_index[capability].add(tool_descriptor.tool_id)
            
            logger.info(f"Registered tool {tool_descriptor.tool_id} with {len(tool_descriptor.capabilities)} capabilities")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool {tool_descriptor.tool_id}: {e}")
            return False
    
    async def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool"""
        try:
            if tool_id not in self._registered_tools:
                return False
            
            tool_descriptor = self._registered_tools[tool_id]
            
            # Remove from capability index
            for capability in tool_descriptor.capabilities:
                self._capability_index[capability].discard(tool_id)
            
            # Remove from registered tools
            del self._registered_tools[tool_id]
            
            # Clear related cache entries
            cache_keys_to_remove = [k for k in self._discovery_cache.keys() 
                                  if tool_id in str(self._discovery_cache[k])]
            for key in cache_keys_to_remove:
                del self._discovery_cache[key]
            
            logger.info(f"Unregistered tool {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_id}: {e}")
            return False
    
    async def get_tool_descriptor(self, tool_id: str) -> Optional[ToolDescriptor]:
        """Get tool descriptor by ID"""
        return self._registered_tools.get(tool_id)
    
    async def find_tools_by_capability(self, capability: str) -> List[ToolDescriptor]:
        """Find tools that provide specific capability"""
        if capability not in self._capability_index:
            return []
        
        tool_ids = self._capability_index[capability]
        return [self._registered_tools[tool_id] for tool_id in tool_ids 
                if tool_id in self._registered_tools]
    
    async def update_tool_metrics(
        self,
        tool_id: str,
        execution_time: float,
        success: bool,
        resource_usage: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update tool performance metrics"""
        if tool_id not in self._registered_tools:
            return False
        
        tool_descriptor = self._registered_tools[tool_id]
        
        # Update execution time (rolling average)
        if tool_descriptor.avg_execution_time is None:
            tool_descriptor.avg_execution_time = execution_time
        else:
            # Simple rolling average - in production would track more samples
            tool_descriptor.avg_execution_time = (
                tool_descriptor.avg_execution_time * 0.8 + execution_time * 0.2
            )
        
        # Update success rate (rolling average)
        success_value = 1.0 if success else 0.0
        tool_descriptor.success_rate = (
            tool_descriptor.success_rate * 0.9 + success_value * 0.1
        )
        
        # Update resource requirements
        if resource_usage:
            tool_descriptor.resource_requirements.update(resource_usage)
        
        # Update health status
        if tool_descriptor.success_rate < 0.5:
            tool_descriptor.health_status = "unhealthy"
        elif tool_descriptor.success_rate < 0.8:
            tool_descriptor.health_status = "degraded"
        else:
            tool_descriptor.health_status = "healthy"
        
        return True
    
    async def get_discovery_metrics(self) -> Dict[str, Any]:
        """Get tool discovery performance metrics"""
        return {
            **self._discovery_stats,
            "registered_tools": len(self._registered_tools),
            "capability_index_size": len(self._capability_index),
            "cache_size": len(self._discovery_cache),
            "healthy_tools": len([t for t in self._registered_tools.values() 
                                if t.health_status == "healthy"]),
            "cache_hit_rate": (self._discovery_stats["cache_hits"] / 
                             max(self._discovery_stats["discovery_requests"], 1))
        }


class AgentCoordinator(IAgentCoordinator):
    """
    Agent workflow orchestration and coordination system
    """
    
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}
        self._coordination_groups: Dict[str, List[str]] = {}  # workflow_id -> session_ids
        self._coordination_stats = {
            "sessions_created": 0,
            "coordination_requests": 0,
            "successful_coordinations": 0,
            "failed_coordinations": 0
        }
        self._task_queue = asyncio.Queue()
        self._coordination_lock = asyncio.Lock()
    
    async def create_session(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        coordination_mode: CoordinationMode = CoordinationMode.SEQUENTIAL
    ) -> AgentSession:
        """Create a new agent session for workflow coordination"""
        session = AgentSession(
            agent_id=agent_id,
            user_id=user_id,
            workflow_id=workflow_id
        )
        session.coordination_role = coordination_mode.value
        
        self._sessions[session.session_id] = session
        
        # Add to coordination group if workflow specified
        if workflow_id:
            if workflow_id not in self._coordination_groups:
                self._coordination_groups[workflow_id] = []
            self._coordination_groups[workflow_id].append(session.session_id)
        
        self._coordination_stats["sessions_created"] += 1
        
        logger.info(f"Created agent session {session.session_id} for agent {agent_id}")
        return session
    
    async def coordinate_agents(
        self,
        sessions: List[AgentSession],
        task: Dict[str, Any],
        mode: CoordinationMode = CoordinationMode.COLLABORATIVE
    ) -> Dict[str, Any]:
        """Coordinate multiple agents for a task"""
        async with self._coordination_lock:
            self._coordination_stats["coordination_requests"] += 1
            
            try:
                if mode == CoordinationMode.SEQUENTIAL:
                    result = await self._sequential_coordination(sessions, task)
                elif mode == CoordinationMode.PARALLEL:
                    result = await self._parallel_coordination(sessions, task)
                elif mode == CoordinationMode.HIERARCHICAL:
                    result = await self._hierarchical_coordination(sessions, task)
                elif mode == CoordinationMode.CONSENSUS:
                    result = await self._consensus_coordination(sessions, task)
                elif mode == CoordinationMode.COLLABORATIVE:
                    result = await self._collaborative_coordination(sessions, task)
                else:
                    raise ValueError(f"Unknown coordination mode: {mode}")
                
                self._coordination_stats["successful_coordinations"] += 1
                return result
                
            except Exception as e:
                self._coordination_stats["failed_coordinations"] += 1
                logger.error(f"Agent coordination failed: {e}")
                raise V2Error(
                    f"Agent coordination failed with mode {mode.value}",
                    category=ErrorCategory.WORKFLOW,
                    severity=ErrorSeverity.HIGH,
                    details={"mode": mode.value, "session_count": len(sessions), "error": str(e)}
                )
    
    async def _sequential_coordination(
        self,
        sessions: List[AgentSession],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sequential coordination - agents execute one after another"""
        results = []
        accumulated_context = task.copy()
        
        for i, session in enumerate(sessions):
            session.update_activity()
            
            # Pass accumulated context to next agent
            agent_task = {
                **accumulated_context,
                "agent_role": f"agent_{i}",
                "previous_results": results
            }
            
            # Simulate agent execution
            agent_result = await self._execute_agent_task(session, agent_task)
            results.append(agent_result)
            
            # Update accumulated context with agent result
            if isinstance(agent_result, dict):
                accumulated_context.update(agent_result)
        
        return {
            "coordination_mode": "sequential",
            "results": results,
            "final_context": accumulated_context,
            "sessions_involved": [s.session_id for s in sessions]
        }
    
    async def _parallel_coordination(
        self,
        sessions: List[AgentSession],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parallel coordination - all agents execute simultaneously"""
        # Create tasks for all agents
        agent_tasks = []
        for i, session in enumerate(sessions):
            session.update_activity()
            agent_task = {
                **task,
                "agent_role": f"agent_{i}",
                "parallel_execution": True
            }
            agent_tasks.append(self._execute_agent_task(session, agent_task))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({"session_id": sessions[i].session_id, "error": str(result)})
            else:
                successful_results.append(result)
        
        return {
            "coordination_mode": "parallel",
            "successful_results": successful_results,
            "failed_results": failed_results,
            "total_agents": len(sessions),
            "successful_count": len(successful_results)
        }
    
    async def _hierarchical_coordination(
        self,
        sessions: List[AgentSession],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Hierarchical coordination - master-worker pattern"""
        if not sessions:
            return {"coordination_mode": "hierarchical", "error": "No sessions provided"}
        
        # First agent becomes the master
        master_session = sessions[0]
        worker_sessions = sessions[1:]
        
        # Master plans the work distribution
        master_task = {
            **task,
            "role": "master",
            "worker_count": len(worker_sessions),
            "coordination_request": "plan_work_distribution"
        }
        
        master_plan = await self._execute_agent_task(master_session, master_task)
        
        # Distribute work to workers based on master's plan
        worker_tasks = self._create_worker_tasks_from_plan(master_plan, worker_sessions)
        worker_results = await asyncio.gather(
            *[self._execute_agent_task(session, task) 
              for session, task in zip(worker_sessions, worker_tasks)],
            return_exceptions=True
        )
        
        # Master consolidates results
        consolidation_task = {
            **task,
            "role": "master",
            "coordination_request": "consolidate_results",
            "worker_results": worker_results
        }
        
        final_result = await self._execute_agent_task(master_session, consolidation_task)
        
        return {
            "coordination_mode": "hierarchical",
            "master_session": master_session.session_id,
            "worker_sessions": [s.session_id for s in worker_sessions],
            "master_plan": master_plan,
            "worker_results": worker_results,
            "final_result": final_result
        }
    
    async def _consensus_coordination(
        self,
        sessions: List[AgentSession],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Consensus coordination - agents reach agreement"""
        max_rounds = 3  # Maximum consensus rounds
        consensus_threshold = 0.7  # 70% agreement threshold
        
        current_proposals = []
        
        # Initial round - all agents make proposals
        for session in sessions:
            session.update_activity()
            proposal_task = {
                **task,
                "coordination_request": "make_proposal",
                "round": 0
            }
            proposal = await self._execute_agent_task(session, proposal_task)
            current_proposals.append({"session_id": session.session_id, "proposal": proposal})
        
        # Consensus rounds
        for round_num in range(1, max_rounds + 1):
            # Each agent reviews all proposals and votes/updates
            votes_and_updates = []
            
            for session in sessions:
                vote_task = {
                    **task,
                    "coordination_request": "vote_and_update",
                    "round": round_num,
                    "current_proposals": current_proposals
                }
                vote_result = await self._execute_agent_task(session, vote_task)
                votes_and_updates.append({
                    "session_id": session.session_id,
                    "vote": vote_result.get("vote"),
                    "updated_proposal": vote_result.get("updated_proposal")
                })
            
            # Check for consensus
            consensus_result = self._check_consensus(votes_and_updates, consensus_threshold)
            if consensus_result["consensus_reached"]:
                return {
                    "coordination_mode": "consensus",
                    "rounds": round_num,
                    "consensus_result": consensus_result,
                    "final_agreement": consensus_result["agreed_proposal"]
                }
            
            # Update proposals for next round
            current_proposals = [
                {"session_id": item["session_id"], "proposal": item["updated_proposal"]}
                for item in votes_and_updates
                if item["updated_proposal"] is not None
            ]
        
        # No consensus reached
        return {
            "coordination_mode": "consensus",
            "rounds": max_rounds,
            "consensus_reached": False,
            "final_proposals": current_proposals
        }
    
    async def _collaborative_coordination(
        self,
        sessions: List[AgentSession],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collaborative coordination - agents work together iteratively"""
        max_iterations = 5
        collaboration_results = []
        shared_context = task.copy()
        
        for iteration in range(max_iterations):
            iteration_results = []
            
            # Each agent contributes to the collaborative effort
            for session in sessions:
                session.update_activity()
                
                collaborative_task = {
                    **shared_context,
                    "coordination_request": "collaborate",
                    "iteration": iteration,
                    "shared_context": shared_context,
                    "previous_contributions": collaboration_results
                }
                
                contribution = await self._execute_agent_task(session, collaborative_task)
                iteration_results.append({
                    "session_id": session.session_id,
                    "contribution": contribution,
                    "iteration": iteration
                })
            
            collaboration_results.append(iteration_results)
            
            # Update shared context with contributions
            self._update_shared_context(shared_context, iteration_results)
            
            # Check if collaboration should continue
            if self._should_stop_collaboration(shared_context, iteration_results):
                break
        
        # Synthesize final result
        final_synthesis = await self._synthesize_collaborative_result(
            sessions[0], collaboration_results, shared_context
        )
        
        return {
            "coordination_mode": "collaborative",
            "iterations": len(collaboration_results),
            "collaboration_results": collaboration_results,
            "shared_context": shared_context,
            "final_synthesis": final_synthesis
        }
    
    def _create_worker_tasks_from_plan(
        self,
        master_plan: Any,
        worker_sessions: List[AgentSession]
    ) -> List[Dict[str, Any]]:
        """Create worker tasks based on master's plan"""
        # Simple work distribution - in production would parse master's actual plan
        tasks = []
        for i, session in enumerate(worker_sessions):
            tasks.append({
                "role": "worker",
                "worker_id": i,
                "assigned_work": f"work_item_{i}",
                "master_plan": master_plan
            })
        return tasks
    
    def _check_consensus(self, votes_and_updates: List[Dict[str, Any]], threshold: float) -> Dict[str, Any]:
        """Check if consensus has been reached"""
        if not votes_and_updates:
            return {"consensus_reached": False}
        
        # Simple consensus check - count votes
        vote_counts = defaultdict(int)
        for item in votes_and_updates:
            vote = item.get("vote")
            if vote:
                vote_counts[str(vote)] += 1
        
        total_votes = len(votes_and_updates)
        if not vote_counts:
            return {"consensus_reached": False}
        
        # Find most voted option
        top_vote = max(vote_counts.items(), key=lambda x: x[1])
        consensus_ratio = top_vote[1] / total_votes
        
        return {
            "consensus_reached": consensus_ratio >= threshold,
            "agreed_proposal": top_vote[0] if consensus_ratio >= threshold else None,
            "consensus_ratio": consensus_ratio,
            "vote_distribution": dict(vote_counts)
        }
    
    def _update_shared_context(self, shared_context: Dict[str, Any], iteration_results: List[Dict[str, Any]]):
        """Update shared context with iteration results"""
        # Extract key insights and add to shared context
        contributions = [result["contribution"] for result in iteration_results if result["contribution"]]
        if contributions:
            shared_context["latest_contributions"] = contributions
            shared_context["contribution_count"] = shared_context.get("contribution_count", 0) + len(contributions)
    
    def _should_stop_collaboration(self, shared_context: Dict[str, Any], iteration_results: List[Dict[str, Any]]) -> bool:
        """Determine if collaboration should stop"""
        # Simple stopping criteria - in production would be more sophisticated
        contribution_count = shared_context.get("contribution_count", 0)
        return contribution_count >= 15  # Stop after 15 total contributions
    
    async def _synthesize_collaborative_result(
        self,
        synthesis_session: AgentSession,
        collaboration_results: List[List[Dict[str, Any]]],
        shared_context: Dict[str, Any]
    ) -> Any:
        """Synthesize final result from collaborative work"""
        synthesis_task = {
            **shared_context,
            "coordination_request": "synthesize_results",
            "all_contributions": collaboration_results
        }
        
        return await self._execute_agent_task(synthesis_session, synthesis_task)
    
    async def _execute_agent_task(self, session: AgentSession, task: Dict[str, Any]) -> Any:
        """Execute a task with an agent session"""
        # This is a mock implementation - in production would call actual agent
        session.message_count += 1
        session.context_tokens += len(str(task)) // 4  # Rough token count
        session.update_activity()
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Return mock result based on task type
        coordination_request = task.get("coordination_request", "general")
        
        if coordination_request == "make_proposal":
            return f"Proposal from agent {session.agent_id}: {task.get('round', 0)}"
        elif coordination_request == "vote_and_update":
            return {
                "vote": "proposal_0",  # Mock vote
                "updated_proposal": f"Updated proposal from {session.agent_id}"
            }
        elif coordination_request == "collaborate":
            return f"Contribution from {session.agent_id} at iteration {task.get('iteration', 0)}"
        elif coordination_request == "synthesize_results":
            return "Synthesized final result from collaboration"
        else:
            return f"Result from agent {session.agent_id} for task: {task.get('task_type', 'general')}"
    
    async def distribute_work(
        self,
        work_items: List[Dict[str, Any]],
        available_sessions: List[AgentSession],
        distribution_strategy: str = "balanced"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Distribute work items across available agent sessions"""
        if not work_items or not available_sessions:
            return {}
        
        distribution = {session.session_id: [] for session in available_sessions}
        
        if distribution_strategy == "balanced":
            # Distribute work items evenly
            for i, work_item in enumerate(work_items):
                session_index = i % len(available_sessions)
                session_id = available_sessions[session_index].session_id
                distribution[session_id].append(work_item)
        
        elif distribution_strategy == "capability_based":
            # Distribute based on agent capabilities (simplified)
            for work_item in work_items:
                required_capability = work_item.get("required_capability", "general")
                # Find best matching session (mock logic)
                best_session = available_sessions[0]  # Simplified selection
                distribution[best_session.session_id].append(work_item)
        
        elif distribution_strategy == "load_based":
            # Distribute based on current session load
            sorted_sessions = sorted(available_sessions, key=lambda s: s.message_count)
            for i, work_item in enumerate(work_items):
                session_id = sorted_sessions[i % len(sorted_sessions)].session_id
                distribution[session_id].append(work_item)
        
        return distribution
    
    async def synchronize_agents(
        self,
        sessions: List[AgentSession],
        checkpoint_data: Dict[str, Any]
    ) -> bool:
        """Synchronize agent states at a checkpoint"""
        try:
            sync_tasks = []
            
            for session in sessions:
                # Create synchronization task for each agent
                sync_task = {
                    "coordination_request": "synchronize",
                    "checkpoint_data": checkpoint_data,
                    "session_id": session.session_id
                }
                sync_tasks.append(self._execute_agent_task(session, sync_task))
            
            # Wait for all agents to synchronize
            sync_results = await asyncio.gather(*sync_tasks, return_exceptions=True)
            
            # Check if all synchronizations were successful
            successful_syncs = [r for r in sync_results if not isinstance(r, Exception)]
            return len(successful_syncs) == len(sessions)
            
        except Exception as e:
            logger.error(f"Agent synchronization failed: {e}")
            return False
    
    async def handle_agent_failure(
        self,
        failed_session: AgentSession,
        recovery_strategy: str = "reassign"
    ) -> bool:
        """Handle agent failure and implement recovery strategy"""
        try:
            if recovery_strategy == "reassign":
                # Mark session as failed and remove from active coordination
                failed_session.status = "failed"
                
                # Remove from coordination groups
                workflow_id = failed_session.workflow_id
                if workflow_id and workflow_id in self._coordination_groups:
                    if failed_session.session_id in self._coordination_groups[workflow_id]:
                        self._coordination_groups[workflow_id].remove(failed_session.session_id)
                
                return True
            
            elif recovery_strategy == "retry":
                # Attempt to restart the session
                failed_session.status = "retrying"
                # In production, would attempt to reconnect/restart agent
                await asyncio.sleep(1)  # Simulate retry delay
                failed_session.status = "active"
                return True
            
            elif recovery_strategy == "graceful_degradation":
                # Continue with reduced capacity
                failed_session.status = "degraded"
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Agent failure handling failed: {e}")
            return False
    
    async def get_coordination_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get coordination status for a workflow"""
        if workflow_id not in self._coordination_groups:
            return {"error": "Workflow not found"}
        
        session_ids = self._coordination_groups[workflow_id]
        sessions = [self._sessions[sid] for sid in session_ids if sid in self._sessions]
        
        status = {
            "workflow_id": workflow_id,
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s.status == "active"]),
            "failed_sessions": len([s for s in sessions if s.status == "failed"]),
            "session_details": [
                {
                    "session_id": s.session_id,
                    "agent_id": s.agent_id,
                    "status": s.status,
                    "message_count": s.message_count,
                    "last_activity": s.last_activity.isoformat()
                }
                for s in sessions
            ],
            "coordination_stats": self._coordination_stats
        }
        
        return status


class WorkflowCache(IWorkflowCache):
    """
    Tool result caching and optimization system
    """
    
    def __init__(self, max_cache_size: int = 10000):
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order = deque()  # For LRU
        self._access_frequency: Dict[str, int] = defaultdict(int)  # For LFU
        self._semantic_index: Dict[str, List[str]] = defaultdict(list)  # For semantic caching
        self._max_cache_size = max_cache_size
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "stores": 0
        }
        self._default_ttl = 3600  # 1 hour
    
    async def get_cached_result(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        similarity_threshold: float = 0.9
    ) -> Optional[CacheEntry]:
        """Get cached result for tool execution"""
        # Generate cache key
        cache_key = self._generate_cache_key(tool_id, input_data)
        
        # Try exact match first
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                entry.update_access()
                self._update_access_tracking(cache_key)
                self._cache_stats["hits"] += 1
                return entry
            else:
                # Remove expired entry
                await self._remove_cache_entry(cache_key)
        
        # Try semantic similarity matching
        similar_entry = await self._find_similar_cached_result(
            tool_id, input_data, similarity_threshold
        )
        
        if similar_entry:
            similar_entry.update_access()
            self._cache_stats["hits"] += 1
            return similar_entry
        
        self._cache_stats["misses"] += 1
        return None
    
    async def store_result(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        result_data: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Store tool execution result in cache"""
        cache_key = self._generate_cache_key(tool_id, input_data)
        
        # Create cache entry
        entry = CacheEntry(
            cache_key=cache_key,
            tool_id=tool_id,
            input_data=input_data.copy(),
            result_data=result_data,
            ttl_seconds=ttl_seconds or self._default_ttl,
            tags=tags or []
        )
        
        # Generate semantic metadata
        entry.input_hash = hashlib.md5(json.dumps(input_data, sort_keys=True).encode()).hexdigest()
        entry.semantic_embedding = await self._generate_semantic_embedding(input_data)
        
        # Check cache size and evict if necessary
        if len(self._cache) >= self._max_cache_size:
            await self._evict_cache_entries(1)
        
        # Store entry
        self._cache[cache_key] = entry
        self._update_semantic_index(entry)
        self._cache_stats["stores"] += 1
        
        logger.debug(f"Cached result for tool {tool_id} with key {cache_key}")
        return cache_key
    
    async def invalidate_cache(
        self,
        cache_key: Optional[str] = None,
        tool_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Invalidate cache entries"""
        entries_to_remove = []
        
        if cache_key:
            if cache_key in self._cache:
                entries_to_remove.append(cache_key)
        
        elif tool_id:
            entries_to_remove = [
                key for key, entry in self._cache.items()
                if entry.tool_id == tool_id
            ]
        
        elif tags:
            entries_to_remove = [
                key for key, entry in self._cache.items()
                if any(tag in entry.tags for tag in tags)
            ]
        
        # Remove entries
        for key in entries_to_remove:
            await self._remove_cache_entry(key)
        
        logger.info(f"Invalidated {len(entries_to_remove)} cache entries")
        return len(entries_to_remove)
    
    async def optimize_cache(
        self,
        strategy: CacheStrategy = CacheStrategy.LRU,
        target_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Optimize cache based on strategy"""
        target_size = target_size or (self._max_cache_size // 2)
        current_size = len(self._cache)
        
        if current_size <= target_size:
            return {"message": "No optimization needed", "removed_entries": 0}
        
        entries_to_remove = current_size - target_size
        removed_count = 0
        
        if strategy == CacheStrategy.LRU:
            removed_count = await self._evict_lru_entries(entries_to_remove)
        elif strategy == CacheStrategy.LFU:
            removed_count = await self._evict_lfu_entries(entries_to_remove)
        elif strategy == CacheStrategy.TTL:
            removed_count = await self._evict_expired_entries()
        elif strategy == CacheStrategy.SEMANTIC:
            removed_count = await self._evict_semantic_duplicates()
        elif strategy == CacheStrategy.ADAPTIVE:
            removed_count = await self._adaptive_cache_optimization(entries_to_remove)
        
        return {
            "strategy": strategy.value,
            "target_size": target_size,
            "removed_entries": removed_count,
            "final_size": len(self._cache)
        }
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = self._cache_stats["hits"] / max(total_requests, 1)
        
        # Calculate average access count
        avg_access_count = statistics.mean([entry.access_count for entry in self._cache.values()]) if self._cache else 0
        
        # Count expired entries
        expired_count = sum(1 for entry in self._cache.values() if entry.is_expired())
        
        return {
            **self._cache_stats,
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "hit_rate": hit_rate,
            "avg_access_count": avg_access_count,
            "memory_usage_mb": self._estimate_cache_size_mb(),
            "semantic_index_size": len(self._semantic_index)
        }
    
    async def warm_cache(
        self,
        tool_id: str,
        common_inputs: List[Dict[str, Any]]
    ) -> int:
        """Warm cache with common tool inputs"""
        # This would typically pre-execute tools with common inputs
        # For now, we'll create placeholder cache entries
        warmed_count = 0
        
        for input_data in common_inputs:
            cache_key = self._generate_cache_key(tool_id, input_data)
            
            if cache_key not in self._cache:
                # Create placeholder entry (in production would actually execute tool)
                entry = CacheEntry(
                    cache_key=cache_key,
                    tool_id=tool_id,
                    input_data=input_data.copy(),
                    result_data=f"Warmed cache result for {tool_id}",
                    ttl_seconds=self._default_ttl,
                    tags=["warmed"]
                )
                
                self._cache[cache_key] = entry
                self._update_semantic_index(entry)
                warmed_count += 1
        
        logger.info(f"Warmed cache with {warmed_count} entries for tool {tool_id}")
        return warmed_count
    
    def _generate_cache_key(self, tool_id: str, input_data: Dict[str, Any]) -> str:
        """Generate cache key for tool and input"""
        # Sort keys for consistent hashing
        sorted_input = json.dumps(input_data, sort_keys=True)
        combined = f"{tool_id}:{sorted_input}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    async def _generate_semantic_embedding(self, input_data: Dict[str, Any]) -> List[float]:
        """Generate semantic embedding for input data"""
        # Simple mock embedding - in production would use actual embedding model
        text_content = json.dumps(input_data, sort_keys=True)
        
        # Create simple numerical features
        embedding = [
            len(text_content) / 1000,  # Normalized length
            len(input_data),  # Number of keys
            hash(text_content) % 1000 / 1000,  # Normalized hash
        ]
        
        # Pad to standard size
        while len(embedding) < 384:  # Common embedding size
            embedding.append(0.0)
        
        return embedding[:384]
    
    def _update_semantic_index(self, entry: CacheEntry):
        """Update semantic index with new entry"""
        if entry.semantic_embedding:
            # Simple indexing by tool_id - in production would use vector search
            self._semantic_index[entry.tool_id].append(entry.cache_key)
    
    async def _find_similar_cached_result(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        similarity_threshold: float
    ) -> Optional[CacheEntry]:
        """Find semantically similar cached result"""
        if tool_id not in self._semantic_index:
            return None
        
        query_embedding = await self._generate_semantic_embedding(input_data)
        best_match = None
        best_similarity = 0.0
        
        for cache_key in self._semantic_index[tool_id]:
            if cache_key not in self._cache:
                continue
                
            entry = self._cache[cache_key]
            if entry.is_expired():
                continue
            
            if entry.semantic_embedding:
                similarity = self._calculate_cosine_similarity(query_embedding, entry.semantic_embedding)
                if similarity > best_similarity and similarity >= similarity_threshold:
                    best_similarity = similarity
                    best_match = entry
        
        return best_match
    
    def _calculate_cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _update_access_tracking(self, cache_key: str):
        """Update access tracking for LRU/LFU"""
        # Update LRU tracking
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        self._access_order.append(cache_key)
        
        # Update LFU tracking
        self._access_frequency[cache_key] += 1
    
    async def _evict_cache_entries(self, count: int) -> int:
        """Evict cache entries using default strategy (LRU)"""
        return await self._evict_lru_entries(count)
    
    async def _evict_lru_entries(self, count: int) -> int:
        """Evict least recently used entries"""
        evicted = 0
        while evicted < count and self._access_order:
            cache_key = self._access_order.popleft()
            if cache_key in self._cache:
                await self._remove_cache_entry(cache_key)
                evicted += 1
        return evicted
    
    async def _evict_lfu_entries(self, count: int) -> int:
        """Evict least frequently used entries"""
        # Sort by access frequency
        sorted_entries = sorted(
            self._access_frequency.items(),
            key=lambda x: x[1]
        )
        
        evicted = 0
        for cache_key, _ in sorted_entries:
            if evicted >= count:
                break
            if cache_key in self._cache:
                await self._remove_cache_entry(cache_key)
                evicted += 1
        
        return evicted
    
    async def _evict_expired_entries(self) -> int:
        """Remove all expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            await self._remove_cache_entry(key)
        
        return len(expired_keys)
    
    async def _evict_semantic_duplicates(self) -> int:
        """Remove semantically similar duplicate entries"""
        # This is a simplified implementation
        # In production would use more sophisticated deduplication
        removed_count = 0
        processed_embeddings = set()
        
        for cache_key, entry in list(self._cache.items()):
            if entry.semantic_embedding:
                embedding_hash = hash(tuple(entry.semantic_embedding))
                if embedding_hash in processed_embeddings:
                    await self._remove_cache_entry(cache_key)
                    removed_count += 1
                else:
                    processed_embeddings.add(embedding_hash)
        
        return removed_count
    
    async def _adaptive_cache_optimization(self, target_remove_count: int) -> int:
        """Adaptive cache optimization using multiple strategies"""
        # First remove expired entries
        removed = await self._evict_expired_entries()
        
        # If still need to remove more, use LRU for low-frequency entries
        if removed < target_remove_count:
            remaining = target_remove_count - removed
            lru_removed = await self._evict_lru_entries(remaining // 2)
            removed += lru_removed
        
        # Finally remove duplicates if still needed
        if removed < target_remove_count:
            duplicate_removed = await self._evict_semantic_duplicates()
            removed += duplicate_removed
        
        return removed
    
    async def _remove_cache_entry(self, cache_key: str):
        """Remove a cache entry and update indices"""
        if cache_key not in self._cache:
            return
        
        entry = self._cache[cache_key]
        
        # Remove from main cache
        del self._cache[cache_key]
        
        # Remove from semantic index
        if entry.tool_id in self._semantic_index:
            if cache_key in self._semantic_index[entry.tool_id]:
                self._semantic_index[entry.tool_id].remove(cache_key)
        
        # Remove from access tracking
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        
        if cache_key in self._access_frequency:
            del self._access_frequency[cache_key]
        
        self._cache_stats["evictions"] += 1
    
    def _estimate_cache_size_mb(self) -> float:
        """Estimate cache size in MB"""
        # Simple estimation - in production would be more accurate
        total_size = 0
        
        for entry in self._cache.values():
            # Estimate size of entry
            entry_size = len(str(entry.input_data)) + len(str(entry.result_data))
            if entry.semantic_embedding:
                entry_size += len(entry.semantic_embedding) * 4  # 4 bytes per float
            total_size += entry_size
        
        return total_size / (1024 * 1024)  # Convert to MB


class ContextPreserver(IContextPreserver):
    """
    Agent conversation context preservation system
    """
    
    def __init__(self):
        self._snapshots: Dict[str, ContextSnapshot] = {}
        self._session_snapshots: Dict[str, List[str]] = defaultdict(list)
        self._preservation_stats = {
            "snapshots_created": 0,
            "contexts_restored": 0,
            "contexts_compressed": 0,
            "contexts_merged": 0
        }
        self._max_snapshots_per_session = 50
    
    async def save_context(
        self,
        agent_session_id: str,
        workflow_execution_id: str,
        step_id: str,
        context_data: Dict[str, Any],
        scope: ContextScope = ContextScope.STEP
    ) -> str:
        """Save agent conversation context"""
        snapshot = ContextSnapshot(
            agent_session_id=agent_session_id,
            workflow_execution_id=workflow_execution_id,
            step_id=step_id,
            scope=scope
        )
        
        # Process context data
        if "messages" in context_data:
            snapshot.messages = context_data["messages"]
        
        if "variables" in context_data:
            snapshot.variables = context_data["variables"].copy()
        
        if "metadata" in context_data:
            snapshot.metadata = context_data["metadata"].copy()
        
        # Calculate completeness and relevance scores
        snapshot.completeness_score = self._calculate_completeness_score(context_data)
        snapshot.relevance_score = self._calculate_relevance_score(context_data, scope)
        
        # Store snapshot
        self._snapshots[snapshot.snapshot_id] = snapshot
        self._session_snapshots[agent_session_id].append(snapshot.snapshot_id)
        
        # Manage session snapshot limit
        await self._manage_session_snapshot_limit(agent_session_id)
        
        self._preservation_stats["snapshots_created"] += 1
        
        logger.debug(f"Saved context snapshot {snapshot.snapshot_id} for session {agent_session_id}")
        return snapshot.snapshot_id
    
    async def restore_context(
        self,
        snapshot_id: str,
        merge_strategy: str = "replace"
    ) -> Optional[ContextSnapshot]:
        """Restore agent conversation context"""
        if snapshot_id not in self._snapshots:
            return None
        
        snapshot = self._snapshots[snapshot_id]
        
        if merge_strategy == "replace":
            # Return snapshot as-is
            restored_snapshot = snapshot
        
        elif merge_strategy == "merge_recent":
            # Merge with recent snapshots from same session
            recent_snapshots = await self._get_recent_session_snapshots(
                snapshot.agent_session_id, 3
            )
            restored_snapshot = await self._merge_snapshots(recent_snapshots, "union")
        
        elif merge_strategy == "enhance":
            # Enhance with additional context
            restored_snapshot = await self._enhance_context_snapshot(snapshot)
        
        else:
            restored_snapshot = snapshot
        
        self._preservation_stats["contexts_restored"] += 1
        
        logger.debug(f"Restored context snapshot {snapshot_id} using {merge_strategy} strategy")
        return restored_snapshot
    
    async def get_context_history(
        self,
        agent_session_id: str,
        limit: int = 50
    ) -> List[ContextSnapshot]:
        """Get context history for an agent session"""
        if agent_session_id not in self._session_snapshots:
            return []
        
        snapshot_ids = self._session_snapshots[agent_session_id]
        
        # Get recent snapshots up to limit
        recent_snapshot_ids = snapshot_ids[-limit:] if len(snapshot_ids) > limit else snapshot_ids
        
        snapshots = []
        for snapshot_id in recent_snapshot_ids:
            if snapshot_id in self._snapshots:
                snapshots.append(self._snapshots[snapshot_id])
        
        # Sort by creation time (most recent first)
        snapshots.sort(key=lambda s: s.created_at, reverse=True)
        
        return snapshots
    
    async def compress_context(
        self,
        snapshot_id: str,
        compression_ratio: float = 0.5,
        preserve_important: bool = True
    ) -> str:
        """Compress context to reduce storage size"""
        if snapshot_id not in self._snapshots:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        snapshot = self._snapshots[snapshot_id]
        original_size = self._calculate_snapshot_size(snapshot)
        
        # Create compressed version
        compressed_snapshot = ContextSnapshot(
            agent_session_id=snapshot.agent_session_id,
            workflow_execution_id=snapshot.workflow_execution_id,
            step_id=snapshot.step_id,
            scope=snapshot.scope
        )
        
        # Compress messages
        if snapshot.messages:
            target_message_count = max(1, int(len(snapshot.messages) * compression_ratio))
            
            if preserve_important:
                compressed_snapshot.messages = await self._compress_messages_preserve_important(
                    snapshot.messages, target_message_count
                )
            else:
                # Simple truncation - keep most recent
                compressed_snapshot.messages = snapshot.messages[-target_message_count:]
        
        # Compress variables (keep most important)
        if snapshot.variables:
            important_vars = self._select_important_variables(
                snapshot.variables, compression_ratio
            )
            compressed_snapshot.variables = important_vars
        
        # Copy essential metadata
        compressed_snapshot.metadata = snapshot.metadata.copy()
        
        # Calculate compression ratio
        compressed_size = self._calculate_snapshot_size(compressed_snapshot)
        actual_compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        compressed_snapshot.compression_ratio = actual_compression_ratio
        
        # Store compressed snapshot
        compressed_id = compressed_snapshot.snapshot_id
        self._snapshots[compressed_id] = compressed_snapshot
        
        # Update session snapshots
        session_id = snapshot.agent_session_id
        if session_id in self._session_snapshots:
            self._session_snapshots[session_id].append(compressed_id)
        
        self._preservation_stats["contexts_compressed"] += 1
        
        logger.info(f"Compressed context {snapshot_id} to {compressed_id} "
                   f"(ratio: {actual_compression_ratio:.3f})")
        
        return compressed_id
    
    async def merge_contexts(
        self,
        snapshot_ids: List[str],
        merge_strategy: str = "union"
    ) -> str:
        """Merge multiple context snapshots"""
        snapshots = []
        for snapshot_id in snapshot_ids:
            if snapshot_id in self._snapshots:
                snapshots.append(self._snapshots[snapshot_id])
        
        if not snapshots:
            raise ValueError("No valid snapshots found for merging")
        
        merged_snapshot = await self._merge_snapshots(snapshots, merge_strategy)
        
        # Store merged snapshot
        self._snapshots[merged_snapshot.snapshot_id] = merged_snapshot
        
        # Add to all relevant sessions
        for snapshot in snapshots:
            session_id = snapshot.agent_session_id
            if session_id in self._session_snapshots:
                self._session_snapshots[session_id].append(merged_snapshot.snapshot_id)
        
        self._preservation_stats["contexts_merged"] += 1
        
        logger.info(f"Merged {len(snapshots)} contexts into {merged_snapshot.snapshot_id} "
                   f"using {merge_strategy} strategy")
        
        return merged_snapshot.snapshot_id
    
    async def cleanup_expired_contexts(self, max_age_hours: int = 24) -> int:
        """Clean up expired context snapshots"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        expired_snapshot_ids = [
            snapshot_id for snapshot_id, snapshot in self._snapshots.items()
            if snapshot.created_at < cutoff_time
        ]
        
        # Remove expired snapshots
        for snapshot_id in expired_snapshot_ids:
            snapshot = self._snapshots[snapshot_id]
            session_id = snapshot.agent_session_id
            
            # Remove from snapshots
            del self._snapshots[snapshot_id]
            
            # Remove from session snapshots
            if session_id in self._session_snapshots:
                if snapshot_id in self._session_snapshots[session_id]:
                    self._session_snapshots[session_id].remove(snapshot_id)
        
        logger.info(f"Cleaned up {len(expired_snapshot_ids)} expired context snapshots")
        return len(expired_snapshot_ids)
    
    def _calculate_completeness_score(self, context_data: Dict[str, Any]) -> float:
        """Calculate completeness score for context data"""
        score = 0.0
        
        # Check for essential components
        if "messages" in context_data and context_data["messages"]:
            score += 0.4
        
        if "variables" in context_data and context_data["variables"]:
            score += 0.3
        
        if "metadata" in context_data and context_data["metadata"]:
            score += 0.2
        
        # Additional quality indicators
        if "agent_state" in context_data:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_relevance_score(self, context_data: Dict[str, Any], scope: ContextScope) -> float:
        """Calculate relevance score based on scope and content"""
        base_score = 0.5
        
        # Scope-based scoring
        if scope == ContextScope.GLOBAL:
            base_score += 0.3
        elif scope == ContextScope.WORKFLOW:
            base_score += 0.2
        elif scope == ContextScope.SESSION:
            base_score += 0.2
        elif scope == ContextScope.STEP:
            base_score += 0.1
        
        # Content-based scoring
        if "messages" in context_data:
            message_count = len(context_data["messages"])
            if message_count > 10:
                base_score += 0.2
            elif message_count > 5:
                base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _calculate_snapshot_size(self, snapshot: ContextSnapshot) -> int:
        """Calculate approximate size of snapshot in bytes"""
        size = 0
        
        # Messages size
        if snapshot.messages:
            size += len(json.dumps(snapshot.messages))
        
        # Variables size
        if snapshot.variables:
            size += len(json.dumps(snapshot.variables, default=str))
        
        # Metadata size
        if snapshot.metadata:
            size += len(json.dumps(snapshot.metadata, default=str))
        
        return size
    
    async def _manage_session_snapshot_limit(self, session_id: str):
        """Manage snapshot limit per session"""
        if session_id not in self._session_snapshots:
            return
        
        snapshot_ids = self._session_snapshots[session_id]
        
        if len(snapshot_ids) > self._max_snapshots_per_session:
            # Remove oldest snapshots
            excess_count = len(snapshot_ids) - self._max_snapshots_per_session
            snapshots_to_remove = snapshot_ids[:excess_count]
            
            for snapshot_id in snapshots_to_remove:
                if snapshot_id in self._snapshots:
                    del self._snapshots[snapshot_id]
                snapshot_ids.remove(snapshot_id)
    
    async def _get_recent_session_snapshots(
        self,
        session_id: str,
        count: int
    ) -> List[ContextSnapshot]:
        """Get recent snapshots for a session"""
        if session_id not in self._session_snapshots:
            return []
        
        snapshot_ids = self._session_snapshots[session_id]
        recent_ids = snapshot_ids[-count:] if len(snapshot_ids) > count else snapshot_ids
        
        snapshots = []
        for snapshot_id in recent_ids:
            if snapshot_id in self._snapshots:
                snapshots.append(self._snapshots[snapshot_id])
        
        return snapshots
    
    async def _merge_snapshots(
        self,
        snapshots: List[ContextSnapshot],
        strategy: str
    ) -> ContextSnapshot:
        """Merge multiple snapshots using specified strategy"""
        if not snapshots:
            raise ValueError("No snapshots to merge")
        
        # Use first snapshot as base
        merged = ContextSnapshot(
            agent_session_id=snapshots[0].agent_session_id,
            workflow_execution_id=snapshots[0].workflow_execution_id,
            step_id="merged",
            scope=ContextScope.WORKFLOW
        )
        
        if strategy == "union":
            # Union of all messages, variables, and metadata
            all_messages = []
            all_variables = {}
            all_metadata = {}
            
            for snapshot in snapshots:
                if snapshot.messages:
                    all_messages.extend(snapshot.messages)
                
                if snapshot.variables:
                    all_variables.update(snapshot.variables)
                
                if snapshot.metadata:
                    all_metadata.update(snapshot.metadata)
            
            # Remove duplicate messages (simple deduplication)
            seen_messages = set()
            unique_messages = []
            for msg in all_messages:
                msg_key = f"{msg.get('role', '')}:{msg.get('content', '')[:100]}"
                if msg_key not in seen_messages:
                    seen_messages.add(msg_key)
                    unique_messages.append(msg)
            
            merged.messages = unique_messages
            merged.variables = all_variables
            merged.metadata = all_metadata
        
        elif strategy == "intersection":
            # Only keep common elements (simplified)
            merged.variables = snapshots[0].variables.copy() if snapshots[0].variables else {}
            merged.metadata = snapshots[0].metadata.copy() if snapshots[0].metadata else {}
            
            # Keep only variables that exist in all snapshots
            for snapshot in snapshots[1:]:
                if snapshot.variables:
                    common_vars = {k: v for k, v in merged.variables.items() 
                                 if k in snapshot.variables}
                    merged.variables = common_vars
        
        elif strategy == "latest_priority":
            # Latest snapshots take priority
            sorted_snapshots = sorted(snapshots, key=lambda s: s.created_at)
            
            for snapshot in sorted_snapshots:
                if snapshot.messages:
                    merged.messages.extend(snapshot.messages)
                
                if snapshot.variables:
                    merged.variables.update(snapshot.variables)
                
                if snapshot.metadata:
                    merged.metadata.update(snapshot.metadata)
        
        # Calculate quality scores
        merged.completeness_score = statistics.mean([s.completeness_score for s in snapshots])
        merged.relevance_score = max([s.relevance_score for s in snapshots])
        
        return merged
    
    async def _compress_messages_preserve_important(
        self,
        messages: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Compress messages while preserving important ones"""
        if len(messages) <= target_count:
            return messages
        
        # Score messages by importance
        scored_messages = []
        for i, msg in enumerate(messages):
            importance_score = self._calculate_message_importance(msg, i, len(messages))
            scored_messages.append((msg, importance_score))
        
        # Sort by importance and take top messages
        scored_messages.sort(key=lambda x: x[1], reverse=True)
        important_messages = [msg for msg, score in scored_messages[:target_count]]
        
        # Sort by original order
        important_messages.sort(key=lambda msg: messages.index(msg))
        
        return important_messages
    
    def _calculate_message_importance(
        self,
        message: Dict[str, Any],
        position: int,
        total_messages: int
    ) -> float:
        """Calculate importance score for a message"""
        score = 0.0
        
        # Recent messages are more important
        recency_score = position / total_messages
        score += recency_score * 0.3
        
        # Messages with more content
        content_length = len(message.get("content", ""))
        if content_length > 100:
            score += 0.2
        elif content_length > 50:
            score += 0.1
        
        # System messages are important
        if message.get("role") == "system":
            score += 0.3
        
        # Messages with special markers
        content = message.get("content", "").lower()
        if any(keyword in content for keyword in ["error", "warning", "important", "critical"]):
            score += 0.2
        
        return min(score, 1.0)
    
    def _select_important_variables(
        self,
        variables: Dict[str, Any],
        compression_ratio: float
    ) -> Dict[str, Any]:
        """Select most important variables based on compression ratio"""
        target_count = max(1, int(len(variables) * compression_ratio))
        
        if len(variables) <= target_count:
            return variables.copy()
        
        # Score variables by importance
        scored_vars = []
        for key, value in variables.items():
            importance_score = self._calculate_variable_importance(key, value)
            scored_vars.append((key, value, importance_score))
        
        # Sort by importance and take top variables
        scored_vars.sort(key=lambda x: x[2], reverse=True)
        
        important_vars = {}
        for key, value, score in scored_vars[:target_count]:
            important_vars[key] = value
        
        return important_vars
    
    def _calculate_variable_importance(self, key: str, value: Any) -> float:
        """Calculate importance score for a variable"""
        score = 0.0
        
        # Key-based importance
        important_keys = ["user_id", "session_id", "workflow_id", "agent_id", "state", "config"]
        if any(important_key in key.lower() for important_key in important_keys):
            score += 0.4
        
        # Value-based importance
        if isinstance(value, (dict, list)) and len(str(value)) > 50:
            score += 0.3
        elif isinstance(value, str) and len(value) > 20:
            score += 0.2
        
        # Type-based importance
        if isinstance(value, (dict, list)):
            score += 0.1
        
        return min(score, 1.0)
    
    async def _enhance_context_snapshot(self, snapshot: ContextSnapshot) -> ContextSnapshot:
        """Enhance context snapshot with additional information"""
        enhanced = ContextSnapshot(
            agent_session_id=snapshot.agent_session_id,
            workflow_execution_id=snapshot.workflow_execution_id,
            step_id=snapshot.step_id,
            scope=snapshot.scope
        )
        
        # Copy existing data
        enhanced.messages = snapshot.messages.copy() if snapshot.messages else []
        enhanced.variables = snapshot.variables.copy() if snapshot.variables else {}
        enhanced.metadata = snapshot.metadata.copy() if snapshot.metadata else {}
        
        # Add enhancement metadata
        enhanced.metadata["enhanced"] = True
        enhanced.metadata["enhancement_timestamp"] = datetime.now(timezone.utc).isoformat()
        enhanced.metadata["original_snapshot_id"] = snapshot.snapshot_id
        
        # Calculate enhanced quality scores
        enhanced.completeness_score = min(snapshot.completeness_score + 0.1, 1.0)
        enhanced.relevance_score = snapshot.relevance_score
        
        return enhanced


class LoadBalancer(ILoadBalancer):
    """
    Tool and agent load balancing system
    """
    
    def __init__(self):
        self._targets: Dict[str, Dict[str, Any]] = {}  # target_id -> target_info
        self._target_metrics: Dict[str, Dict[str, Any]] = {}  # target_id -> metrics
        self._routing_stats: Dict[str, int] = defaultdict(int)  # target_id -> request_count
        self._health_scores: Dict[str, float] = {}  # target_id -> health_score
        self._load_balancer_stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "unhealthy_targets_removed": 0
        }
        self._default_config = LoadBalancerConfig()
        self._last_health_check = time.time()
    
    async def select_target(
        self,
        targets: List[str],
        request_context: Dict[str, Any],
        config: Optional[LoadBalancerConfig] = None
    ) -> Optional[str]:
        """Select target for load balancing"""
        if not targets:
            return None
        
        config = config or self._default_config
        self._load_balancer_stats["total_requests"] += 1
        
        # Filter healthy targets
        healthy_targets = await self._filter_healthy_targets(targets)
        
        if not healthy_targets:
            # No healthy targets available
            self._load_balancer_stats["failed_routes"] += 1
            return None
        
        try:
            selected_target = None
            
            if config.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                selected_target = await self._round_robin_selection(healthy_targets)
            elif config.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                selected_target = await self._least_connections_selection(healthy_targets)
            elif config.strategy == LoadBalancingStrategy.WEIGHTED:
                selected_target = await self._weighted_selection(healthy_targets, config.weights)
            elif config.strategy == LoadBalancingStrategy.PERFORMANCE:
                selected_target = await self._performance_based_selection(healthy_targets, config)
            elif config.strategy == LoadBalancingStrategy.RESOURCE_USAGE:
                selected_target = await self._resource_usage_selection(healthy_targets)
            elif config.strategy == LoadBalancingStrategy.GEOGRAPHIC:
                selected_target = await self._geographic_selection(healthy_targets, request_context)
            
            if selected_target:
                # Update routing stats
                self._routing_stats[selected_target] += 1
                self._load_balancer_stats["successful_routes"] += 1
                
                # Log routing decision
                logger.debug(f"Selected target {selected_target} using {config.strategy.value} strategy")
                
                return selected_target
            else:
                self._load_balancer_stats["failed_routes"] += 1
                return None
                
        except Exception as e:
            logger.error(f"Load balancer selection failed: {e}")
            self._load_balancer_stats["failed_routes"] += 1
            return None
    
    async def _filter_healthy_targets(self, targets: List[str]) -> List[str]:
        """Filter targets based on health status"""
        healthy = []
        
        for target_id in targets:
            # Check if we have health info
            if target_id in self._health_scores:
                if self._health_scores[target_id] >= 0.5:  # Minimum health threshold
                    healthy.append(target_id)
            else:
                # If no health info, assume healthy
                healthy.append(target_id)
                self._health_scores[target_id] = 1.0
        
        return healthy
    
    async def _round_robin_selection(self, targets: List[str]) -> str:
        """Round robin selection"""
        # Simple round robin based on request counts
        min_requests = min(self._routing_stats.get(target, 0) for target in targets)
        candidates = [target for target in targets 
                     if self._routing_stats.get(target, 0) == min_requests]
        
        # If multiple candidates, pick first one
        return candidates[0]
    
    async def _least_connections_selection(self, targets: List[str]) -> str:
        """Least connections selection"""
        # Use routing stats as proxy for connections
        min_connections = min(self._routing_stats.get(target, 0) for target in targets)
        candidates = [target for target in targets 
                     if self._routing_stats.get(target, 0) == min_connections]
        
        return candidates[0]
    
    async def _weighted_selection(self, targets: List[str], weights: Dict[str, float]) -> str:
        """Weighted selection based on target weights"""
        if not weights:
            return await self._round_robin_selection(targets)
        
        # Calculate weighted probabilities
        total_weight = 0.0
        target_weights = {}
        
        for target in targets:
            weight = weights.get(target, 1.0)  # Default weight 1.0
            # Adjust weight based on health score
            health_score = self._health_scores.get(target, 1.0)
            adjusted_weight = weight * health_score
            target_weights[target] = adjusted_weight
            total_weight += adjusted_weight
        
        if total_weight == 0:
            return await self._round_robin_selection(targets)
        
        # Select based on weights
        import random
        rand_value = random.uniform(0, total_weight)
        cumulative_weight = 0.0
        
        for target, weight in target_weights.items():
            cumulative_weight += weight
            if rand_value <= cumulative_weight:
                return target
        
        # Fallback to first target
        return targets[0]
    
    async def _performance_based_selection(
        self,
        targets: List[str],
        config: LoadBalancerConfig
    ) -> str:
        """Performance-based selection using multiple factors"""
        best_target = None
        best_score = -1.0
        
        for target in targets:
            score = 0.0
            
            # Health score component
            health_score = self._health_scores.get(target, 1.0)
            score += health_score * 0.4
            
            # Performance metrics
            metrics = self._target_metrics.get(target, {})
            
            # Latency component (lower is better)
            avg_latency = metrics.get("avg_latency_ms", 100)  # Default 100ms
            latency_score = max(0, 1.0 - (avg_latency / 1000))  # Normalize to 0-1
            score += latency_score * config.latency_weight
            
            # Success rate component
            success_rate = metrics.get("success_rate", 1.0)
            score += success_rate * config.success_rate_weight
            
            # Resource usage component (lower is better)
            cpu_usage = metrics.get("cpu_usage", 0.5)  # Default 50%
            memory_usage = metrics.get("memory_usage", 0.5)  # Default 50%
            resource_score = 1.0 - ((cpu_usage + memory_usage) / 2)
            score += resource_score * config.resource_weight
            
            if score > best_score:
                best_score = score
                best_target = target
        
        return best_target or targets[0]
    
    async def _resource_usage_selection(self, targets: List[str]) -> str:
        """Resource usage-based selection"""
        best_target = None
        lowest_usage = float('inf')
        
        for target in targets:
            metrics = self._target_metrics.get(target, {})
            
            # Calculate combined resource usage
            cpu_usage = metrics.get("cpu_usage", 0.5)
            memory_usage = metrics.get("memory_usage", 0.5)
            combined_usage = (cpu_usage + memory_usage) / 2
            
            if combined_usage < lowest_usage:
                lowest_usage = combined_usage
                best_target = target
        
        return best_target or targets[0]
    
    async def _geographic_selection(
        self,
        targets: List[str],
        request_context: Dict[str, Any]
    ) -> str:
        """Geographic proximity-based selection"""
        # Simple geographic selection based on context
        user_region = request_context.get("region", "us-east-1")
        
        # Find targets in same region
        same_region_targets = []
        for target in targets:
            target_info = self._targets.get(target, {})
            target_region = target_info.get("region", "us-east-1")
            if target_region == user_region:
                same_region_targets.append(target)
        
        if same_region_targets:
            return await self._round_robin_selection(same_region_targets)
        else:
            # Fallback to any target
            return await self._round_robin_selection(targets)
    
    async def update_target_health(
        self,
        target_id: str,
        health_score: float,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update target health and performance metrics"""
        try:
            # Clamp health score to 0-1 range
            health_score = max(0.0, min(1.0, health_score))
            self._health_scores[target_id] = health_score
            
            # Update performance metrics if provided
            if performance_metrics:
                if target_id not in self._target_metrics:
                    self._target_metrics[target_id] = {}
                
                self._target_metrics[target_id].update(performance_metrics)
                self._target_metrics[target_id]["last_updated"] = time.time()
            
            # Register target if not exists
            if target_id not in self._targets:
                self._targets[target_id] = {
                    "target_id": target_id,
                    "registered_at": time.time(),
                    "region": "us-east-1"  # Default region
                }
            
            logger.debug(f"Updated health for target {target_id}: {health_score}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update target health for {target_id}: {e}")
            return False
    
    async def remove_unhealthy_targets(self, health_threshold: float = 0.5) -> List[str]:
        """Remove unhealthy targets from load balancing pool"""
        unhealthy_targets = []
        
        for target_id, health_score in list(self._health_scores.items()):
            if health_score < health_threshold:
                unhealthy_targets.append(target_id)
                
                # Remove from tracking
                if target_id in self._health_scores:
                    del self._health_scores[target_id]
                
                if target_id in self._targets:
                    del self._targets[target_id]
                
                if target_id in self._target_metrics:
                    del self._target_metrics[target_id]
        
        if unhealthy_targets:
            self._load_balancer_stats["unhealthy_targets_removed"] += len(unhealthy_targets)
            logger.info(f"Removed {len(unhealthy_targets)} unhealthy targets: {unhealthy_targets}")
        
        return unhealthy_targets
    
    async def get_target_statistics(self, target_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific target"""
        if target_id not in self._targets:
            return None
        
        target_info = self._targets[target_id]
        metrics = self._target_metrics.get(target_id, {})
        health_score = self._health_scores.get(target_id, 1.0)
        request_count = self._routing_stats.get(target_id, 0)
        
        return {
            "target_id": target_id,
            "target_info": target_info,
            "health_score": health_score,
            "request_count": request_count,
            "performance_metrics": metrics,
            "last_selected": metrics.get("last_updated", 0)
        }
    
    async def get_load_balancing_metrics(self) -> Dict[str, Any]:
        """Get overall load balancing metrics"""
        total_requests = self._load_balancer_stats["total_requests"]
        success_rate = (self._load_balancer_stats["successful_routes"] / 
                       max(total_requests, 1))
        
        # Calculate request distribution
        if self._routing_stats:
            max_requests = max(self._routing_stats.values())
            min_requests = min(self._routing_stats.values())
            request_variance = max_requests - min_requests
        else:
            request_variance = 0
        
        return {
            **self._load_balancer_stats,
            "success_rate": success_rate,
            "active_targets": len(self._targets),
            "healthy_targets": len([t for t in self._health_scores.values() if t >= 0.5]),
            "request_distribution": dict(self._routing_stats),
            "request_variance": request_variance,
            "avg_health_score": (statistics.mean(self._health_scores.values()) 
                               if self._health_scores else 0.0)
        }
    
    async def rebalance_load(self, force_rebalance: bool = False) -> Dict[str, Any]:
        """Trigger load rebalancing"""
        try:
            initial_distribution = dict(self._routing_stats)
            
            if not force_rebalance:
                # Check if rebalancing is needed
                if self._routing_stats:
                    max_requests = max(self._routing_stats.values())
                    min_requests = min(self._routing_stats.values())
                    variance = max_requests - min_requests
                    
                    # Only rebalance if variance is significant
                    if variance < 10:  # Threshold for rebalancing
                        return {
                            "rebalanced": False,
                            "reason": "Variance too low",
                            "variance": variance
                        }
            
            # Perform rebalancing by resetting stats
            if force_rebalance or (self._routing_stats and max(self._routing_stats.values()) > 100):
                # Reset routing stats for rebalancing
                reset_count = len(self._routing_stats)
                self._routing_stats.clear()
                
                logger.info(f"Rebalanced load balancer - reset {reset_count} target stats")
                
                return {
                    "rebalanced": True,
                    "reset_targets": reset_count,
                    "initial_distribution": initial_distribution,
                    "reason": "Forced rebalancing" if force_rebalance else "High variance detected"
                }
            
            return {
                "rebalanced": False,
                "reason": "No rebalancing needed"
            }
            
        except Exception as e:
            logger.error(f"Load rebalancing failed: {e}")
            return {
                "rebalanced": False,
                "error": str(e)
            }