"""
Comprehensive tests for V2 Agent Memory & Context Management System

Tests the sophisticated memory and context handling capabilities including:
- Persistent conversation memory across sessions
- Context compression and summarization
- Long-term memory with retrieval capabilities
- Context-aware personalization and adaptation
- Memory analytics and usage optimization
"""

import pytest
import asyncio
import tempfile
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

from langswarm.v2.core.agents.interfaces import AgentMessage
from langswarm.v2.core.agents.memory.interfaces import (
    MemoryRecord, ConversationContext, PersonalizationProfile, MemoryInsight,
    MemoryType, ContextScope, CompressionStrategy, RetrievalStrategy, PersonalizationLevel,
    create_agent_memory
)
from langswarm.v2.core.agents.memory.implementations import (
    AgentMemoryManager, ContextManager, MemoryRetrievalEngine,
    PersonalizationEngine, MemoryAnalytics
)


class TestAgentMemoryManager:
    """Test core agent memory management functionality"""
    
    @pytest.fixture
    async def memory_manager(self):
        """Create a test memory manager"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        config = {
            'db_path': db_path,
            'max_records': 1000,
            'embedding_dim': 1536
        }
        
        manager = AgentMemoryManager('test_agent', config)
        await asyncio.sleep(0.1)  # Allow initialization to complete
        
        yield manager
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_memory(self, memory_manager):
        """Test basic memory storage and retrieval"""
        # Create test memory record
        record = MemoryRecord(
            memory_type=MemoryType.EPISODIC,
            content="Test conversation message",
            session_id="session_123",
            user_id="user_456",
            agent_id="test_agent",
            importance_score=0.8,
            tags=["conversation", "test"],
            metadata={"source": "test"}
        )
        
        # Store memory
        success = await memory_manager.store_memory(record)
        assert success
        
        # Retrieve memory
        memories = await memory_manager.retrieve_memories(
            session_id="session_123",
            limit=10
        )
        
        assert len(memories) == 1
        retrieved = memories[0]
        assert retrieved.memory_id == record.memory_id
        assert retrieved.content == "Test conversation message"
        assert retrieved.memory_type == MemoryType.EPISODIC
        assert retrieved.session_id == "session_123"
        assert retrieved.user_id == "user_456"
        assert retrieved.importance_score == 0.8
        assert "conversation" in retrieved.tags
    
    @pytest.mark.asyncio
    async def test_memory_search(self, memory_manager):
        """Test memory search functionality"""
        # Store multiple memories
        memories = [
            MemoryRecord(
                memory_type=MemoryType.SEMANTIC,
                content="Python programming tutorial",
                user_id="user_123",
                tags=["programming", "python"],
                importance_score=0.9
            ),
            MemoryRecord(
                memory_type=MemoryType.SEMANTIC,
                content="JavaScript web development",
                user_id="user_123", 
                tags=["programming", "javascript"],
                importance_score=0.7
            ),
            MemoryRecord(
                memory_type=MemoryType.EPISODIC,
                content="Cooking recipe discussion",
                user_id="user_123",
                tags=["cooking", "food"],
                importance_score=0.5
            )
        ]
        
        for memory in memories:
            await memory_manager.store_memory(memory)
        
        # Search for programming-related memories
        results = await memory_manager.search_memories(
            query="programming",
            limit=5
        )
        
        assert len(results) == 2
        # Results should be scored and sorted
        assert all(score > 0 for _, score in results)
        
        # Search with memory type filter
        semantic_memories = await memory_manager.retrieve_memories(
            memory_types=[MemoryType.SEMANTIC],
            limit=10
        )
        
        assert len(semantic_memories) == 2
        assert all(m.memory_type == MemoryType.SEMANTIC for m in semantic_memories)
    
    @pytest.mark.asyncio
    async def test_memory_update_and_delete(self, memory_manager):
        """Test memory update and deletion"""
        # Store initial memory
        record = MemoryRecord(
            memory_type=MemoryType.PROCEDURAL,
            content="Initial procedure",
            importance_score=0.5,
            tags=["procedure"]
        )
        
        await memory_manager.store_memory(record)
        
        # Update memory
        updates = {
            'content': 'Updated procedure',
            'importance_score': 0.8,
            'tags': ['procedure', 'updated']
        }
        
        success = await memory_manager.update_memory(record.memory_id, updates)
        assert success
        
        # Retrieve and verify update
        memories = await memory_manager.retrieve_memories(limit=1)
        updated = memories[0]
        assert updated.content == "Updated procedure"
        assert updated.importance_score == 0.8
        assert "updated" in updated.tags
        
        # Delete memory
        success = await memory_manager.delete_memory(record.memory_id)
        assert success
        
        # Verify deletion
        memories = await memory_manager.retrieve_memories(limit=10)
        assert len(memories) == 0
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self, memory_manager):
        """Test expired memory cleanup"""
        now = datetime.now(timezone.utc)
        past_time = now - timedelta(hours=1)
        future_time = now + timedelta(hours=1)
        
        # Store expired and non-expired memories
        expired_record = MemoryRecord(
            memory_type=MemoryType.WORKING,
            content="Expired memory",
            expires_at=past_time
        )
        
        valid_record = MemoryRecord(
            memory_type=MemoryType.WORKING,
            content="Valid memory",
            expires_at=future_time
        )
        
        await memory_manager.store_memory(expired_record)
        await memory_manager.store_memory(valid_record)
        
        # Cleanup expired memories
        deleted_count = await memory_manager.cleanup_expired_memories()
        assert deleted_count == 1
        
        # Verify only valid memory remains
        memories = await memory_manager.retrieve_memories(limit=10)
        assert len(memories) == 1
        assert memories[0].content == "Valid memory"
    
    @pytest.mark.asyncio
    async def test_memory_stats(self, memory_manager):
        """Test memory statistics"""
        # Store various memory types
        memory_types = [
            MemoryType.WORKING,
            MemoryType.EPISODIC,
            MemoryType.SEMANTIC,
            MemoryType.PROCEDURAL
        ]
        
        for i, mem_type in enumerate(memory_types):
            record = MemoryRecord(
                memory_type=mem_type,
                content=f"Test content {i}",
                importance_score=0.5 + i * 0.1
            )
            await memory_manager.store_memory(record)
        
        # Get statistics
        stats = await memory_manager.get_memory_stats()
        
        assert stats['total_records'] == 4
        assert 'records_by_type' in stats
        assert 'storage_size_bytes' in stats
        assert stats['storage_size_bytes'] > 0
        
        # Verify type distribution
        type_counts = stats['records_by_type']
        for mem_type in memory_types:
            assert type_counts.get(mem_type.value, 0) == 1


class TestContextManager:
    """Test conversation context management"""
    
    @pytest.fixture
    async def context_manager(self):
        """Create a test context manager"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        config = {'db_path': db_path}
        memory_manager = AgentMemoryManager('test_agent', config)
        await asyncio.sleep(0.1)
        
        context_manager = ContextManager(memory_manager)
        
        yield context_manager
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_create_and_update_context(self, context_manager):
        """Test context creation and message updates"""
        # Create context
        context = await context_manager.create_context(
            session_id="test_session",
            user_id="test_user",
            agent_id="test_agent"
        )
        
        assert context.session_id == "test_session"
        assert context.user_id == "test_user"
        assert context.agent_id == "test_agent"
        assert len(context.messages) == 0
        
        # Add messages
        messages = [
            AgentMessage(role="user", content="Hello, how are you?"),
            AgentMessage(role="assistant", content="I'm doing well, thank you!"),
            AgentMessage(role="user", content="Can you help me with Python?"),
        ]
        
        for message in messages:
            updated_context = await context_manager.update_context(
                "test_session", message
            )
            assert updated_context.session_id == "test_session"
        
        # Verify context state
        final_context = await context_manager.get_context("test_session")
        assert final_context is not None
        assert len(final_context.messages) == 3
        assert final_context.message_count == 3
        assert final_context.token_count > 0  # Should have calculated tokens
    
    @pytest.mark.asyncio
    async def test_context_compression(self, context_manager):
        """Test context compression functionality"""
        # Create context with many messages
        context = await context_manager.create_context("compression_session")
        
        # Add many messages to trigger compression
        messages = []
        for i in range(20):
            message = AgentMessage(
                role="user" if i % 2 == 0 else "assistant",
                content=f"This is test message number {i} with some content to make it longer."
            )
            messages.append(message)
            await context_manager.update_context("compression_session", message)
        
        # Test summarization compression
        result = await context_manager.compress_context(
            "compression_session",
            target_token_count=100,
            strategy=CompressionStrategy.SUMMARIZATION
        )
        
        assert result.original_token_count > result.compressed_token_count
        assert result.compression_ratio < 1.0
        assert result.strategy_used == CompressionStrategy.SUMMARIZATION
        assert len(result.compressed_messages) < 20
        assert result.summary is not None
        
        # Test extraction compression
        result = await context_manager.compress_context(
            "compression_session",
            target_token_count=150,
            strategy=CompressionStrategy.EXTRACTION
        )
        
        assert result.strategy_used == CompressionStrategy.EXTRACTION
        assert len(result.compressed_messages) <= 20
    
    @pytest.mark.asyncio
    async def test_relevant_context_retrieval(self, context_manager):
        """Test retrieval of relevant context messages"""
        # Create context with diverse messages
        context = await context_manager.create_context("relevance_session")
        
        messages = [
            AgentMessage(role="user", content="I love Python programming"),
            AgentMessage(role="assistant", content="Python is great for data science"),
            AgentMessage(role="user", content="What about JavaScript?"),
            AgentMessage(role="assistant", content="JavaScript is excellent for web development"),
            AgentMessage(role="user", content="I'm cooking dinner tonight"),
            AgentMessage(role="assistant", content="That sounds delicious!"),
        ]
        
        for message in messages:
            await context_manager.update_context("relevance_session", message)
        
        # Get relevant context for programming query
        relevant_messages = await context_manager.get_relevant_context(
            "relevance_session",
            "Python programming",
            max_tokens=200
        )
        
        assert len(relevant_messages) > 0
        # Should include Python-related messages
        programming_content = " ".join([m.content for m in relevant_messages])
        assert "python" in programming_content.lower()
    
    @pytest.mark.asyncio
    async def test_context_summarization(self, context_manager):
        """Test conversation summarization"""
        context = await context_manager.create_context("summary_session")
        
        # Add meaningful conversation
        messages = [
            AgentMessage(role="user", content="I need help with my Python project"),
            AgentMessage(role="assistant", content="I'd be happy to help with your Python project"),
            AgentMessage(role="user", content="I'm building a web scraper"),
            AgentMessage(role="assistant", content="Web scraping is important for data collection"),
        ]
        
        for message in messages:
            await context_manager.update_context("summary_session", message)
        
        # Generate summary
        summary = await context_manager.summarize_context("summary_session")
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        # Summary should contain key topics
        summary_lower = summary.lower()
        assert any(word in summary_lower for word in ["python", "project", "help"])
    
    @pytest.mark.asyncio
    async def test_entity_extraction(self, context_manager):
        """Test entity extraction from conversation"""
        context = await context_manager.create_context("entity_session")
        
        # Add messages with entities
        messages = [
            AgentMessage(role="user", content="I work at Google in San Francisco"),
            AgentMessage(role="assistant", content="Google is a great company in California"),
            AgentMessage(role="user", content="I met John Smith yesterday"),
        ]
        
        for message in messages:
            await context_manager.update_context("entity_session", message)
        
        # Extract entities
        entities = await context_manager.extract_entities("entity_session")
        
        assert isinstance(entities, dict)
        assert "people" in entities
        assert "places" in entities
        assert "organizations" in entities
        assert "topics" in entities


class TestPersonalizationEngine:
    """Test personalization and adaptation functionality"""
    
    @pytest.fixture
    async def personalization_engine(self):
        """Create a test personalization engine"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        config = {'db_path': db_path}
        memory_manager = AgentMemoryManager('test_agent', config)
        await asyncio.sleep(0.1)
        
        engine = PersonalizationEngine(memory_manager, PersonalizationLevel.ADAPTIVE)
        
        yield engine
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_profile_creation_and_updates(self, personalization_engine):
        """Test user profile creation and updates"""
        user_id = "test_user_123"
        
        # Get initial profile (should create new one)
        profile = await personalization_engine.get_profile(user_id)
        assert profile is not None
        assert profile.user_id == user_id
        assert profile.personalization_level == PersonalizationLevel.ADAPTIVE
        
        # Update profile with interaction data
        interaction_data = {
            'response_rating': 0.8,
            'response_style': 'detailed',
            'topics_mentioned': ['python', 'programming', 'machine learning']
        }
        
        updated_profile = await personalization_engine.update_profile(
            user_id, interaction_data
        )
        
        assert updated_profile.response_preferences['detailed'] == 0.8
        assert 'python' in updated_profile.topic_interests
        assert updated_profile.topic_interests['python'] > 0.5
        assert updated_profile.last_interaction is not None
    
    @pytest.mark.asyncio
    async def test_personalized_context(self, personalization_engine):
        """Test personalized context generation"""
        user_id = "context_user"
        
        # Create profile with interests
        interaction_data = {
            'topics_mentioned': ['python', 'data science', 'ai']
        }
        await personalization_engine.update_profile(user_id, interaction_data)
        
        # Create base context
        base_context = [
            AgentMessage(role="user", content="I love cooking recipes"),
            AgentMessage(role="assistant", content="Let me help with Python programming"),
            AgentMessage(role="user", content="Can you explain data science concepts?"),
            AgentMessage(role="assistant", content="Machine learning is fascinating"),
        ]
        
        # Get personalized context
        personalized_context = await personalization_engine.get_personalized_context(
            user_id, base_context
        )
        
        assert len(personalized_context) == len(base_context)
        # Should prioritize messages about user's interests
        # Check that messages are reordered based on interests
    
    @pytest.mark.asyncio
    async def test_response_style_suggestions(self, personalization_engine):
        """Test response style suggestions"""
        user_id = "style_user"
        
        # Update profile with style preferences
        interaction_data = {
            'response_rating': 0.9,
            'response_style': 'friendly_detailed'
        }
        await personalization_engine.update_profile(user_id, interaction_data)
        
        # Get style suggestions
        context = [AgentMessage(role="user", content="How are you today?")]
        suggestions = await personalization_engine.suggest_response_style(
            user_id, context
        )
        
        assert 'style' in suggestions
        assert 'confidence' in suggestions
        assert suggestions['style'] == 'friendly_detailed'
        assert suggestions['confidence'] == 0.9
        assert 'suggestions' in suggestions
    
    @pytest.mark.asyncio
    async def test_intent_prediction(self, personalization_engine):
        """Test user intent prediction"""
        user_id = "intent_user"
        context = [AgentMessage(role="assistant", content="Hello!")]
        
        # Test question intent
        intents = await personalization_engine.predict_user_intent(
            user_id,
            "What is machine learning?",
            context
        )
        
        assert 'question' in intents
        assert intents['question'] > 0.5
        
        # Test help intent
        intents = await personalization_engine.predict_user_intent(
            user_id,
            "Can you help me with this problem?",
            context
        )
        
        assert 'help' in intents
        assert intents['help'] > 0.5
        
        # Test request intent
        intents = await personalization_engine.predict_user_intent(
            user_id,
            "Please explain this concept",
            context
        )
        
        assert 'request' in intents
        assert intents['request'] > 0.5
    
    @pytest.mark.asyncio
    async def test_feedback_adaptation(self, personalization_engine):
        """Test adaptation based on user feedback"""
        user_id = "feedback_user"
        
        # Provide feedback
        feedback = {
            'type': 'response_quality',
            'rating': 4,
            'sentiment': 'positive',
            'comment': 'Very helpful explanation',
            'improvements': ['more examples']
        }
        
        success = await personalization_engine.adapt_to_feedback(user_id, feedback)
        assert success
        
        # Verify feedback was stored and profile updated
        profile = await personalization_engine.get_profile(user_id)
        assert profile is not None
        # Check that feedback influenced the profile
        assert len(profile.feedback_history) > 0 or profile.last_interaction is not None


class TestMemoryAnalytics:
    """Test memory analytics and optimization"""
    
    @pytest.fixture
    async def memory_analytics(self):
        """Create a test memory analytics system"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        config = {'db_path': db_path}
        memory_manager = AgentMemoryManager('analytics_agent', config)
        await asyncio.sleep(0.1)
        
        analytics = MemoryAnalytics(memory_manager)
        
        # Add some test data
        test_memories = [
            MemoryRecord(
                memory_type=MemoryType.EPISODIC,
                content="User asked about Python",
                user_id="user1",
                access_count=5,
                importance_score=0.8
            ),
            MemoryRecord(
                memory_type=MemoryType.SEMANTIC,
                content="Python is a programming language",
                user_id="user1", 
                access_count=10,
                importance_score=0.9
            ),
            MemoryRecord(
                memory_type=MemoryType.PROCEDURAL,
                content="How to debug Python code",
                user_id="user2",
                access_count=2,
                importance_score=0.6
            )
        ]
        
        for memory in test_memories:
            await memory_manager.store_memory(memory)
        
        yield analytics, memory_manager
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_memory_usage_analysis(self, memory_analytics):
        """Test memory usage analysis"""
        analytics, memory_manager = memory_analytics
        
        # Analyze memory usage
        analysis = await analytics.analyze_memory_usage()
        
        assert 'total_records' in analysis
        assert 'records_by_type' in analysis
        assert 'storage_size_bytes' in analysis
        assert analysis['total_records'] == 3
        
        # Test user-specific analysis
        user_analysis = await analytics.analyze_memory_usage(user_id="user1")
        assert isinstance(user_analysis, dict)
    
    @pytest.mark.asyncio
    async def test_insight_generation(self, memory_analytics):
        """Test insight generation from memory data"""
        analytics, memory_manager = memory_analytics
        
        # Generate insights
        insights = await analytics.generate_insights()
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # Check insight structure
        for insight in insights:
            assert isinstance(insight, MemoryInsight)
            assert insight.insight_type in ['access_patterns', 'type_distribution', 'temporal_patterns']
            assert insight.title is not None
            assert insight.description is not None
            assert insight.confidence_score > 0
        
        # Test specific insight types
        access_insights = await analytics.generate_insights(insight_types=['access_patterns'])
        assert len(access_insights) > 0
        assert all(i.insight_type == 'access_patterns' for i in access_insights)
    
    @pytest.mark.asyncio
    async def test_conversation_analytics(self, memory_analytics):
        """Test conversation-specific analytics"""
        analytics, memory_manager = memory_analytics
        
        # Add session-specific memories
        session_id = "test_session_123"
        session_memory = MemoryRecord(
            memory_type=MemoryType.EPISODIC,
            content="Discussion about machine learning",
            session_id=session_id,
            user_id="user1"
        )
        await memory_manager.store_memory(session_memory)
        
        # Get conversation analytics
        conv_analytics = await analytics.get_conversation_analytics(session_id)
        
        assert 'session_id' in conv_analytics
        assert conv_analytics['session_id'] == session_id
        assert 'message_count' in conv_analytics
        assert 'total_memories' in conv_analytics
        assert 'memory_types' in conv_analytics
        assert conv_analytics['total_memories'] >= 1
    
    @pytest.mark.asyncio
    async def test_user_analytics(self, memory_analytics):
        """Test user-specific analytics"""
        analytics, memory_manager = memory_analytics
        
        # Get user analytics
        user_analytics = await analytics.get_user_analytics("user1")
        
        assert 'user_id' in user_analytics
        assert user_analytics['user_id'] == "user1"
        assert 'total_memories' in user_analytics
        assert 'memory_types' in user_analytics
        assert user_analytics['total_memories'] >= 2  # We stored 2 memories for user1
        
        # Test with time range
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=1)
        future = now + timedelta(days=1)
        
        time_range_analytics = await analytics.get_user_analytics(
            "user1", 
            time_range=(past, future)
        )
        assert isinstance(time_range_analytics, dict)
    
    @pytest.mark.asyncio
    async def test_memory_optimization(self, memory_analytics):
        """Test memory usage optimization"""
        analytics, memory_manager = memory_analytics
        
        # Add more memories to have something to optimize
        for i in range(10):
            memory = MemoryRecord(
                memory_type=MemoryType.WORKING,
                content=f"Temporary memory {i}",
                importance_score=0.1,  # Low importance
                access_count=0  # Never accessed
            )
            await memory_manager.store_memory(memory)
        
        # Optimize memory usage
        result = await analytics.optimize_memory_usage(target_reduction=0.3)
        
        assert 'target_reduction' in result
        assert 'memories_removed' in result
        assert 'new_total' in result
        assert 'optimization_success' in result
        
        if result['memories_removed'] > 0:
            assert result['optimization_success'] is True
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, memory_analytics):
        """Test performance metrics collection"""
        analytics, memory_manager = memory_analytics
        
        metrics = await analytics.get_performance_metrics()
        
        assert 'cache_performance' in metrics
        assert 'storage_performance' in metrics
        assert 'access_patterns' in metrics
        
        # Verify cache metrics
        cache_metrics = metrics['cache_performance']
        assert 'cache_size' in cache_metrics
        assert 'cache_hit_ratio' in cache_metrics
        assert 'cache_utilization' in cache_metrics
        
        # Verify storage metrics
        storage_metrics = metrics['storage_performance']
        assert 'storage_size_mb' in storage_metrics
        assert 'storage_efficiency' in storage_metrics


class TestIntegrationFactory:
    """Test the complete memory system integration"""
    
    @pytest.mark.asyncio
    async def test_create_agent_memory_factory(self):
        """Test the factory function for creating complete memory system"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        config = {'db_path': db_path}
        
        try:
            # Create complete memory system
            components = create_agent_memory(
                'factory_test_agent',
                config,
                PersonalizationLevel.INTELLIGENT
            )
            
            memory, context_manager, retrieval, personalization, analytics = components
            
            # Test all components are created correctly
            assert memory.agent_id == 'factory_test_agent'
            assert isinstance(context_manager, ContextManager)
            assert isinstance(retrieval, MemoryRetrievalEngine)
            assert isinstance(personalization, PersonalizationEngine)
            assert isinstance(analytics, MemoryAnalytics)
            
            # Test integration works
            record = MemoryRecord(
                memory_type=MemoryType.SEMANTIC,
                content="Factory test memory",
                importance_score=0.7
            )
            
            success = await memory.store_memory(record)
            assert success
            
            memories = await retrieval.retrieve_by_keywords(['factory'])
            assert len(memories) > 0
            
            stats = await analytics.get_performance_metrics()
            assert 'total_records' in stats
            
        finally:
            try:
                os.unlink(db_path)
            except:
                pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])