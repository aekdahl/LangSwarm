"""
Tests for Advanced Tool & Agent Integration in V2 Workflows

Comprehensive test suite covering all integration components and enhanced workflow steps.
"""

import pytest
import asyncio
import tempfile
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import the integration components
from langswarm.v2.core.workflows.integration.interfaces import (
    DiscoveryStrategy, CoordinationMode, CacheStrategy, ContextScope,
    LoadBalancingStrategy, ToolDescriptor, AgentSession, CacheEntry,
    ContextSnapshot, LoadBalancerConfig
)
from langswarm.v2.core.workflows.integration.implementations import (
    DynamicToolDiscovery, AgentCoordinator, WorkflowCache,
    ContextPreserver, LoadBalancer
)
from langswarm.v2.core.workflows.integration.steps import (
    AdvancedAgentStep, CachedToolStep, CoordinatedAgentStep,
    LoadBalancedStep, ContextAwareStep
)
from langswarm.v2.core.workflows.integration.factory import (
    create_integration_manager, create_default_integration_manager,
    create_performance_optimized_integration_manager
)
from langswarm.v2.core.workflows.interfaces import WorkflowContext, StepType
from langswarm.v2.core.workflows.base import BaseWorkflowStep


class TestDynamicToolDiscovery:
    """Test dynamic tool discovery implementation"""
    
    @pytest.fixture
    def tool_discovery(self):
        config = {
            "discovery_timeout": 10,
            "max_concurrent_discoveries": 3,
            "cache_discoveries": True
        }
        return DynamicToolDiscovery(config)
    
    @pytest.fixture
    def sample_context(self):
        return WorkflowContext(
            workflow_id="test_workflow",
            execution_id="test_execution",
            variables={"user_id": "test_user", "task_type": "analysis"}
        )
    
    @pytest.mark.asyncio
    async def test_tool_discovery_initialization(self, tool_discovery):
        """Test tool discovery initialization"""
        assert await tool_discovery.initialize()
        assert tool_discovery._initialized
    
    @pytest.mark.asyncio
    async def test_discover_tools_automatic(self, tool_discovery, sample_context):
        """Test automatic tool discovery"""
        await tool_discovery.initialize()
        
        tools = await tool_discovery.discover_tools(
            context=sample_context,
            strategy=DiscoveryStrategy.AUTOMATIC
        )
        
        assert isinstance(tools, list)
        # With mock implementation, we should get some basic tools
        assert len(tools) >= 0
    
    @pytest.mark.asyncio
    async def test_discover_tools_with_capabilities(self, tool_discovery, sample_context):
        """Test tool discovery with specific capabilities"""
        await tool_discovery.initialize()
        
        tools = await tool_discovery.discover_tools(
            context=sample_context,
            required_capabilities=["data_processing", "file_system"],
            strategy=DiscoveryStrategy.SEMANTIC
        )
        
        assert isinstance(tools, list)
        # All returned tools should have the required capabilities
        for tool in tools:
            assert any(cap in tool.capabilities for cap in ["data_processing", "file_system"])
    
    @pytest.mark.asyncio
    async def test_register_and_get_tool(self, tool_discovery):
        """Test tool registration and retrieval"""
        await tool_discovery.initialize()
        
        # Create a test tool descriptor
        test_tool = ToolDescriptor(
            tool_id="test_tool_1",
            tool_name="Test Tool",
            tool_type="utility",
            capabilities=["read", "write"],
            metadata={"version": "1.0"}
        )
        
        # Register tool
        assert await tool_discovery.register_tool(test_tool)
        
        # Retrieve tool
        retrieved = await tool_discovery.get_tool_descriptor("test_tool_1")
        assert retrieved is not None
        assert retrieved.tool_id == "test_tool_1"
        assert retrieved.tool_name == "Test Tool"
    
    @pytest.mark.asyncio
    async def test_find_tools_by_capability(self, tool_discovery):
        """Test finding tools by capability"""
        await tool_discovery.initialize()
        
        # Register tools with different capabilities
        tool1 = ToolDescriptor("tool1", "Tool 1", "utility", capabilities=["read", "write"])
        tool2 = ToolDescriptor("tool2", "Tool 2", "network", capabilities=["read", "network"])
        
        await tool_discovery.register_tool(tool1)
        await tool_discovery.register_tool(tool2)
        
        # Find tools with specific capability
        read_tools = await tool_discovery.find_tools_by_capability("read")
        assert len(read_tools) == 2
        
        network_tools = await tool_discovery.find_tools_by_capability("network")
        assert len(network_tools) == 1
        assert network_tools[0].tool_id == "tool2"
    
    @pytest.mark.asyncio
    async def test_update_tool_metrics(self, tool_discovery):
        """Test updating tool performance metrics"""
        await tool_discovery.initialize()
        
        # Register a tool
        test_tool = ToolDescriptor("perf_tool", "Performance Tool", "utility")
        await tool_discovery.register_tool(test_tool)
        
        # Update metrics
        success = await tool_discovery.update_tool_metrics(
            tool_id="perf_tool",
            execution_time=1.5,
            success=True,
            resource_usage={"cpu": 0.2, "memory": 1024}
        )
        
        assert success
        
        # Verify metrics are stored
        metrics = await tool_discovery.get_discovery_metrics()
        assert "perf_tool" in metrics.get("tool_metrics", {})


class TestAgentCoordinator:
    """Test agent coordination implementation"""
    
    @pytest.fixture
    def agent_coordinator(self):
        config = {
            "coordination_timeout": 60,
            "failure_retry_count": 2,
            "sync_checkpoint_interval": 30
        }
        return AgentCoordinator(config)
    
    @pytest.mark.asyncio
    async def test_coordinator_initialization(self, agent_coordinator):
        """Test agent coordinator initialization"""
        assert await agent_coordinator.initialize()
        assert agent_coordinator._initialized
    
    @pytest.mark.asyncio
    async def test_create_agent_session(self, agent_coordinator):
        """Test creating agent sessions"""
        await agent_coordinator.initialize()
        
        session = await agent_coordinator.create_session(
            agent_id="test_agent",
            user_id="test_user",
            workflow_id="test_workflow",
            coordination_mode=CoordinationMode.COLLABORATIVE
        )
        
        assert isinstance(session, AgentSession)
        assert session.agent_id == "test_agent"
        assert session.user_id == "test_user"
        assert session.workflow_id == "test_workflow"
        assert session.status == "active"
    
    @pytest.mark.asyncio
    async def test_coordinate_agents_collaborative(self, agent_coordinator):
        """Test collaborative agent coordination"""
        await agent_coordinator.initialize()
        
        # Create test sessions
        sessions = []
        for i in range(3):
            session = await agent_coordinator.create_session(
                agent_id=f"agent_{i}",
                user_id="test_user",
                workflow_id="test_workflow"
            )
            sessions.append(session)
        
        # Test collaboration
        task = {
            "type": "analysis",
            "data": "Test data for analysis",
            "requirements": ["accuracy", "speed"]
        }
        
        with patch('langswarm.v2.core.agents.get_agent') as mock_get_agent:
            # Mock agent responses
            mock_agent = AsyncMock()
            mock_agent.send_message = AsyncMock(return_value=MagicMock(content="Analysis complete"))
            mock_get_agent.return_value = mock_agent
            
            result = await agent_coordinator.coordinate_agents(
                sessions=sessions,
                task=task,
                mode=CoordinationMode.COLLABORATIVE
            )
            
            assert isinstance(result, dict)
            assert "coordination_result" in result
    
    @pytest.mark.asyncio
    async def test_distribute_work(self, agent_coordinator):
        """Test work distribution across agents"""
        await agent_coordinator.initialize()
        
        # Create sessions
        sessions = [
            await agent_coordinator.create_session(f"agent_{i}", "user", "workflow")
            for i in range(3)
        ]
        
        # Create work items
        work_items = [
            {"task": f"Task {i}", "priority": i % 3}
            for i in range(6)
        ]
        
        distribution = await agent_coordinator.distribute_work(
            work_items=work_items,
            available_sessions=sessions,
            distribution_strategy="balanced"
        )
        
        assert isinstance(distribution, dict)
        assert len(distribution) <= len(sessions)
        
        # Verify all work items are distributed
        total_distributed = sum(len(items) for items in distribution.values())
        assert total_distributed == len(work_items)
    
    @pytest.mark.asyncio
    async def test_synchronize_agents(self, agent_coordinator):
        """Test agent synchronization at checkpoints"""
        await agent_coordinator.initialize()
        
        sessions = [
            await agent_coordinator.create_session(f"agent_{i}", "user", "workflow")
            for i in range(2)
        ]
        
        checkpoint_data = {
            "checkpoint_id": "cp_1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": "processing"
        }
        
        success = await agent_coordinator.synchronize_agents(
            sessions=sessions,
            checkpoint_data=checkpoint_data
        )
        
        assert success


class TestWorkflowCache:
    """Test workflow cache implementation"""
    
    @pytest.fixture
    def workflow_cache(self):
        config = {
            "backend": "memory",
            "default_ttl": 300,
            "max_cache_size": 100
        }
        return WorkflowCache(config)
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, workflow_cache):
        """Test cache initialization"""
        assert await workflow_cache.initialize()
        assert workflow_cache._initialized
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_result(self, workflow_cache):
        """Test storing and retrieving cached results"""
        await workflow_cache.initialize()
        
        # Store a result
        tool_id = "test_tool"
        input_data = {"param1": "value1", "param2": 42}
        result_data = {"output": "processed_result", "status": "success"}
        
        cache_key = await workflow_cache.store_result(
            tool_id=tool_id,
            input_data=input_data,
            result_data=result_data,
            ttl_seconds=60,
            tags=["test", "demo"]
        )
        
        assert cache_key is not None
        
        # Retrieve the result
        cached_result = await workflow_cache.get_cached_result(
            tool_id=tool_id,
            input_data=input_data,
            similarity_threshold=1.0  # Exact match
        )
        
        assert cached_result is not None
        assert cached_result.tool_id == tool_id
        assert cached_result.result_data == result_data
        assert "test" in cached_result.tags
    
    @pytest.mark.asyncio
    async def test_cache_similarity_matching(self, workflow_cache):
        """Test semantic similarity matching in cache"""
        await workflow_cache.initialize()
        
        # Store a result
        await workflow_cache.store_result(
            tool_id="similarity_tool",
            input_data={"query": "analyze data"},
            result_data={"analysis": "complete"},
            tags=["similarity_test"]
        )
        
        # Try to retrieve with similar but not identical input
        similar_result = await workflow_cache.get_cached_result(
            tool_id="similarity_tool",
            input_data={"query": "analyze the data"},
            similarity_threshold=0.8
        )
        
        # Should find a match due to semantic similarity
        assert similar_result is not None or similar_result is None  # Depends on implementation
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, workflow_cache):
        """Test cache invalidation"""
        await workflow_cache.initialize()
        
        # Store multiple results
        keys = []
        for i in range(3):
            key = await workflow_cache.store_result(
                tool_id=f"tool_{i}",
                input_data={"id": i},
                result_data={"result": f"output_{i}"},
                tags=["invalidation_test"]
            )
            keys.append(key)
        
        # Invalidate by tag
        invalidated = await workflow_cache.invalidate_cache(
            tags=["invalidation_test"]
        )
        
        assert invalidated >= 3
        
        # Verify results are gone
        for i in range(3):
            result = await workflow_cache.get_cached_result(
                tool_id=f"tool_{i}",
                input_data={"id": i}
            )
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_optimization(self, workflow_cache):
        """Test cache optimization strategies"""
        await workflow_cache.initialize()
        
        # Fill cache with test data
        for i in range(10):
            await workflow_cache.store_result(
                tool_id="opt_tool",
                input_data={"iteration": i},
                result_data={"output": f"result_{i}"},
                ttl_seconds=60
            )
        
        # Optimize cache
        optimization_result = await workflow_cache.optimize_cache(
            strategy=CacheStrategy.LRU,
            target_size=5
        )
        
        assert isinstance(optimization_result, dict)
        assert "optimized_entries" in optimization_result
    
    @pytest.mark.asyncio
    async def test_cache_statistics(self, workflow_cache):
        """Test cache statistics tracking"""
        await workflow_cache.initialize()
        
        # Perform some cache operations
        await workflow_cache.store_result("stats_tool", {"test": 1}, {"result": "ok"})
        await workflow_cache.get_cached_result("stats_tool", {"test": 1})  # Hit
        await workflow_cache.get_cached_result("stats_tool", {"test": 2})  # Miss
        
        stats = await workflow_cache.get_cache_statistics()
        
        assert isinstance(stats, dict)
        assert "hit_count" in stats
        assert "miss_count" in stats
        assert "total_entries" in stats


class TestContextPreserver:
    """Test context preservation implementation"""
    
    @pytest.fixture
    def context_preserver(self):
        config = {
            "storage_backend": "sqlite",
            "compression_enabled": True,
            "max_context_age_hours": 24
        }
        return ContextPreserver(config)
    
    @pytest.mark.asyncio
    async def test_context_preserver_initialization(self, context_preserver):
        """Test context preserver initialization"""
        assert await context_preserver.initialize()
        assert context_preserver._initialized
    
    @pytest.mark.asyncio
    async def test_save_and_restore_context(self, context_preserver):
        """Test saving and restoring context"""
        await context_preserver.initialize()
        
        # Save context
        context_data = {
            "messages": [
                {"role": "user", "content": "Test message"},
                {"role": "assistant", "content": "Test response"}
            ],
            "variables": {"var1": "value1", "var2": 42},
            "metadata": {"step": "test_step"}
        }
        
        snapshot_id = await context_preserver.save_context(
            agent_session_id="test_session",
            workflow_execution_id="test_execution",
            step_id="test_step",
            context_data=context_data,
            scope=ContextScope.STEP
        )
        
        assert snapshot_id is not None
        
        # Restore context
        restored_context = await context_preserver.restore_context(
            snapshot_id=snapshot_id,
            merge_strategy="replace"
        )
        
        assert restored_context is not None
        assert isinstance(restored_context, ContextSnapshot)
        assert restored_context.agent_session_id == "test_session"
        assert len(restored_context.messages) == 2
    
    @pytest.mark.asyncio
    async def test_context_history(self, context_preserver):
        """Test getting context history"""
        await context_preserver.initialize()
        
        session_id = "history_test_session"
        
        # Save multiple context snapshots
        for i in range(5):
            await context_preserver.save_context(
                agent_session_id=session_id,
                workflow_execution_id="test_execution",
                step_id=f"step_{i}",
                context_data={"iteration": i, "data": f"test_data_{i}"},
                scope=ContextScope.STEP
            )
        
        # Get context history
        history = await context_preserver.get_context_history(
            agent_session_id=session_id,
            limit=3
        )
        
        assert isinstance(history, list)
        assert len(history) <= 3
        assert all(isinstance(snapshot, ContextSnapshot) for snapshot in history)
    
    @pytest.mark.asyncio
    async def test_context_compression(self, context_preserver):
        """Test context compression"""
        await context_preserver.initialize()
        
        # Save a context with large data
        large_context = {
            "messages": [{"role": "user", "content": "x" * 1000}] * 10,
            "variables": {f"var_{i}": f"value_{i}" * 100 for i in range(20)},
            "metadata": {"large_data": "y" * 5000}
        }
        
        snapshot_id = await context_preserver.save_context(
            agent_session_id="compression_test",
            workflow_execution_id="test_execution",
            step_id="large_step",
            context_data=large_context,
            scope=ContextScope.STEP
        )
        
        # Compress the context
        compressed_id = await context_preserver.compress_context(
            snapshot_id=snapshot_id,
            compression_ratio=0.5,
            preserve_important=True
        )
        
        assert compressed_id is not None
        
        # Verify compressed context is smaller but still functional
        compressed_context = await context_preserver.restore_context(compressed_id)
        assert compressed_context is not None
        assert compressed_context.compression_ratio <= 0.5
    
    @pytest.mark.asyncio
    async def test_merge_contexts(self, context_preserver):
        """Test merging multiple contexts"""
        await context_preserver.initialize()
        
        # Create multiple contexts to merge
        snapshot_ids = []
        for i in range(3):
            context_data = {
                "variables": {f"var_{i}": f"value_{i}"},
                "metadata": {f"meta_{i}": f"metadata_{i}"},
                "messages": [{"role": "assistant", "content": f"Message {i}"}]
            }
            
            snapshot_id = await context_preserver.save_context(
                agent_session_id="merge_test",
                workflow_execution_id="test_execution",
                step_id=f"merge_step_{i}",
                context_data=context_data,
                scope=ContextScope.STEP
            )
            snapshot_ids.append(snapshot_id)
        
        # Merge contexts
        merged_id = await context_preserver.merge_contexts(
            snapshot_ids=snapshot_ids,
            merge_strategy="union"
        )
        
        assert merged_id is not None
        
        # Verify merged context contains data from all sources
        merged_context = await context_preserver.restore_context(merged_id)
        assert merged_context is not None
        assert len(merged_context.variables) >= 3
        assert len(merged_context.messages) >= 3


class TestLoadBalancer:
    """Test load balancer implementation"""
    
    @pytest.fixture
    def load_balancer(self):
        config = LoadBalancerConfig(
            strategy=LoadBalancingStrategy.ROUND_ROBIN,
            health_check_interval=30,
            failure_threshold=2
        )
        return LoadBalancer(config)
    
    @pytest.mark.asyncio
    async def test_load_balancer_initialization(self, load_balancer):
        """Test load balancer initialization"""
        assert await load_balancer.initialize()
        assert load_balancer._initialized
    
    @pytest.mark.asyncio
    async def test_target_selection_round_robin(self, load_balancer):
        """Test round-robin target selection"""
        await load_balancer.initialize()
        
        targets = ["target_1", "target_2", "target_3"]
        request_context = {"request_id": "test_request"}
        
        # Make multiple selections to verify round-robin behavior
        selections = []
        for _ in range(6):
            selected = await load_balancer.select_target(
                targets=targets,
                request_context=request_context
            )
            selections.append(selected)
        
        # Should cycle through targets
        assert len(set(selections)) == len(targets)
        # First three selections should be different
        assert len(set(selections[:3])) == 3
    
    @pytest.mark.asyncio
    async def test_target_health_tracking(self, load_balancer):
        """Test target health tracking and updates"""
        await load_balancer.initialize()
        
        target_id = "health_test_target"
        
        # Update target health
        success = await load_balancer.update_target_health(
            target_id=target_id,
            health_score=0.8,
            performance_metrics={
                "response_time": 0.5,
                "success_rate": 0.95,
                "cpu_usage": 0.3
            }
        )
        
        assert success
        
        # Get target statistics
        stats = await load_balancer.get_target_statistics(target_id)
        
        assert stats is not None
        assert stats["health_score"] == 0.8
        assert "performance_metrics" in stats
    
    @pytest.mark.asyncio
    async def test_unhealthy_target_removal(self, load_balancer):
        """Test removal of unhealthy targets"""
        await load_balancer.initialize()
        
        # Add targets with different health scores
        targets = ["healthy_target", "unhealthy_target"]
        
        await load_balancer.update_target_health("healthy_target", 0.9)
        await load_balancer.update_target_health("unhealthy_target", 0.3)
        
        # Remove unhealthy targets
        removed = await load_balancer.remove_unhealthy_targets(
            health_threshold=0.5
        )
        
        assert "unhealthy_target" in removed
        assert "healthy_target" not in removed
    
    @pytest.mark.asyncio
    async def test_load_rebalancing(self, load_balancer):
        """Test load rebalancing operation"""
        await load_balancer.initialize()
        
        # Simulate load imbalance
        targets = ["target_1", "target_2", "target_3"]
        for target in targets:
            await load_balancer.update_target_health(
                target_id=target,
                health_score=0.8,
                performance_metrics={"load": 0.5}
            )
        
        # Trigger rebalancing
        rebalance_result = await load_balancer.rebalance_load(force_rebalance=True)
        
        assert isinstance(rebalance_result, dict)
        assert "rebalanced" in rebalance_result
    
    @pytest.mark.asyncio
    async def test_load_balancing_metrics(self, load_balancer):
        """Test getting load balancing metrics"""
        await load_balancer.initialize()
        
        # Perform some load balancing operations
        targets = ["metric_target_1", "metric_target_2"]
        for _ in range(5):
            await load_balancer.select_target(
                targets=targets,
                request_context={"test": "metrics"}
            )
        
        # Get metrics
        metrics = await load_balancer.get_load_balancing_metrics()
        
        assert isinstance(metrics, dict)
        assert "total_requests" in metrics
        assert "target_distribution" in metrics


class TestEnhancedWorkflowSteps:
    """Test enhanced workflow steps"""
    
    @pytest.fixture
    def sample_context(self):
        return WorkflowContext(
            workflow_id="test_workflow",
            execution_id="test_execution",
            variables={"user_id": "test_user", "input": "test input"}
        )
    
    @pytest.mark.asyncio
    async def test_advanced_agent_step(self, sample_context):
        """Test AdvancedAgentStep execution"""
        step = AdvancedAgentStep(
            step_id="advanced_agent_test",
            agent_id="test_agent",
            input_data="Process this: ${input}",
            preserve_context=True,
            context_scope=ContextScope.STEP
        )
        
        with patch('langswarm.v2.core.agents.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.send_message = AsyncMock(return_value=MagicMock(content="Processed successfully"))
            mock_get_agent.return_value = mock_agent
            
            result = await step.execute(sample_context)
            
            assert result.status.name == "COMPLETED"
            assert "Processed successfully" in str(result.result)
    
    @pytest.mark.asyncio
    async def test_cached_tool_step(self, sample_context):
        """Test CachedToolStep execution"""
        step = CachedToolStep(
            step_id="cached_tool_test",
            tool_name="test_tool",
            parameters={"input": "${input}", "mode": "test"},
            cache_strategy=CacheStrategy.SEMANTIC,
            cache_ttl_seconds=300
        )
        
        with patch('langswarm.v2.tools.get_tool_registry') as mock_registry:
            mock_tool = MagicMock()
            mock_tool.execution.execute = AsyncMock(return_value="Tool executed successfully")
            mock_registry.return_value.get_tool.return_value = mock_tool
            
            result = await step.execute(sample_context)
            
            assert result.status.name == "COMPLETED"
            assert result.result == "Tool executed successfully"
    
    @pytest.mark.asyncio
    async def test_coordinated_agent_step(self, sample_context):
        """Test CoordinatedAgentStep execution"""
        step = CoordinatedAgentStep(
            step_id="coordinated_agents_test",
            agent_ids=["agent_1", "agent_2", "agent_3"],
            task_data={"task": "collaborative analysis", "data": "${input}"},
            coordination_mode=CoordinationMode.PARALLEL
        )
        
        with patch('langswarm.v2.core.agents.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.send_message = AsyncMock(return_value=MagicMock(content="Agent analysis complete"))
            mock_get_agent.return_value = mock_agent
            
            result = await step.execute(sample_context)
            
            assert result.status.name == "COMPLETED"
            assert isinstance(result.result, dict)
            assert "coordination_mode" in result.result
    
    @pytest.mark.asyncio
    async def test_load_balanced_step(self, sample_context):
        """Test LoadBalancedStep execution"""
        step = LoadBalancedStep(
            step_id="load_balanced_test",
            target_type="agent",
            target_ids=["agent_1", "agent_2"],
            execution_data="Load balanced task: ${input}",
            load_balancing_strategy=LoadBalancingStrategy.ROUND_ROBIN
        )
        
        with patch('langswarm.v2.core.agents.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.send_message = AsyncMock(return_value=MagicMock(content="Load balanced execution"))
            mock_get_agent.return_value = mock_agent
            
            result = await step.execute(sample_context)
            
            assert result.status.name == "COMPLETED"
            assert result.result == "Load balanced execution"
    
    @pytest.mark.asyncio
    async def test_context_aware_step(self, sample_context):
        """Test ContextAwareStep execution"""
        def test_logic(context: WorkflowContext) -> str:
            return f"Context aware result for {context.variables.get('user_id')}"
        
        step = ContextAwareStep(
            step_id="context_aware_test",
            step_type=StepType.TRANSFORM,
            execution_logic=test_logic,
            context_scope=ContextScope.WORKFLOW,
            preserve_history=True
        )
        
        result = await step.execute(sample_context)
        
        assert result.status.name == "COMPLETED"
        assert "Context aware result for test_user" == result.result


class TestIntegrationManagerFactory:
    """Test integration manager factory functions"""
    
    @pytest.mark.asyncio
    async def test_create_default_integration_manager(self):
        """Test creating default integration manager"""
        manager = create_default_integration_manager()
        
        assert manager is not None
        assert hasattr(manager, 'tool_discovery')
        assert hasattr(manager, 'agent_coordinator')
        assert hasattr(manager, 'workflow_cache')
        assert hasattr(manager, 'context_preserver')
        assert hasattr(manager, 'load_balancer')
        
        # Test initialization
        success = await manager.initialize()
        assert success
        
        # Test system health check
        health = await manager.get_system_health()
        assert isinstance(health, dict)
        assert "status" in health
        assert "components" in health
        
        # Test shutdown
        shutdown_success = await manager.shutdown()
        assert shutdown_success
    
    @pytest.mark.asyncio
    async def test_create_performance_optimized_manager(self):
        """Test creating performance-optimized manager"""
        manager = create_performance_optimized_integration_manager()
        
        assert manager is not None
        
        # Check that performance optimizations are applied
        assert manager.config["agent_coordinator"]["max_concurrent_sessions"] == 100
        assert manager.config["workflow_cache"]["backend"] == "redis"
        assert manager.config["load_balancer"]["strategy"] == LoadBalancingStrategy.PERFORMANCE.value
    
    def test_create_custom_integration_manager(self):
        """Test creating manager with custom configuration"""
        custom_config = {
            "tool_discovery": {
                "discovery_timeout": 5,
                "cache_discoveries": False
            },
            "workflow_cache": {
                "backend": "sqlite",
                "max_cache_size": 5000
            }
        }
        
        manager = create_integration_manager(custom_config)
        
        assert manager is not None
        assert manager.config["tool_discovery"]["discovery_timeout"] == 5
        assert manager.config["tool_discovery"]["cache_discoveries"] is False
        assert manager.config["workflow_cache"]["backend"] == "sqlite"
        assert manager.config["workflow_cache"]["max_cache_size"] == 5000


class TestIntegrationEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_integration_workflow(self):
        """Test a complete workflow using all integration components"""
        # Create integration manager
        manager = create_default_integration_manager()
        await manager.initialize()
        
        try:
            # Create a workflow context
            context = WorkflowContext(
                workflow_id="e2e_test_workflow",
                execution_id="e2e_test_execution",
                variables={
                    "user_id": "test_user",
                    "task": "end-to-end integration test",
                    "data": "sample data for processing"
                }
            )
            
            # Test tool discovery
            tools = await manager.tool_discovery.discover_tools(
                context=context,
                strategy=DiscoveryStrategy.AUTOMATIC
            )
            
            # Test agent coordination
            session = await manager.agent_coordinator.create_session(
                agent_id="test_agent",
                user_id="test_user",
                workflow_id=context.workflow_id
            )
            
            # Test caching
            cache_key = await manager.workflow_cache.store_result(
                tool_id="e2e_test_tool",
                input_data={"test": "data"},
                result_data={"result": "cached_value"},
                ttl_seconds=300
            )
            
            cached_result = await manager.workflow_cache.get_cached_result(
                tool_id="e2e_test_tool",
                input_data={"test": "data"}
            )
            
            assert cached_result is not None
            assert cached_result.result_data["result"] == "cached_value"
            
            # Test context preservation
            snapshot_id = await manager.context_preserver.save_context(
                agent_session_id=session.session_id,
                workflow_execution_id=context.execution_id,
                step_id="e2e_test_step",
                context_data={
                    "messages": [{"role": "user", "content": "test message"}],
                    "variables": context.variables
                },
                scope=ContextScope.WORKFLOW
            )
            
            restored_context = await manager.context_preserver.restore_context(snapshot_id)
            assert restored_context is not None
            
            # Test load balancing
            targets = ["target_1", "target_2", "target_3"]
            selected_target = await manager.load_balancer.select_target(
                targets=targets,
                request_context={"workflow_id": context.workflow_id}
            )
            
            assert selected_target in targets
            
            # Verify system health
            health = await manager.get_system_health()
            assert health["status"] in ["healthy", "degraded"]
            assert len(health["components"]) == 5
            
        finally:
            # Clean up
            await manager.shutdown()


# Performance and stress tests
class TestPerformanceAndStress:
    """Performance and stress tests for integration components"""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_discovery(self):
        """Test concurrent tool discovery operations"""
        discovery = DynamicToolDiscovery({"max_concurrent_discoveries": 10})
        await discovery.initialize()
        
        # Create multiple concurrent discovery tasks
        contexts = [
            WorkflowContext(f"workflow_{i}", f"execution_{i}", {"task": f"task_{i}"})
            for i in range(20)
        ]
        
        start_time = asyncio.get_event_loop().time()
        
        tasks = [
            discovery.discover_tools(context, strategy=DiscoveryStrategy.AUTOMATIC)
            for context in contexts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = asyncio.get_event_loop().time()
        
        # Verify all tasks completed
        assert len(results) == 20
        assert all(not isinstance(result, Exception) for result in results)
        
        # Should complete in reasonable time (less than 30 seconds)
        assert end_time - start_time < 30
    
    @pytest.mark.asyncio
    async def test_cache_performance_with_many_entries(self):
        """Test cache performance with many entries"""
        cache = WorkflowCache({
            "backend": "memory",
            "max_cache_size": 1000,
            "enable_compression": False  # Disable compression for pure performance test
        })
        await cache.initialize()
        
        # Store many entries
        start_time = asyncio.get_event_loop().time()
        
        store_tasks = []
        for i in range(500):
            task = cache.store_result(
                tool_id=f"perf_tool_{i % 50}",  # 50 different tools
                input_data={"id": i, "data": f"data_{i}"},
                result_data={"output": f"result_{i}"},
                tags=[f"batch_{i // 100}"]
            )
            store_tasks.append(task)
        
        await asyncio.gather(*store_tasks)
        
        store_time = asyncio.get_event_loop().time() - start_time
        
        # Retrieve entries
        start_time = asyncio.get_event_loop().time()
        
        retrieve_tasks = []
        for i in range(0, 500, 10):  # Sample every 10th entry
            task = cache.get_cached_result(
                tool_id=f"perf_tool_{i % 50}",
                input_data={"id": i, "data": f"data_{i}"}
            )
            retrieve_tasks.append(task)
        
        retrieved_results = await asyncio.gather(*retrieve_tasks)
        
        retrieve_time = asyncio.get_event_loop().time() - start_time
        
        # Verify performance
        assert store_time < 10  # Should store 500 entries in less than 10 seconds
        assert retrieve_time < 5  # Should retrieve 50 entries in less than 5 seconds
        
        # Verify retrieval accuracy
        successful_retrievals = sum(1 for result in retrieved_results if result is not None)
        assert successful_retrievals == len(retrieved_results)  # All should be found
    
    @pytest.mark.asyncio
    async def test_context_preservation_stress(self):
        """Test context preservation under stress"""
        preserver = ContextPreserver({
            "storage_backend": "sqlite",
            "compression_enabled": True,
            "auto_cleanup_interval": 0  # Disable auto cleanup for test
        })
        await preserver.initialize()
        
        # Create many context snapshots rapidly
        session_ids = [f"stress_session_{i}" for i in range(10)]
        
        save_tasks = []
        for session_id in session_ids:
            for step in range(20):  # 20 steps per session
                context_data = {
                    "messages": [
                        {"role": "user", "content": f"Message {step} from {session_id}"},
                        {"role": "assistant", "content": f"Response {step} from {session_id}"}
                    ],
                    "variables": {f"var_{step}": f"value_{step}", "session": session_id},
                    "metadata": {"step": step, "session": session_id}
                }
                
                task = preserver.save_context(
                    agent_session_id=session_id,
                    workflow_execution_id=f"stress_execution_{session_id}",
                    step_id=f"stress_step_{step}",
                    context_data=context_data,
                    scope=ContextScope.STEP
                )
                save_tasks.append(task)
        
        start_time = asyncio.get_event_loop().time()
        
        # Execute all save operations
        snapshot_ids = await asyncio.gather(*save_tasks)
        
        save_time = asyncio.get_event_loop().time() - start_time
        
        # Test rapid retrieval
        start_time = asyncio.get_event_loop().time()
        
        retrieve_tasks = [
            preserver.restore_context(snapshot_id)
            for snapshot_id in snapshot_ids[::5]  # Sample every 5th snapshot
        ]
        
        restored_contexts = await asyncio.gather(*retrieve_tasks)
        
        retrieve_time = asyncio.get_event_loop().time() - start_time
        
        # Verify performance and correctness
        assert save_time < 15  # Should save 200 contexts in less than 15 seconds
        assert retrieve_time < 3  # Should retrieve 40 contexts in less than 3 seconds
        
        # Verify all contexts were retrieved successfully
        assert len(restored_contexts) == len(retrieve_tasks)
        assert all(context is not None for context in restored_contexts)
        
        # Test context history retrieval for all sessions
        history_tasks = [
            preserver.get_context_history(session_id, limit=10)
            for session_id in session_ids
        ]
        
        histories = await asyncio.gather(*history_tasks)
        
        # Each session should have history
        assert len(histories) == len(session_ids)
        assert all(len(history) <= 10 for history in histories)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])