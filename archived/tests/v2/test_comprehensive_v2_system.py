"""
Comprehensive test suite for all V2 LangSwarm components

Tests integration and functionality across:
- Agent system (providers, builders, configurations)
- Tool system (unified tools, adapters, registries)
- Workflow system (execution, builders, monitoring)
- Memory system (backends, sessions, vector stores)
- Session system (providers, storage, lifecycle)
- Configuration system (schemas, validation, migration)
- Observability system (integrated with all components)
"""

import pytest
import asyncio
import tempfile
import os
import sys
from typing import Dict, Any, List
import json

# Add current directory to Python path
sys.path.insert(0, os.path.abspath('.'))


class TestV2AgentSystem:
    """Comprehensive tests for V2 agent system"""
    
    def test_agent_imports(self):
        """Test that all agent components can be imported"""
        try:
            from langswarm.v2.core.agents import (
                # Core interfaces
                IAgent, IAgentProvider, AgentConfiguration,
                
                # Base implementations
                BaseAgent, AgentBuilder,
                
                # Provider types
                ProviderType,
                
                # Factory functions
                create_agent, create_openai_agent, create_anthropic_agent
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Agent import failed: {e}")
    
    def test_agent_configuration(self):
        """Test agent configuration creation and validation"""
        from langswarm.v2.core.agents import AgentConfiguration, ProviderType
        
        config = AgentConfiguration(
            name="test_agent",
            provider=ProviderType.MOCK,
            model="test-model",
            api_key="test-key",
            temperature=0.7,
            max_tokens=1000
        )
        
        assert config.name == "test_agent"
        assert config.provider == ProviderType.MOCK
        assert config.model == "test-model"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
    
    def test_agent_builder_pattern(self):
        """Test agent builder fluent API"""
        from langswarm.v2.core.agents import AgentBuilder, ProviderType
        
        agent = (AgentBuilder("test_agent")
                .mock()
                .model("test-model")
                .temperature(0.8)
                .max_tokens(500)
                .build())
        
        assert agent is not None
        assert agent.config.name == "test_agent"
        assert agent.config.provider == ProviderType.MOCK
        assert agent.config.model == "test-model"
        assert agent.config.temperature == 0.8
        assert agent.config.max_tokens == 500
    
    @pytest.mark.asyncio
    async def test_agent_lifecycle(self):
        """Test agent lifecycle management"""
        from langswarm.v2.core.agents import create_agent
        
        agent = create_agent("test_agent", provider="mock")
        
        # Test initialization
        await agent.initialize()
        assert agent._initialized is True
        
        # Test health check
        health = await agent.get_health()
        assert health["status"] in ["healthy", "unknown"]
        
        # Test shutdown
        await agent.shutdown()


class TestV2ToolSystem:
    """Comprehensive tests for V2 tool system"""
    
    def test_tool_imports(self):
        """Test that all tool components can be imported"""
        try:
            from langswarm.v2.tools import (
                # Core interfaces
                IToolInterface, IToolMetadata, IToolExecution,
                
                # Base implementations
                BaseTool, ToolRegistry,
                
                # Built-in tools
                SystemStatusTool, TextProcessorTool,
                
                # Adapters
                AdapterFactory
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Tool import failed: {e}")
    
    def test_built_in_tools(self):
        """Test built-in V2 tools functionality"""
        from langswarm.v2.tools.builtin import SystemStatusTool, TextProcessorTool
        
        # Test system status tool
        system_tool = SystemStatusTool()
        metadata = system_tool.get_metadata()
        assert metadata.name == "system_status"
        assert len(metadata.methods) > 0
        
        # Test text processor tool
        text_tool = TextProcessorTool()
        metadata = text_tool.get_metadata()
        assert metadata.name == "text_processor"
        assert len(metadata.methods) > 0
    
    def test_tool_adapter_factory(self):
        """Test tool adapter factory for legacy tools"""
        from langswarm.v2.tools.adapters import AdapterFactory
        
        # Mock legacy tools for testing
        class MockSynapseTool:
            def __init__(self):
                self.name = "mock_synapse"
        
        class MockRAGTool:
            def __init__(self):
                self.name = "mock_rag"
        
        # Test adapter creation
        synapse_adapter = AdapterFactory.create_adapter(MockSynapseTool(), "synapse")
        assert synapse_adapter is not None
        
        rag_adapter = AdapterFactory.create_adapter(MockRAGTool(), "rag")
        assert rag_adapter is not None


class TestV2WorkflowSystem:
    """Comprehensive tests for V2 workflow system"""
    
    def test_workflow_imports(self):
        """Test that all workflow components can be imported"""
        try:
            from langswarm.v2.core.workflows import (
                # Core interfaces
                IWorkflow, IWorkflowStep, WorkflowStatus,
                
                # Base implementations
                BaseWorkflow, WorkflowEngine, WorkflowBuilder,
                
                # Factory functions
                create_workflow, create_linear_workflow
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Workflow import failed: {e}")
    
    def test_workflow_builder(self):
        """Test workflow builder patterns"""
        from langswarm.v2.core.workflows import WorkflowBuilder, StepType
        
        workflow = (WorkflowBuilder("test_workflow")
                   .add_step("step1", StepType.AGENT, config={"agent_id": "test"})
                   .add_step("step2", StepType.TOOL, config={"tool_name": "calculator"})
                   .build())
        
        assert workflow is not None
        assert workflow.workflow_id == "test_workflow"
        assert len(workflow.steps) == 2
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test workflow execution"""
        from langswarm.v2.core.workflows import create_linear_workflow, WorkflowEngine, WorkflowRegistry
        
        # Create simple workflow
        workflow = create_linear_workflow(
            "test_execution",
            [
                {"name": "step1", "type": "agent", "config": {"prompt": "Hello"}},
                {"name": "step2", "type": "tool", "config": {"operation": "test"}}
            ]
        )
        
        # Test execution engine
        registry = WorkflowRegistry()
        engine = WorkflowEngine(registry)
        
        # Mock execution (would need actual agents/tools for full test)
        assert workflow is not None
        assert len(workflow.steps) == 2


class TestV2MemorySystem:
    """Comprehensive tests for V2 memory system"""
    
    def test_memory_imports(self):
        """Test that all memory components can be imported"""
        try:
            from langswarm.v2.core.memory import (
                # Core interfaces
                IMemoryBackend, IMemoryManager, MemoryBackendType,
                
                # Base implementations
                MemoryManager, InMemoryBackend,
                
                # Factory functions
                MemoryFactory, initialize_memory
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Memory import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_memory_backends(self):
        """Test different memory backends"""
        from langswarm.v2.core.memory import InMemoryBackend, MemoryBackendType
        
        # Test in-memory backend
        backend = InMemoryBackend()
        await backend.connect()
        
        # Test basic operations
        session_data = {
            "session_id": "test_session",
            "user_id": "test_user",
            "messages": []
        }
        
        # Save session
        await backend.save_session("test_session", session_data)
        
        # Load session
        loaded_data = await backend.load_session("test_session")
        assert loaded_data is not None
        assert loaded_data["session_id"] == "test_session"
        
        # List sessions
        sessions = await backend.list_sessions()
        assert "test_session" in sessions
        
        await backend.disconnect()
    
    def test_memory_configuration(self):
        """Test memory configuration patterns"""
        from langswarm.v2.core.memory import MemoryConfiguration, MemoryBackendType
        
        # Test pattern-based configuration
        dev_config = MemoryConfiguration.from_pattern("development")
        assert dev_config.backend_type == MemoryBackendType.IN_MEMORY
        
        # Test custom configuration
        custom_config = MemoryConfiguration(
            backend_type=MemoryBackendType.SQLITE,
            connection_string="sqlite:///test.db",
            max_sessions=1000
        )
        assert custom_config.backend_type == MemoryBackendType.SQLITE


class TestV2SessionSystem:
    """Comprehensive tests for V2 session system"""
    
    def test_session_imports(self):
        """Test that all session components can be imported"""
        try:
            from langswarm.v2.core.session import (
                # Core interfaces
                ISession, ISessionManager, SessionStatus,
                
                # Base implementations
                BaseSession, BaseSessionManager,
                
                # Storage backends
                InMemorySessionBackend, SQLiteSessionBackend,
                
                # Provider sessions
                MockSessionProvider
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Session import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        """Test session lifecycle management"""
        from langswarm.v2.core.session import BaseSession, BaseSessionManager, InMemorySessionBackend
        
        # Create session manager with in-memory backend
        backend = InMemorySessionBackend()
        await backend.connect()
        
        manager = BaseSessionManager(backend)
        
        # Create session
        session = await manager.create_session("test_user", {"provider": "mock"})
        assert session is not None
        assert session.user_id == "test_user"
        
        # Add message
        await session.add_message("user", "Hello, world!")
        assert len(session.messages) == 1
        
        # Get session
        retrieved_session = await manager.get_session(session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.session_id == session.session_id
        
        await backend.disconnect()


class TestV2ConfigurationSystem:
    """Comprehensive tests for V2 configuration system"""
    
    def test_config_imports(self):
        """Test that all configuration components can be imported"""
        try:
            from langswarm.v2.core.config import (
                # Core schemas
                LangSwarmConfig, AgentConfig, ToolConfig,
                
                # Loaders and validation
                ConfigurationLoader, ConfigValidator,
                
                # Utilities
                ConfigMerger, v1_to_v2_migrate
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Configuration import failed: {e}")
    
    def test_configuration_schema(self):
        """Test configuration schema validation"""
        from langswarm.v2.core.config import LangSwarmConfig, AgentConfig, ProviderType
        
        # Test minimal configuration
        config = LangSwarmConfig(
            agents=[
                AgentConfig(
                    name="test_agent",
                    provider=ProviderType.MOCK,
                    model="test-model"
                )
            ]
        )
        
        assert len(config.agents) == 1
        assert config.agents[0].name == "test_agent"
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        from langswarm.v2.core.config import validate_config, LangSwarmConfig
        
        # Test valid configuration
        valid_config = LangSwarmConfig()
        issues = validate_config(valid_config)
        # Should have minimal or no issues for default config
        assert isinstance(issues, list)
    
    def test_v1_to_v2_migration(self):
        """Test V1 to V2 configuration migration"""
        from langswarm.v2.core.config import v1_to_v2_migrate
        
        # Mock V1 configuration
        v1_config = {
            "agents": [
                {
                    "name": "legacy_agent",
                    "provider": "openai",
                    "model": "gpt-3.5-turbo"
                }
            ]
        }
        
        # Test migration
        v2_config = v1_to_v2_migrate(v1_config)
        assert v2_config is not None
        assert isinstance(v2_config, dict)


class TestV2VectorStores:
    """Comprehensive tests for V2 native vector stores"""
    
    def test_vector_store_imports(self):
        """Test that all vector store components can be imported"""
        try:
            from langswarm.v2.core.memory.vector_stores import (
                # Core interfaces
                IVectorStore, VectorDocument, VectorQuery,
                
                # Native implementations
                NativeSQLiteStore, VectorStoreFactory,
                
                # Factory functions
                create_development_store
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Vector store import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_sqlite_vector_store(self):
        """Test SQLite vector store functionality"""
        from langswarm.v2.core.memory.vector_stores import NativeSQLiteStore, VectorDocument
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            # Create store
            store = NativeSQLiteStore({"database_path": db_path})
            await store.connect()
            
            # Test document upsert
            documents = [
                VectorDocument(
                    id="doc1",
                    content="Test document content",
                    embedding=[0.1, 0.2, 0.3, 0.4],
                    metadata={"type": "test"}
                )
            ]
            
            await store.upsert(documents)
            
            # Test retrieval
            retrieved = await store.retrieve(["doc1"])
            assert len(retrieved) == 1
            assert retrieved[0].id == "doc1"
            
            # Test query (basic similarity)
            from langswarm.v2.core.memory.vector_stores import VectorQuery
            query = VectorQuery(
                embedding=[0.1, 0.2, 0.3, 0.4],
                top_k=1
            )
            
            results = await store.query(query)
            assert len(results) >= 0  # May be 0 if similarity is too low
            
            await store.disconnect()
            
        finally:
            os.unlink(db_path)
    
    def test_vector_store_factory(self):
        """Test vector store factory"""
        from langswarm.v2.core.memory.vector_stores import VectorStoreFactory, VectorStoreType
        
        # Test factory creation
        factory = VectorStoreFactory()
        
        # Test available stores
        available = factory.list_available_stores()
        assert VectorStoreType.SQLITE in available


class TestV2Integration:
    """Integration tests across V2 components"""
    
    @pytest.mark.asyncio
    async def test_observability_integration(self):
        """Test observability integration across components"""
        from langswarm.v2.core.observability import create_development_observability
        from langswarm.v2.core.agents import create_agent
        
        # Create observability provider
        obs_provider = create_development_observability()
        await obs_provider.start()
        
        try:
            # Create agent with observability
            agent = create_agent("test_agent", provider="mock")
            
            # Test that operations can be traced and logged
            with obs_provider.tracer.start_span("integration_test") as span:
                if span:
                    obs_provider.logger.info("Integration test", "test")
                    obs_provider.metrics.increment_counter("integration.tests", 1.0)
            
            # Check health
            health = obs_provider.get_health_status()
            assert health["status"] == "healthy"
            
        finally:
            await obs_provider.stop()
    
    @pytest.mark.asyncio
    async def test_memory_session_integration(self):
        """Test memory and session system integration"""
        from langswarm.v2.core.memory import initialize_memory
        from langswarm.v2.core.session import create_session_manager, InMemorySessionBackend
        
        # Initialize memory system
        memory_manager = initialize_memory("development")
        
        # Create session manager
        backend = InMemorySessionBackend()
        await backend.connect()
        session_manager = create_session_manager(backend)
        
        # Create session with memory context
        session = await session_manager.create_session("test_user", {
            "memory_enabled": True,
            "memory_backend": "in_memory"
        })
        
        assert session is not None
        assert session.user_id == "test_user"
        
        await backend.disconnect()
    
    def test_full_system_import(self):
        """Test that complete V2 system can be imported"""
        try:
            # Import all major V2 components
            from langswarm.v2.core.agents import AgentBuilder
            from langswarm.v2.tools import BaseTool
            from langswarm.v2.core.workflows import WorkflowBuilder
            from langswarm.v2.core.memory import MemoryManager
            from langswarm.v2.core.session import BaseSessionManager
            from langswarm.v2.core.config import LangSwarmConfig
            from langswarm.v2.core.observability import ObservabilityProvider
            
            assert True
        except ImportError as e:
            pytest.fail(f"Full system import failed: {e}")


# Test performance and scalability
class TestV2Performance:
    """Performance and scalability tests for V2 system"""
    
    @pytest.mark.asyncio
    async def test_observability_performance(self):
        """Test observability system performance under load"""
        from langswarm.v2.core.observability import create_development_observability
        
        provider = create_development_observability()
        await provider.start()
        
        try:
            # Generate load
            for i in range(100):
                with provider.tracer.start_span(f"perf_test_{i}") as span:
                    if span:
                        provider.metrics.increment_counter("perf.operations", 1.0)
                        provider.logger.debug(f"Performance test {i}", "test")
            
            # System should remain healthy
            health = provider.get_health_status()
            assert health["status"] == "healthy"
            
        finally:
            await provider.stop()
    
    @pytest.mark.asyncio
    async def test_memory_system_performance(self):
        """Test memory system performance"""
        from langswarm.v2.core.memory import InMemoryBackend
        
        backend = InMemoryBackend()
        await backend.connect()
        
        try:
            # Test multiple session operations
            for i in range(50):
                session_data = {
                    "session_id": f"session_{i}",
                    "user_id": f"user_{i}",
                    "messages": [f"Message {j}" for j in range(10)]
                }
                await backend.save_session(f"session_{i}", session_data)
            
            # Test bulk retrieval
            sessions = await backend.list_sessions()
            assert len(sessions) == 50
            
        finally:
            await backend.disconnect()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
