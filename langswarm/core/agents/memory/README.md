# V2 Agent Memory & Context Management System

The V2 Agent Memory & Context Management System provides sophisticated memory and context handling capabilities for LangSwarm V2 agents, enabling persistent conversation memory, intelligent context compression, long-term memory with semantic retrieval, personalization, and comprehensive analytics.

## Features

### 🧠 **Persistent Conversation Memory**
- **Cross-session persistence**: Conversations are stored persistently across agent sessions
- **Multiple memory types**: Working, Episodic, Semantic, Procedural, Emotional, and Preference memories
- **Automatic expiration**: Memories can be set to expire automatically
- **Importance scoring**: Memories are scored by importance for intelligent retention

### 🗜️ **Context Compression & Summarization**
- **Intelligent compression**: Reduces context size while preserving important information
- **Multiple strategies**: Summarization, extraction, clustering, hierarchical, and semantic compression
- **Automatic triggers**: Compression activates when context exceeds token limits
- **Quality preservation**: Maintains semantic similarity and minimizes information loss

### 🔍 **Long-term Memory with Retrieval**
- **Semantic search**: Vector-based similarity search for relevant memories
- **Keyword matching**: Traditional keyword-based retrieval
- **Temporal queries**: Retrieve memories within specific time ranges
- **Pattern recognition**: Find memories matching behavioral patterns
- **Hybrid strategies**: Combine multiple retrieval approaches

### 👤 **Context-aware Personalization**
- **User profiling**: Build detailed user preference profiles
- **Adaptive learning**: Learn from user interactions and feedback
- **Intent prediction**: Predict user intent based on conversation patterns
- **Response styling**: Suggest personalized response styles
- **Behavioral adaptation**: Adapt to user communication preferences

### 📊 **Memory Analytics & Optimization**
- **Usage analytics**: Comprehensive memory usage statistics
- **Insight generation**: AI-powered insights from memory data
- **Performance monitoring**: Cache hit rates, storage efficiency, access patterns
- **Automatic optimization**: Remove low-value memories to optimize storage
- **Conversation analytics**: Detailed analysis of individual conversations

## Quick Start

```python
from langswarm.core.agents.memory import create_agent_memory, PersonalizationLevel

# Create complete memory system for an agent
config = {
    'db_path': 'agent_memory.db',
    'max_records': 10000,
    'embedding_dim': 1536
}

memory, context_mgr, retrieval, personalization, analytics = create_agent_memory(
    agent_id='my_agent',
    memory_backend_config=config,
    personalization_level=PersonalizationLevel.ADAPTIVE
)

# Store a memory
from langswarm.core.agents.memory import MemoryRecord, MemoryType

record = MemoryRecord(
    memory_type=MemoryType.EPISODIC,
    content="User asked about Python programming",
    user_id="user_123",
    session_id="session_456",
    importance_score=0.8,
    tags=["programming", "python"]
)

await memory.store_memory(record)

# Retrieve relevant memories
memories = await memory.retrieve_memories(
    query="python programming",
    user_id="user_123",
    limit=10
)
```

## Architecture

### Core Components

#### 1. **AgentMemoryManager**
Central memory storage and retrieval system with SQLite backend and in-memory caching.

```python
# Store and retrieve memories
await memory.store_memory(record)
memories = await memory.retrieve_memories(user_id="user123")
search_results = await memory.search_memories("python programming")
```

#### 2. **ContextManager**
Manages conversation context with compression and summarization capabilities.

```python
# Update context with new messages
context = await context_mgr.update_context(session_id, message)

# Compress context when needed
compressed = await context_mgr.compress_context(
    session_id, 
    target_token_count=2000,
    strategy=CompressionStrategy.SUMMARIZATION
)

# Get relevant context for queries
relevant = await context_mgr.get_relevant_context(session_id, "python help")
```

#### 3. **MemoryRetrievalEngine**
Advanced retrieval with multiple search strategies.

```python
# Semantic similarity search
similar = await retrieval.retrieve_by_similarity(
    query_embedding=embedding,
    threshold=0.7
)

# Keyword-based retrieval
keyword_results = await retrieval.retrieve_by_keywords(["python", "programming"])

# Temporal retrieval
recent = await retrieval.retrieve_temporal(
    start_time=yesterday,
    end_time=now
)
```

#### 4. **PersonalizationEngine**
Context-aware personalization and user adaptation.

```python
# Get user profile
profile = await personalization.get_profile("user123")

# Update based on interaction
updated_profile = await personalization.update_profile(
    "user123",
    {"response_rating": 0.9, "topics_mentioned": ["python"]}
)

# Get personalized context
personal_context = await personalization.get_personalized_context(
    "user123", base_context
)

# Predict user intent
intents = await personalization.predict_user_intent(
    "user123", "Can you help me?", context
)
```

#### 5. **MemoryAnalytics**
Comprehensive analytics and optimization.

```python
# Get usage statistics
stats = await analytics.analyze_memory_usage()

# Generate insights
insights = await analytics.generate_insights(user_id="user123")

# Optimize memory usage
optimization = await analytics.optimize_memory_usage(target_reduction=0.2)

# Performance metrics
metrics = await analytics.get_performance_metrics()
```

## Memory Types

| Type | Purpose | Retention | Examples |
|------|---------|-----------|----------|
| **Working** | Current conversation context | Session-based | Active dialog, temporary notes |
| **Episodic** | Specific conversation episodes | Medium-term | Important discussions, events |
| **Semantic** | Knowledge and facts | Long-term | Learned information, definitions |
| **Procedural** | Learned patterns and procedures | Long-term | How-to knowledge, workflows |
| **Emotional** | Emotional context and patterns | Medium-term | Sentiment, feedback, mood |
| **Preference** | User preferences and patterns | Long-term | Communication style, interests |

## Configuration

### Memory Backend Configuration

```python
config = {
    'db_path': 'path/to/memory.db',        # SQLite database path
    'max_records': 10000,                  # Maximum memory records
    'embedding_dim': 1536,                 # Embedding dimensionality
    'cache_size': 1000,                    # In-memory cache size
    'cleanup_interval': 3600,              # Cleanup interval (seconds)
    'compression_threshold': 8000,         # Token threshold for compression
    'importance_decay': 0.1,               # Daily importance decay rate
}
```

### Personalization Levels

- **NONE**: No personalization
- **BASIC**: Basic preference tracking
- **ADAPTIVE**: Learning from interactions
- **PREDICTIVE**: Predicting user needs
- **INTELLIGENT**: AI-driven personalization

### Compression Strategies

- **SUMMARIZATION**: Summarize older messages
- **EXTRACTION**: Extract key information
- **CLUSTERING**: Group similar messages
- **HIERARCHICAL**: Multi-level compression
- **SEMANTIC**: Semantic similarity compression

## Integration with V2 Agents

The memory system integrates seamlessly with V2 agents:

```python
from langswarm.core.agents import create_agent
from langswarm.core.agents.memory import create_agent_memory

# Create agent with memory
agent = create_agent("intelligent_agent", provider="openai")

# Create memory system
memory_config = {'db_path': f'memory_{agent.agent_id}.db'}
memory, context_mgr, retrieval, personalization, analytics = create_agent_memory(
    agent.agent_id,
    memory_config,
    PersonalizationLevel.INTELLIGENT
)

# Use in agent interactions
async def enhanced_chat(user_id: str, message: str, session_id: str):
    # Update context with user message
    user_msg = AgentMessage(role="user", content=message)
    context = await context_mgr.update_context(session_id, user_msg)
    
    # Get personalized context
    personal_context = await personalization.get_personalized_context(
        user_id, context.messages
    )
    
    # Predict user intent
    intents = await personalization.predict_user_intent(
        user_id, message, personal_context
    )
    
    # Generate response with agent
    response = await agent.chat(message, session_id=session_id)
    
    # Update context with response
    response_msg = AgentMessage(role="assistant", content=response.content)
    await context_mgr.update_context(session_id, response_msg)
    
    # Store important memories
    if intents.get("help", 0) > 0.7:  # High help intent
        memory_record = MemoryRecord(
            memory_type=MemoryType.EPISODIC,
            content=f"User needed help with: {message}",
            user_id=user_id,
            session_id=session_id,
            importance_score=0.8,
            tags=["help", "important"]
        )
        await memory.store_memory(memory_record)
    
    return response
```

## Performance & Scalability

### Storage Efficiency
- **SQLite backend**: Efficient local storage with ACID compliance
- **In-memory caching**: LRU cache for frequently accessed memories
- **Automatic cleanup**: Expired memory cleanup and optimization
- **Compression**: Reduces storage size by up to 70%

### Query Performance
- **Database indexing**: Optimized indices for common queries
- **Semantic search**: Fast vector similarity search
- **Caching layer**: Sub-millisecond cache hits
- **Batch operations**: Efficient bulk memory operations

### Memory Limits
- **Configurable limits**: Set maximum memory records per agent
- **Automatic optimization**: Remove low-value memories when limits reached
- **Importance scoring**: Retain most valuable memories
- **Expiration policies**: Automatic cleanup of expired memories

## Best Practices

### Memory Management
1. **Set appropriate importance scores** based on conversation significance
2. **Use expiration times** for temporary information
3. **Tag memories** for efficient categorization and retrieval
4. **Regular cleanup** to maintain optimal performance

### Context Compression
1. **Monitor token counts** and compress proactively
2. **Choose appropriate strategies** based on conversation type
3. **Preserve important entities** during compression
4. **Test compression quality** with semantic similarity metrics

### Personalization
1. **Start with basic personalization** and gradually increase sophistication
2. **Collect user feedback** to improve adaptation
3. **Respect privacy settings** and user preferences
4. **Monitor personalization effectiveness** with analytics

### Analytics & Monitoring
1. **Track memory usage patterns** to optimize configuration
2. **Monitor performance metrics** for bottlenecks
3. **Generate regular insights** for system improvements
4. **Use conversation analytics** to understand user behavior

## Error Handling

The memory system includes comprehensive error handling:

```python
from langswarm.core.error import V2Error, ErrorCategory

try:
    await memory.store_memory(record)
except V2Error as e:
    if e.category == ErrorCategory.MEMORY:
        # Handle memory-specific errors
        logger.error(f"Memory error: {e.message}")
    # Implement fallback strategy
```

## Testing

Comprehensive test coverage includes:

```bash
# Run memory system tests
pytest tests/v2/test_agent_memory_system.py -v

# Run performance benchmarks
python tests/v2/memory_performance_benchmark.py

# Run integration tests
pytest tests/v2/test_memory_integration.py -v
```

## Future Enhancements

### Planned Features
- **Vector database integration**: Support for Pinecone, Weaviate, Qdrant
- **Advanced NLP**: Better entity extraction and summarization
- **Multi-modal memories**: Support for image, audio, and video memories
- **Federated memory**: Shared memories across multiple agents
- **Memory synchronization**: Sync memories across devices and deployments

### Research Areas
- **Neuromorphic memory**: Brain-inspired memory architectures
- **Quantum memory**: Quantum-enhanced retrieval and storage
- **Emotional AI**: Advanced emotional memory and empathy
- **Privacy-preserving**: Zero-knowledge memory operations

## Support

For questions, issues, or contributions:
- **Documentation**: [LangSwarm V2 Docs](https://docs.langswarm.com/v2/memory)
- **Issues**: [GitHub Issues](https://github.com/langswarm/langswarm/issues)
- **Community**: [Discord Server](https://discord.gg/langswarm)

---

*The V2 Agent Memory & Context Management System represents a significant advancement in conversational AI memory capabilities, providing the foundation for intelligent, personalized, and context-aware agent interactions.*