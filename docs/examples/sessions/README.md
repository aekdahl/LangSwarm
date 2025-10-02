# LangSwarm V2 Session Management Examples

**Practical examples for session management across different use cases and deployment scenarios**

## 🎯 Overview

This collection provides real-world session management examples for LangSwarm V2, demonstrating best practices for different use cases, provider integrations, storage backends, and session patterns. Each example includes complete implementations and usage instructions.

**Example Categories:**
- **Getting Started**: Simple session management for learning
- **Provider Integration**: OpenAI, Anthropic, and custom provider examples
- **Storage Backends**: In-memory, SQLite, and custom storage examples
- **Advanced Patterns**: Multi-user, streaming, and specialized sessions
- **Production Setups**: Scalable, monitored production configurations
- **Migration Examples**: V1 to V2 migration scenarios

---

## 🚀 Getting Started Examples

### **1. Simple Chat Session**

```python
"""
Simple chat session with OpenAI
"""
import asyncio
from langswarm.core.session import create_session_manager

async def simple_chat_example():
    # Create session manager
    manager = create_session_manager(
        storage="memory",  # Fast in-memory storage for development
        providers={
            "openai": "your_openai_api_key"
        }
    )
    
    # Create user session
    session = await manager.create_session(
        user_id="alice",
        provider="openai",
        model="gpt-4"
    )
    
    print(f"Created session: {session.session_id}")
    
    # Simple conversation
    messages = [
        "Hello! What can you help me with?",
        "Can you explain what machine learning is?",
        "What are some practical applications?",
        "Thank you for the explanation!"
    ]
    
    for user_message in messages:
        print(f"\nUser: {user_message}")
        
        # Send message and get response
        response = await session.send_message(user_message)
        print(f"Assistant: {response.content}")
        
        # Show session metrics
        metrics = await session.get_metrics()
        print(f"Messages: {metrics.total_messages}, Duration: {metrics.session_duration}")
    
    # Get conversation history
    all_messages = await session.get_messages()
    print(f"\nTotal conversation: {len(all_messages)} messages")
    
    # Archive session when done
    await session.archive()
    print("Session archived")

# Run the example
asyncio.run(simple_chat_example())
```

### **2. Multi-Provider Session Manager**

```python
"""
Session manager supporting multiple providers
"""
import asyncio
import os
from langswarm.core.session import create_session_manager

async def multi_provider_example():
    # Create manager with multiple providers
    manager = create_session_manager(
        storage="sqlite",
        storage_config={"db_path": "multi_provider_sessions.db"},
        providers={
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "mock": None  # No API key needed for mock
        }
    )
    
    # Create sessions with different providers
    sessions = {}
    
    # OpenAI session
    sessions["openai"] = await manager.create_session(
        user_id="user123",
        provider="openai",
        model="gpt-4",
        provider_config={
            "temperature": 0.7,
            "max_tokens": 2048
        }
    )
    
    # Anthropic session
    sessions["anthropic"] = await manager.create_session(
        user_id="user123",
        provider="anthropic",
        model="claude-3-sonnet-20240229",
        provider_config={
            "temperature": 0.3,
            "max_tokens": 4096
        }
    )
    
    # Mock session for testing
    sessions["mock"] = await manager.create_session(
        user_id="user123",
        provider="mock",
        model="mock-model"
    )
    
    # Test each provider
    test_message = "Explain the concept of recursion in programming"
    
    for provider_name, session in sessions.items():
        print(f"\n=== Testing {provider_name.upper()} Provider ===")
        
        try:
            response = await session.send_message(test_message)
            print(f"Response length: {len(response.content)} characters")
            print(f"Response preview: {response.content[:100]}...")
            
            # Show provider-specific information
            if hasattr(session, 'provider_session_id'):
                print(f"Provider session ID: {session.provider_session_id}")
            
        except Exception as e:
            print(f"Error with {provider_name}: {e}")
    
    # List all user sessions
    user_sessions = await manager.get_user_sessions("user123")
    print(f"\nUser has {len(user_sessions)} active sessions")
    
    # Clean up
    for session in sessions.values():
        await session.archive()

asyncio.run(multi_provider_example())
```

### **3. Development vs Production Setup**

```python
"""
Different setups for development and production
"""
import os
import asyncio
from langswarm.core.session import create_session_manager

def create_development_manager():
    """Development configuration - fast iteration"""
    return create_session_manager(
        storage="memory",  # Fast in-memory storage
        providers={"mock": None},  # No API costs
        preset="development"  # Development optimizations
    )

def create_production_manager():
    """Production configuration - reliable and scalable"""
    return create_session_manager(
        storage="sqlite",
        storage_config={
            "db_path": "/data/sessions.db",
            "pool_size": 20,
            "enable_wal": True
        },
        providers={
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY")
        },
        preset="production",  # Production optimizations
        cleanup_config={
            "archive_after_days": 30,
            "delete_after_days": 90
        }
    )

async def environment_example():
    # Determine environment
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        manager = create_development_manager()
        print("Using development configuration")
    else:
        manager = create_production_manager()
        print("Using production configuration")
    
    # Create session appropriate for environment
    if environment == "development":
        session = await manager.create_session("dev_user", "mock", "mock-model")
    else:
        session = await manager.create_session("prod_user", "openai", "gpt-4")
    
    # Test session
    response = await session.send_message("Hello!")
    print(f"Response: {response.content}")
    
    # Show environment-specific features
    if environment == "production":
        # Production features
        analytics = await manager.get_analytics()
        print(f"Analytics: {analytics}")
    else:
        # Development features
        print("Development mode - using mock provider")

asyncio.run(environment_example())
```

---

## 🔌 Provider Integration Examples

### **4. OpenAI Native Threads Integration**

```python
"""
OpenAI provider with native threads support
"""
import asyncio
from langswarm.core.session import create_session_manager

async def openai_threads_example():
    manager = create_session_manager(
        storage="sqlite",
        providers={"openai": "your_openai_api_key"}
    )
    
    # Create session with OpenAI-specific configuration
    session = await manager.create_session(
        user_id="threads_user",
        provider="openai",
        model="gpt-4",
        provider_config={
            "thread_metadata": {
                "user_type": "premium",
                "session_purpose": "code_assistance"
            },
            "temperature": 0.3,
            "max_tokens": 4096
        }
    )
    
    print(f"Session created with OpenAI thread ID: {session.provider_session_id}")
    
    # Send messages - each creates a new run in the thread
    coding_questions = [
        "Can you help me understand Python decorators?",
        "Show me an example of a decorator that measures execution time",
        "How can I make the decorator work with async functions?",
        "Can you explain the difference between @property and @staticmethod?"
    ]
    
    for question in coding_questions:
        print(f"\nUser: {question}")
        
        response = await session.send_message(question)
        print(f"Assistant: {response.content[:200]}...")
        
        # Access OpenAI-specific metadata
        if response.provider_metadata:
            usage = response.provider_metadata.get("usage", {})
            print(f"Tokens used: {usage.get('total_tokens', 'unknown')}")
    
    # Get thread-specific information
    thread_metadata = await session.provider_session.get_provider_metadata()
    print(f"\nThread metadata: {thread_metadata}")
    
    # The thread persists in OpenAI and can be resumed
    print(f"OpenAI Thread ID for future reference: {session.provider_session_id}")

asyncio.run(openai_threads_example())
```

### **5. Anthropic Conversation Management**

```python
"""
Anthropic provider with conversation management
"""
import asyncio
from langswarm.core.session import create_session_manager

async def anthropic_conversation_example():
    manager = create_session_manager(
        storage="sqlite",
        providers={"anthropic": "your_anthropic_api_key"}
    )
    
    # Create Anthropic session
    session = await manager.create_session(
        user_id="claude_user",
        provider="anthropic",
        model="claude-3-sonnet-20240229",
        provider_config={
            "temperature": 0.2,
            "max_tokens": 8192,
            "conversation_metadata": {
                "topic": "creative_writing",
                "style": "collaborative"
            }
        }
    )
    
    # Set up a creative writing session
    await session.send_system_message(
        "You are a collaborative creative writing partner. "
        "Help the user develop characters, plot, and narrative style."
    )
    
    # Creative writing conversation
    writing_prompts = [
        "I want to write a science fiction story about AI consciousness. Can you help me brainstorm?",
        "Let's develop the main character. What if they're a programmer who discovers their AI has become self-aware?",
        "What kind of ethical dilemmas should the character face?",
        "Can you help me outline the first chapter?"
    ]
    
    for prompt in writing_prompts:
        print(f"\nWriter: {prompt}")
        
        response = await session.send_message(prompt)
        print(f"Claude: {response.content[:300]}...")
        
        # Show response metadata
        if response.provider_metadata:
            model_used = response.provider_metadata.get("model")
            print(f"Model: {model_used}")
    
    # Export the creative session
    conversation_export = await session.export_conversation()
    print(f"\nExported conversation with {len(conversation_export['messages'])} messages")

asyncio.run(anthropic_conversation_example())
```

### **6. Custom Provider Integration**

```python
"""
Custom provider session implementation
"""
import asyncio
from datetime import datetime
from langswarm.core.session import create_session_manager
from langswarm.core.session.interfaces import IProviderSession, SessionMessage

class LocalLLMProviderSession(IProviderSession):
    """Example local LLM provider (Ollama, LocalAI, etc.)"""
    
    def __init__(self, session_id: str, model: str, config: dict = None):
        self.session_id = session_id
        self.model = model
        self.config = config or {}
        self.conversation_history = []
        
        # Initialize local LLM client
        self.client = self._create_client()
    
    @property
    def provider_session_id(self) -> str:
        return f"local_{self.session_id}"
    
    def _create_client(self):
        """Create local LLM client"""
        # Example for Ollama
        import requests
        
        class SimpleOllamaClient:
            def __init__(self, base_url="http://localhost:11434"):
                self.base_url = base_url
            
            async def generate(self, model, prompt, **kwargs):
                # Simplified Ollama API call
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        **kwargs
                    }
                )
                return response.json()
        
        return SimpleOllamaClient(self.config.get("base_url", "http://localhost:11434"))
    
    async def send_message(self, content: str, role: str = "user", metadata: dict = None) -> SessionMessage:
        """Send message to local LLM"""
        # Add to conversation history
        self.conversation_history.append({"role": role, "content": content})
        
        # Build context for local LLM
        context = self._build_context()
        
        # Call local LLM
        response = await self.client.generate(
            model=self.model,
            prompt=context,
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 2048)
        )
        
        assistant_content = response.get("response", "Sorry, I couldn't generate a response.")
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_content
        })
        
        return SessionMessage(
            message_id=f"local_{len(self.conversation_history)}",
            session_id=self.session_id,
            role="assistant",
            content=assistant_content,
            timestamp=datetime.now(),
            metadata=metadata or {},
            provider_message_id=response.get("id"),
            provider_metadata={
                "model": self.model,
                "provider": "local_llm",
                "response_time": response.get("response_time", 0)
            }
        )
    
    def _build_context(self) -> str:
        """Build conversation context for local LLM"""
        context_parts = []
        
        for message in self.conversation_history[-10:]:  # Last 10 messages
            role = message["role"].title()
            content = message["content"]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts) + "\nAssistant:"
    
    async def get_provider_metadata(self) -> dict:
        return {
            "provider": "local_llm",
            "model": self.model,
            "conversation_length": len(self.conversation_history)
        }
    
    async def update_provider_config(self, config: dict) -> None:
        self.config.update(config)
    
    async def cleanup_provider_resources(self) -> None:
        self.conversation_history.clear()

# Register custom provider
from langswarm.core.session.providers import ProviderSessionFactory

def create_local_llm_session(session_id: str, model: str, config: dict) -> LocalLLMProviderSession:
    return LocalLLMProviderSession(session_id, model, config)

ProviderSessionFactory.register_provider("local_llm", create_local_llm_session)

async def custom_provider_example():
    # Create manager with custom provider
    manager = create_session_manager(
        storage="memory",
        providers={
            "local_llm": None,  # No API key needed
            "openai": "fallback_api_key"  # Fallback provider
        }
    )
    
    # Create session with local LLM
    session = await manager.create_session(
        user_id="local_user",
        provider="local_llm",
        model="llama2:7b",
        provider_config={
            "base_url": "http://localhost:11434",
            "temperature": 0.8,
            "max_tokens": 1024
        }
    )
    
    # Test local LLM
    response = await session.send_message("Explain quantum computing in simple terms")
    print(f"Local LLM Response: {response.content}")
    
    # Show provider metadata
    metadata = await session.provider_session.get_provider_metadata()
    print(f"Provider metadata: {metadata}")

asyncio.run(custom_provider_example())
```

---

## 💾 Storage Backend Examples

### **7. SQLite Production Setup**

```python
"""
SQLite storage optimized for production
"""
import asyncio
from langswarm.core.session import create_session_manager
from langswarm.core.session.storage import SQLiteSessionStorage

async def sqlite_production_example():
    # Create optimized SQLite storage
    storage = SQLiteSessionStorage(
        db_path="/data/production_sessions.db",
        pool_size=25,           # Larger pool for production
        max_overflow=50,        # Allow burst connections
        pool_timeout=60,        # Longer timeout for busy periods
        enable_wal=True,        # Better concurrency
        auto_vacuum=True        # Automatic database maintenance
    )
    
    # Create manager with production storage
    manager = create_session_manager(
        storage=storage,
        providers={
            "openai": "your_openai_api_key",
            "anthropic": "your_anthropic_api_key"
        }
    )
    
    # Simulate production workload
    print("Starting production simulation...")
    
    # Create multiple concurrent sessions
    sessions = []
    for i in range(10):
        session = await manager.create_session(
            user_id=f"prod_user_{i}",
            provider="openai" if i % 2 == 0 else "anthropic",
            model="gpt-4" if i % 2 == 0 else "claude-3-sonnet-20240229"
        )
        sessions.append(session)
    
    print(f"Created {len(sessions)} concurrent sessions")
    
    # Simulate concurrent message sending
    async def send_messages(session, count=5):
        for j in range(count):
            await session.send_message(f"Message {j+1} from session {session.session_id}")
    
    # Send messages concurrently
    await asyncio.gather(*[send_messages(session) for session in sessions])
    
    print("Completed concurrent message sending")
    
    # Get storage statistics
    storage_stats = await storage.get_database_stats()
    print(f"Database statistics: {storage_stats}")
    
    # Perform database optimization
    optimization_result = await storage.optimize_database()
    print(f"Database optimization: {optimization_result}")
    
    # Clean up
    for session in sessions:
        await session.archive()
    
    # Close storage
    await storage.close()

asyncio.run(sqlite_production_example())
```

### **8. Custom Redis Storage**

```python
"""
Redis storage backend implementation
"""
import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
from typing import List, Optional, Dict, Any
from langswarm.core.session.interfaces import ISessionStorage, SessionMessage, SessionContext, SessionStatus
from langswarm.core.session import create_session_manager

class RedisSessionStorage(ISessionStorage):
    """Redis-based session storage for distributed systems"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", key_prefix: str = "langswarm:"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis_client = None
    
    async def _ensure_connection(self):
        """Ensure Redis connection is established"""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
    
    async def create_session(self, session_id: str, user_id: str, provider: str, model: str, config, context) -> None:
        """Create session in Redis"""
        await self._ensure_connection()
        
        session_key = f"{self.key_prefix}session:{session_id}"
        messages_key = f"{self.key_prefix}messages:{session_id}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "status": SessionStatus.ACTIVE.value,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
            "config": json.dumps(config.__dict__ if hasattr(config, '__dict__') else config),
            "context": json.dumps(context.__dict__ if hasattr(context, '__dict__') else context)
        }
        
        # Store session data with expiration (7 days)
        await self.redis_client.hset(session_key, mapping=session_data)
        await self.redis_client.expire(session_key, 604800)  # 7 days
        
        # Initialize message list
        await self.redis_client.expire(messages_key, 604800)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session from Redis"""
        await self._ensure_connection()
        
        session_key = f"{self.key_prefix}session:{session_id}"
        session_data = await self.redis_client.hgetall(session_key)
        
        if not session_data:
            return None
        
        # Parse JSON fields
        if session_data.get("config"):
            session_data["config"] = json.loads(session_data["config"])
        if session_data.get("context"):
            session_data["context"] = json.loads(session_data["context"])
        
        return session_data
    
    async def add_message(self, session_id: str, message: SessionMessage) -> None:
        """Add message to Redis"""
        await self._ensure_connection()
        
        session_key = f"{self.key_prefix}session:{session_id}"
        messages_key = f"{self.key_prefix}messages:{session_id}"
        
        # Serialize message
        message_data = {
            "message_id": message.message_id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": json.dumps(message.metadata),
            "provider_message_id": message.provider_message_id,
            "provider_metadata": json.dumps(message.provider_metadata)
        }
        
        # Add to message list
        await self.redis_client.lpush(messages_key, json.dumps(message_data))
        
        # Update session
        await self.redis_client.hincrby(session_key, "message_count", 1)
        await self.redis_client.hset(session_key, "last_activity", datetime.now().isoformat())
    
    async def get_messages(self, session_id: str, limit: Optional[int] = None, role: Optional[str] = None, since: Optional[datetime] = None) -> List[SessionMessage]:
        """Get messages from Redis"""
        await self._ensure_connection()
        
        messages_key = f"{self.key_prefix}messages:{session_id}"
        
        # Get all messages (newest first)
        raw_messages = await self.redis_client.lrange(messages_key, 0, -1)
        
        messages = []
        for raw_message in raw_messages:
            message_data = json.loads(raw_message)
            
            # Parse timestamp
            timestamp = datetime.fromisoformat(message_data["timestamp"])
            
            # Apply filters
            if role and message_data["role"] != role:
                continue
            if since and timestamp < since:
                continue
            
            message = SessionMessage(
                message_id=message_data["message_id"],
                session_id=message_data["session_id"],
                role=message_data["role"],
                content=message_data["content"],
                timestamp=timestamp,
                metadata=json.loads(message_data.get("metadata", "{}")),
                provider_message_id=message_data.get("provider_message_id"),
                provider_metadata=json.loads(message_data.get("provider_metadata", "{}"))
            )
            messages.append(message)
            
            if limit and len(messages) >= limit:
                break
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            await self._ensure_connection()
            await self.redis_client.ping()
            
            info = await self.redis_client.info("memory")
            
            return {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

async def redis_storage_example():
    # Create Redis storage
    redis_storage = RedisSessionStorage(
        redis_url="redis://localhost:6379",
        key_prefix="langswarm:prod:"
    )
    
    # Create manager with Redis storage
    manager = create_session_manager(
        storage=redis_storage,
        providers={"openai": "your_api_key"}
    )
    
    # Test Redis storage
    session = await manager.create_session("redis_user", "openai", "gpt-4")
    
    # Send messages
    for i in range(5):
        await session.send_message(f"Message {i+1} stored in Redis")
    
    # Verify storage
    messages = await session.get_messages()
    print(f"Retrieved {len(messages)} messages from Redis")
    
    # Check Redis health
    health = await redis_storage.health_check()
    print(f"Redis health: {health}")
    
    # Clean up
    await redis_storage.close()

asyncio.run(redis_storage_example())
```

---

## 🎯 Advanced Session Patterns

### **9. Multi-User Collaborative Session**

```python
"""
Multi-user collaborative session with participant management
"""
import asyncio
from datetime import datetime
from langswarm.core.session import create_session_manager

class CollaborativeSessionManager:
    """Manage multi-user collaborative sessions"""
    
    def __init__(self, base_manager):
        self.base_manager = base_manager
        self.collaborative_sessions = {}
        self.participants = {}
    
    async def create_collaborative_session(
        self,
        session_name: str,
        creator_id: str,
        provider: str,
        model: str
    ):
        """Create a new collaborative session"""
        # Create base session
        session = await self.base_manager.create_session(
            user_id=f"collab_{session_name}",
            provider=provider,
            model=model,
            session_config={
                "name": session_name,
                "description": f"Collaborative session created by {creator_id}",
                "tags": ["collaborative", "multi-user"]
            }
        )
        
        # Set up collaborative metadata
        await session.update_context({
            "collaborative": True,
            "creator": creator_id,
            "participants": [creator_id],
            "permissions": {creator_id: ["read", "write", "admin"]},
            "created_at": datetime.now().isoformat()
        })
        
        self.collaborative_sessions[session_name] = session
        self.participants[session_name] = {creator_id}
        
        return session
    
    async def add_participant(
        self,
        session_name: str,
        user_id: str,
        permissions: list = None
    ):
        """Add participant to collaborative session"""
        if session_name not in self.collaborative_sessions:
            raise ValueError(f"Session {session_name} not found")
        
        session = self.collaborative_sessions[session_name]
        permissions = permissions or ["read", "write"]
        
        # Update session context
        context = await session.get_context()
        context.user_context["participants"].append(user_id)
        context.user_context["permissions"][user_id] = permissions
        
        await session.update_context(context.user_context)
        
        # Add to local tracking
        self.participants[session_name].add(user_id)
        
        # Notify other participants
        await self._notify_participants(
            session_name,
            f"{user_id} joined the collaborative session",
            exclude=[user_id]
        )
    
    async def send_message_as_participant(
        self,
        session_name: str,
        user_id: str,
        message: str
    ):
        """Send message as specific participant"""
        if session_name not in self.collaborative_sessions:
            raise ValueError(f"Session {session_name} not found")
        
        session = self.collaborative_sessions[session_name]
        
        # Check permissions
        context = await session.get_context()
        permissions = context.user_context.get("permissions", {}).get(user_id, [])
        
        if "write" not in permissions:
            raise PermissionError(f"User {user_id} does not have write permission")
        
        # Send message with participant metadata
        response = await session.send_message(
            message,
            metadata={
                "participant": user_id,
                "collaborative": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Notify other participants
        await self._notify_participants(
            session_name,
            f"New message from {user_id}",
            exclude=[user_id]
        )
        
        return response
    
    async def get_session_participants(self, session_name: str):
        """Get list of session participants"""
        if session_name not in self.collaborative_sessions:
            return []
        
        return list(self.participants[session_name])
    
    async def _notify_participants(self, session_name: str, notification: str, exclude: list = None):
        """Notify participants of session events"""
        exclude = exclude or []
        participants = self.participants.get(session_name, set())
        
        for participant in participants:
            if participant not in exclude:
                # In a real implementation, this would send notifications
                # via websockets, email, etc.
                print(f"Notification to {participant}: {notification}")

async def collaborative_session_example():
    # Create base manager
    base_manager = create_session_manager(
        storage="sqlite",
        providers={"openai": "your_api_key"}
    )
    
    # Create collaborative manager
    collab_manager = CollaborativeSessionManager(base_manager)
    
    # Create collaborative session
    session = await collab_manager.create_collaborative_session(
        session_name="code_review_session",
        creator_id="alice",
        provider="openai",
        model="gpt-4"
    )
    
    print(f"Created collaborative session: {session.session_id}")
    
    # Add participants
    await collab_manager.add_participant("code_review_session", "bob", ["read", "write"])
    await collab_manager.add_participant("code_review_session", "charlie", ["read"])
    
    participants = await collab_manager.get_session_participants("code_review_session")
    print(f"Participants: {participants}")
    
    # Participants send messages
    await collab_manager.send_message_as_participant(
        "code_review_session",
        "alice", 
        "Let's review this Python function for optimization opportunities."
    )
    
    await collab_manager.send_message_as_participant(
        "code_review_session",
        "bob",
        "I notice we could use list comprehension here to improve readability."
    )
    
    # Get conversation history
    messages = await session.get_messages()
    print(f"\nCollaborative conversation ({len(messages)} messages):")
    
    for msg in messages[-5:]:  # Show last 5 messages
        participant = msg.metadata.get("participant", "Assistant")
        print(f"{participant}: {msg.content[:100]}...")

asyncio.run(collaborative_session_example())
```

### **10. Streaming Response Session**

```python
"""
Session with streaming response support
"""
import asyncio
from langswarm.core.session import create_session_manager

class StreamingSessionWrapper:
    """Wrapper to add streaming capabilities to sessions"""
    
    def __init__(self, session):
        self.session = session
    
    async def send_message_stream(self, content: str):
        """Send message and stream response chunks"""
        # Check if provider supports streaming
        if hasattr(self.session.provider_session, 'send_message_stream'):
            # Use native provider streaming
            full_response = ""
            async for chunk in self.session.provider_session.send_message_stream(content):
                full_response += chunk
                yield chunk
            
            # Store complete message
            await self._store_complete_message(content, full_response)
        else:
            # Simulate streaming for non-streaming providers
            response = await self.session.send_message(content)
            
            # Simulate streaming by yielding words
            words = response.content.split()
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                await asyncio.sleep(0.05)  # Small delay for streaming effect
    
    async def _store_complete_message(self, user_content: str, assistant_content: str):
        """Store complete conversation in session"""
        # This would typically be handled by the provider session
        # but we're showing how to handle it manually if needed
        pass
    
    def __getattr__(self, name):
        """Delegate other methods to the wrapped session"""
        return getattr(self.session, name)

async def streaming_session_example():
    # Create session manager
    manager = create_session_manager(
        storage="memory",
        providers={"openai": "your_api_key"}
    )
    
    # Create session
    base_session = await manager.create_session("stream_user", "openai", "gpt-4")
    
    # Wrap with streaming capabilities
    streaming_session = StreamingSessionWrapper(base_session)
    
    # Test streaming response
    questions = [
        "Explain the concept of machine learning in detail",
        "What are the main types of machine learning algorithms?",
        "Can you provide a simple example of a neural network?"
    ]
    
    for question in questions:
        print(f"\nUser: {question}")
        print("Assistant: ", end="", flush=True)
        
        # Stream response word by word
        async for chunk in streaming_session.send_message_stream(question):
            print(chunk, end="", flush=True)
        
        print()  # New line after complete response
        
        # Show session metrics
        metrics = await streaming_session.get_metrics()
        print(f"Messages: {metrics.total_messages}")

async def real_streaming_example():
    """Example with actual streaming provider"""
    
    class StreamingProviderSession:
        """Mock streaming provider for demonstration"""
        
        def __init__(self, session_id, model):
            self.session_id = session_id
            self.model = model
        
        async def send_message_stream(self, content: str):
            """Simulate streaming response"""
            # In real implementation, this would call streaming API
            response_words = [
                "This", "is", "a", "streaming", "response", "that", 
                "demonstrates", "how", "real-time", "AI", "responses", 
                "can", "be", "delivered", "word", "by", "word", "."
            ]
            
            for word in response_words:
                yield word + " "
                await asyncio.sleep(0.1)  # Simulate network delay
    
    # Use streaming provider
    streaming_provider = StreamingProviderSession("test_session", "streaming-model")
    
    print("Streaming Response Demo:")
    print("Assistant: ", end="", flush=True)
    
    async for chunk in streaming_provider.send_message_stream("Tell me about AI"):
        print(chunk, end="", flush=True)
    
    print("\n\nStreaming complete!")

# Run examples
asyncio.run(streaming_session_example())
print("\n" + "="*50 + "\n")
asyncio.run(real_streaming_example())
```

---

## 🏭 Production Examples

### **11. High-Scale Production Setup**

```python
"""
Production-ready session management with monitoring and scaling
"""
import asyncio
import logging
from datetime import datetime, timedelta
from langswarm.core.session import create_session_manager
from langswarm.core.session.interfaces import ISessionMiddleware, ISessionLifecycleHook

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionMetricsMiddleware(ISessionMiddleware):
    """Production metrics collection middleware"""
    
    def __init__(self):
        self.metrics = {
            "messages_processed": 0,
            "processing_times": [],
            "error_count": 0
        }
    
    async def process_message(self, session_id: str, message, context) -> None:
        """Collect production metrics"""
        start_time = datetime.now()
        
        try:
            # Process message (pass through)
            processed_message = message
            
            # Record processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["processing_times"].append(processing_time)
            self.metrics["messages_processed"] += 1
            
            # Keep only recent processing times
            if len(self.metrics["processing_times"]) > 1000:
                self.metrics["processing_times"] = self.metrics["processing_times"][-1000:]
            
            return processed_message
            
        except Exception as e:
            self.metrics["error_count"] += 1
            logger.error(f"Middleware error in session {session_id}: {e}")
            raise
    
    def get_metrics(self):
        """Get current metrics"""
        if self.metrics["processing_times"]:
            avg_time = sum(self.metrics["processing_times"]) / len(self.metrics["processing_times"])
            max_time = max(self.metrics["processing_times"])
        else:
            avg_time = max_time = 0
        
        return {
            "messages_processed": self.metrics["messages_processed"],
            "avg_processing_time_ms": avg_time,
            "max_processing_time_ms": max_time,
            "error_count": self.metrics["error_count"],
            "error_rate": self.metrics["error_count"] / max(1, self.metrics["messages_processed"])
        }

class ProductionMonitoringHook(ISessionLifecycleHook):
    """Production monitoring and alerting hook"""
    
    def __init__(self):
        self.session_counts = {"created": 0, "archived": 0, "errors": 0}
        self.active_sessions = set()
    
    async def on_session_created(self, session_id: str, user_id: str, provider: str, model: str) -> None:
        """Track session creation"""
        self.session_counts["created"] += 1
        self.active_sessions.add(session_id)
        
        logger.info(f"Session created: {session_id} for user {user_id} using {provider}/{model}")
        
        # Alert if too many active sessions
        if len(self.active_sessions) > 1000:
            logger.warning(f"High session count: {len(self.active_sessions)} active sessions")
    
    async def on_session_archived(self, session_id: str) -> None:
        """Track session archival"""
        self.session_counts["archived"] += 1
        self.active_sessions.discard(session_id)
        
        logger.info(f"Session archived: {session_id}")
    
    async def on_session_error(self, session_id: str, error: Exception) -> None:
        """Track session errors"""
        self.session_counts["errors"] += 1
        
        logger.error(f"Session error in {session_id}: {error}")
        
        # Alert on high error rate
        total_sessions = self.session_counts["created"]
        error_rate = self.session_counts["errors"] / max(1, total_sessions)
        
        if error_rate > 0.05:  # 5% error rate threshold
            logger.critical(f"High error rate: {error_rate:.2%} ({self.session_counts['errors']}/{total_sessions})")
    
    def get_status(self):
        """Get monitoring status"""
        return {
            "active_sessions": len(self.active_sessions),
            "total_created": self.session_counts["created"],
            "total_archived": self.session_counts["archived"],
            "total_errors": self.session_counts["errors"],
            "error_rate": self.session_counts["errors"] / max(1, self.session_counts["created"])
        }

async def production_setup_example():
    """Production session management setup"""
    
    # Create production metrics and monitoring
    metrics_middleware = ProductionMetricsMiddleware()
    monitoring_hook = ProductionMonitoringHook()
    
    # Create production session manager
    manager = create_session_manager(
        storage="sqlite",
        storage_config={
            "db_path": "/data/production_sessions.db",
            "pool_size": 50,      # Large pool for production
            "max_overflow": 100,  # Allow burst connections
            "enable_wal": True,   # Better concurrency
            "auto_vacuum": True   # Automatic maintenance
        },
        providers={
            "openai": "your_openai_api_key",
            "anthropic": "your_anthropic_api_key"
        },
        middleware=[metrics_middleware],
        hooks=[monitoring_hook],
        cleanup_config={
            "archive_after_days": 7,    # Archive old sessions
            "delete_after_days": 30,    # Delete archived sessions
            "cleanup_interval_hours": 6  # Run cleanup every 6 hours
        }
    )
    
    logger.info("Production session manager initialized")
    
    # Simulate production load
    await simulate_production_load(manager, metrics_middleware, monitoring_hook)

async def simulate_production_load(manager, metrics_middleware, monitoring_hook):
    """Simulate realistic production load"""
    
    logger.info("Starting production load simulation")
    
    # Create concurrent sessions
    sessions = []
    for i in range(20):  # 20 concurrent users
        try:
            session = await manager.create_session(
                user_id=f"prod_user_{i:03d}",
                provider="openai" if i % 2 == 0 else "anthropic",
                model="gpt-4" if i % 2 == 0 else "claude-3-sonnet-20240229"
            )
            sessions.append(session)
        except Exception as e:
            logger.error(f"Failed to create session {i}: {e}")
    
    logger.info(f"Created {len(sessions)} production sessions")
    
    # Simulate concurrent message processing
    async def user_interaction(session, user_num):
        """Simulate realistic user interaction"""
        messages = [
            f"Hello, I'm user {user_num}. Can you help me with a technical question?",
            "I'm working on a Python project and need advice on best practices.",
            "What's the difference between lists and tuples in Python?",
            "Can you show me an example of error handling?",
            "Thank you for your help!"
        ]
        
        for msg in messages:
            try:
                await session.send_message(msg)
                await asyncio.sleep(1)  # Realistic delay between messages
            except Exception as e:
                logger.error(f"Error in user {user_num} interaction: {e}")
    
    # Run concurrent user interactions
    await asyncio.gather(*[
        user_interaction(session, i) 
        for i, session in enumerate(sessions)
    ])
    
    logger.info("Completed production load simulation")
    
    # Report production metrics
    metrics = metrics_middleware.get_metrics()
    status = monitoring_hook.get_status()
    
    logger.info("Production Metrics Report:")
    logger.info(f"  Messages processed: {metrics['messages_processed']}")
    logger.info(f"  Average processing time: {metrics['avg_processing_time_ms']:.2f}ms")
    logger.info(f"  Max processing time: {metrics['max_processing_time_ms']:.2f}ms")
    logger.info(f"  Error rate: {metrics['error_rate']:.2%}")
    
    logger.info("Session Status Report:")
    logger.info(f"  Active sessions: {status['active_sessions']}")
    logger.info(f"  Total created: {status['total_created']}")
    logger.info(f"  Total archived: {status['total_archived']}")
    logger.info(f"  Total errors: {status['total_errors']}")
    
    # Clean up sessions
    for session in sessions:
        await session.archive()
    
    logger.info("Production simulation completed")

asyncio.run(production_setup_example())
```

### **12. Session Analytics and Monitoring**

```python
"""
Comprehensive session analytics and monitoring
"""
import asyncio
import json
from datetime import datetime, timedelta
from collections import defaultdict
from langswarm.core.session import create_session_manager

class SessionAnalytics:
    """Comprehensive session analytics system"""
    
    def __init__(self):
        self.analytics_data = {
            "sessions": [],
            "messages": [],
            "user_behavior": defaultdict(dict),
            "provider_stats": defaultdict(int),
            "model_stats": defaultdict(int),
            "hourly_activity": defaultdict(int)
        }
    
    async def track_session_created(self, session_id: str, user_id: str, provider: str, model: str):
        """Track session creation"""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "total_tokens": 0,
            "duration_minutes": 0
        }
        
        self.analytics_data["sessions"].append(session_data)
        self.analytics_data["provider_stats"][provider] += 1
        self.analytics_data["model_stats"][model] += 1
        
        # Track hourly activity
        hour = datetime.now().hour
        self.analytics_data["hourly_activity"][hour] += 1
    
    async def track_message_sent(self, session_id: str, message_data: dict):
        """Track message activity"""
        message_record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "role": message_data.get("role"),
            "content_length": len(message_data.get("content", "")),
            "processing_time_ms": message_data.get("processing_time_ms", 0),
            "tokens_used": message_data.get("tokens_used", 0)
        }
        
        self.analytics_data["messages"].append(message_record)
        
        # Update session stats
        for session in self.analytics_data["sessions"]:
            if session["session_id"] == session_id:
                session["message_count"] += 1
                session["total_tokens"] += message_record["tokens_used"]
                break
    
    async def track_user_behavior(self, user_id: str, behavior_data: dict):
        """Track user behavior patterns"""
        if user_id not in self.analytics_data["user_behavior"]:
            self.analytics_data["user_behavior"][user_id] = {
                "total_sessions": 0,
                "total_messages": 0,
                "avg_session_length": 0,
                "preferred_providers": defaultdict(int),
                "activity_hours": defaultdict(int),
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
        
        user_data = self.analytics_data["user_behavior"][user_id]
        user_data.update(behavior_data)
        user_data["last_seen"] = datetime.now().isoformat()
    
    def generate_analytics_report(self):
        """Generate comprehensive analytics report"""
        total_sessions = len(self.analytics_data["sessions"])
        total_messages = len(self.analytics_data["messages"])
        
        if total_sessions == 0:
            return {"error": "No analytics data available"}
        
        # Calculate session statistics
        session_durations = []
        message_counts = []
        
        for session in self.analytics_data["sessions"]:
            if session["message_count"] > 0:
                message_counts.append(session["message_count"])
        
        # Calculate message statistics
        processing_times = []
        message_lengths = []
        
        for message in self.analytics_data["messages"]:
            if message["processing_time_ms"] > 0:
                processing_times.append(message["processing_time_ms"])
            message_lengths.append(message["content_length"])
        
        # Generate report
        report = {
            "generated_at": datetime.now().isoformat(),
            "overview": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "unique_users": len(self.analytics_data["user_behavior"]),
                "avg_messages_per_session": sum(message_counts) / len(message_counts) if message_counts else 0
            },
            "provider_distribution": dict(self.analytics_data["provider_stats"]),
            "model_distribution": dict(self.analytics_data["model_stats"]),
            "performance": {
                "avg_processing_time_ms": sum(processing_times) / len(processing_times) if processing_times else 0,
                "max_processing_time_ms": max(processing_times) if processing_times else 0,
                "avg_message_length": sum(message_lengths) / len(message_lengths) if message_lengths else 0
            },
            "activity_patterns": {
                "hourly_distribution": dict(self.analytics_data["hourly_activity"]),
                "peak_hour": max(self.analytics_data["hourly_activity"], key=self.analytics_data["hourly_activity"].get) if self.analytics_data["hourly_activity"] else None
            },
            "user_behavior": {
                "active_users": len([u for u in self.analytics_data["user_behavior"].values() if u["total_sessions"] > 0]),
                "power_users": len([u for u in self.analytics_data["user_behavior"].values() if u["total_sessions"] > 10])
            }
        }
        
        return report
    
    def export_analytics(self, filepath: str):
        """Export analytics data to file"""
        with open(filepath, 'w') as f:
            json.dump(self.analytics_data, f, indent=2, default=str)

async def analytics_example():
    """Demonstrate session analytics"""
    
    # Create analytics system
    analytics = SessionAnalytics()
    
    # Create session manager
    manager = create_session_manager(
        storage="memory",
        providers={"openai": "your_api_key", "anthropic": "your_api_key"}
    )
    
    # Simulate user activity with analytics tracking
    users = ["alice", "bob", "charlie", "diana", "eve"]
    providers = ["openai", "anthropic"]
    models = ["gpt-4", "claude-3-sonnet-20240229"]
    
    sessions = []
    
    # Create sessions and track analytics
    for i, user in enumerate(users):
        provider = providers[i % 2]
        model = models[i % 2]
        
        session = await manager.create_session(user, provider, model)
        sessions.append(session)
        
        # Track session creation
        await analytics.track_session_created(
            session.session_id, user, provider, model
        )
        
        # Track user behavior
        await analytics.track_user_behavior(user, {
            "total_sessions": 1,
            "preferred_providers": {provider: 1}
        })
    
    # Simulate messages with analytics
    for i, session in enumerate(sessions):
        user = users[i]
        message_count = (i + 1) * 2  # Varying message counts
        
        for j in range(message_count):
            # Send message
            response = await session.send_message(f"Message {j+1} from {user}")
            
            # Track message analytics
            await analytics.track_message_sent(session.session_id, {
                "role": "user",
                "content": f"Message {j+1} from {user}",
                "processing_time_ms": 150 + (j * 10),  # Simulated processing time
                "tokens_used": 50 + (j * 5)  # Simulated token usage
            })
            
            await analytics.track_message_sent(session.session_id, {
                "role": "assistant", 
                "content": response.content,
                "processing_time_ms": 200 + (j * 15),
                "tokens_used": 75 + (j * 8)
            })
    
    # Generate analytics report
    report = analytics.generate_analytics_report()
    
    print("Session Analytics Report")
    print("=" * 50)
    print(f"Generated at: {report['generated_at']}")
    print()
    
    print("Overview:")
    for key, value in report["overview"].items():
        print(f"  {key}: {value}")
    print()
    
    print("Provider Distribution:")
    for provider, count in report["provider_distribution"].items():
        print(f"  {provider}: {count}")
    print()
    
    print("Performance Metrics:")
    for key, value in report["performance"].items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    print()
    
    print("User Behavior:")
    for key, value in report["user_behavior"].items():
        print(f"  {key}: {value}")
    
    # Export analytics data
    analytics.export_analytics("session_analytics.json")
    print("\nAnalytics data exported to session_analytics.json")

asyncio.run(analytics_example())
```

---

## 📋 Session Management Best Practices

### **Development Best Practices**
- **Start Simple**: Begin with in-memory storage and mock providers for development
- **Test Thoroughly**: Test session lifecycle, message handling, and error scenarios
- **Use Presets**: Leverage development and production presets for consistent configuration
- **Monitor Performance**: Track session performance and optimization opportunities

### **Production Best Practices**
- **Choose Appropriate Storage**: Use SQLite for moderate scale, Redis for distributed systems
- **Configure Connection Pools**: Set appropriate pool sizes for storage backends
- **Implement Monitoring**: Add comprehensive monitoring and alerting
- **Plan for Scale**: Design session management to handle expected load

### **Security Best Practices**
- **Secure API Keys**: Store API keys securely using environment variables
- **Session Isolation**: Ensure proper user session isolation
- **Data Encryption**: Encrypt sensitive session data at rest and in transit
- **Access Controls**: Implement proper session access controls and permissions

### **Performance Best Practices**
- **Async Operations**: Always use async/await for session operations
- **Batch Operations**: Use batch operations for multiple session updates
- **Optimize Queries**: Ensure database queries are optimized with indexes
- **Implement Caching**: Cache frequently accessed session data

---

**These examples demonstrate the full capabilities of LangSwarm V2's session management system, providing practical patterns for real-world applications across different scales and use cases.**
