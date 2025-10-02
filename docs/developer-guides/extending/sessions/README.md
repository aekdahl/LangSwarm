# Extending LangSwarm V2 Session Management

**Complete guide for extending and customizing the V2 session management system**

## 🎯 Overview

LangSwarm V2's session management system is designed for extensibility, allowing developers to add custom storage backends, provider integrations, middleware, lifecycle hooks, and session behaviors while maintaining compatibility with the core system.

**Extension Capabilities:**
- **Custom Storage Backends**: Add support for additional storage systems
- **Custom Provider Sessions**: Integrate new LLM providers
- **Custom Middleware**: Implement message processing pipelines
- **Custom Lifecycle Hooks**: Add session event handling
- **Custom Session Behaviors**: Extend session functionality
- **Integration Patterns**: Integrate with external systems

---

## 💾 Custom Storage Backends

### **Implementing Custom Storage**

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from langswarm.core.session.interfaces import (
    ISessionStorage,
    SessionMessage,
    SessionContext,
    SessionStatus
)

class RedisSessionStorage(ISessionStorage):
    """Redis-based session storage implementation"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = None,
        db: int = 0,
        key_prefix: str = "langswarm:session:",
        ttl_hours: int = 24 * 7  # 1 week default
    ):
        """Initialize Redis storage
        
        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            db: Redis database number
            key_prefix: Key prefix for session data
            ttl_hours: Session TTL in hours
        """
        import redis
        self.redis = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True
        )
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_hours * 3600
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str,
        config: SessionConfig,
        context: SessionContext
    ) -> None:
        """Create session in Redis"""
        session_key = f"{self.key_prefix}{session_id}"
        messages_key = f"{session_key}:messages"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "status": SessionStatus.ACTIVE.value,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
            "config": json.dumps(config.__dict__),
            "context": json.dumps(context.__dict__)
        }
        
        # Store session data
        await self._async_execute(
            self.redis.hmset, session_key, session_data
        )
        
        # Set TTL
        await self._async_execute(
            self.redis.expire, session_key, self.ttl_seconds
        )
        
        # Initialize empty message list
        await self._async_execute(
            self.redis.expire, messages_key, self.ttl_seconds
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from Redis"""
        session_key = f"{self.key_prefix}{session_id}"
        
        session_data = await self._async_execute(
            self.redis.hgetall, session_key
        )
        
        if not session_data:
            return None
        
        # Parse JSON fields
        session_data["config"] = json.loads(session_data.get("config", "{}"))
        session_data["context"] = json.loads(session_data.get("context", "{}"))
        session_data["message_count"] = int(session_data.get("message_count", 0))
        
        return session_data
    
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Update session data in Redis"""
        session_key = f"{self.key_prefix}{session_id}"
        
        # Convert complex objects to JSON
        update_data = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                update_data[key] = json.dumps(value)
            elif isinstance(value, datetime):
                update_data[key] = value.isoformat()
            else:
                update_data[key] = str(value)
        
        await self._async_execute(
            self.redis.hmset, session_key, update_data
        )
        
        # Refresh TTL
        await self._async_execute(
            self.redis.expire, session_key, self.ttl_seconds
        )
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session from Redis"""
        session_key = f"{self.key_prefix}{session_id}"
        messages_key = f"{session_key}:messages"
        
        await self._async_execute(self.redis.delete, session_key, messages_key)
    
    async def add_message(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Add message to session in Redis"""
        session_key = f"{self.key_prefix}{session_id}"
        messages_key = f"{session_key}:messages"
        
        # Store message as JSON
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
        
        # Add to list and update session
        await self._async_execute(
            self.redis.lpush, messages_key, json.dumps(message_data)
        )
        
        # Update message count
        await self._async_execute(
            self.redis.hincrby, session_key, "message_count", 1
        )
        
        # Update last activity
        await self._async_execute(
            self.redis.hset, session_key, "last_activity", 
            datetime.now().isoformat()
        )
        
        # Refresh TTL
        await self._async_execute(
            self.redis.expire, messages_key, self.ttl_seconds
        )
    
    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        role: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[SessionMessage]:
        """Get session messages from Redis"""
        messages_key = f"{self.key_prefix}{session_id}:messages"
        
        # Get messages (latest first)
        raw_messages = await self._async_execute(
            self.redis.lrange, messages_key, 0, -1
        )
        
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
            
            # Create SessionMessage object
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
            
            # Apply limit
            if limit and len(messages) >= limit:
                break
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    async def _async_execute(self, func, *args, **kwargs):
        """Execute Redis command asynchronously"""
        import asyncio
        
        # Run Redis command in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis connection health"""
        try:
            await self._async_execute(self.redis.ping)
            info = await self._async_execute(self.redis.info, "memory")
            
            return {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close Redis connection"""
        self.redis.close()

# Register custom storage backend
from langswarm.core.session.storage import StorageFactory

StorageFactory.register_backend(
    "redis",
    RedisSessionStorage,
    config_schema={
        "host": {"type": "string", "default": "localhost"},
        "port": {"type": "integer", "default": 6379},
        "password": {"type": "string", "required": False},
        "db": {"type": "integer", "default": 0},
        "ttl_hours": {"type": "integer", "default": 168}
    }
)

# Usage
redis_storage = StorageFactory.create("redis", {
    "host": "redis.example.com",
    "port": 6379,
    "password": "secure_password",
    "ttl_hours": 72
})

manager = SessionManager(storage=redis_storage)
```

### **MongoDB Storage Backend**

```python
class MongoDBSessionStorage(ISessionStorage):
    """MongoDB-based session storage implementation"""
    
    def __init__(
        self,
        connection_string: str,
        database_name: str = "langswarm",
        collection_name: str = "sessions",
        message_collection: str = "messages"
    ):
        """Initialize MongoDB storage
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name
            collection_name: Sessions collection name
            message_collection: Messages collection name
        """
        from motor.motor_asyncio import AsyncIOMotorClient
        
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[database_name]
        self.sessions = self.db[collection_name]
        self.messages = self.db[message_collection]
        
        # Create indexes for performance
        self._create_indexes()
    
    async def _create_indexes(self):
        """Create database indexes"""
        # Session indexes
        await self.sessions.create_index("session_id", unique=True)
        await self.sessions.create_index("user_id")
        await self.sessions.create_index("status")
        await self.sessions.create_index("created_at")
        await self.sessions.create_index("last_activity")
        
        # Message indexes
        await self.messages.create_index("session_id")
        await self.messages.create_index("timestamp")
        await self.messages.create_index([("session_id", 1), ("timestamp", -1)])
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str,
        config: SessionConfig,
        context: SessionContext
    ) -> None:
        """Create session in MongoDB"""
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "status": SessionStatus.ACTIVE.value,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0,
            "config": config.__dict__,
            "context": context.__dict__
        }
        
        await self.sessions.insert_one(session_doc)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from MongoDB"""
        session_doc = await self.sessions.find_one({"session_id": session_id})
        
        if session_doc:
            # Remove MongoDB _id field
            session_doc.pop("_id", None)
            
        return session_doc
    
    async def add_message(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Add message to MongoDB"""
        message_doc = {
            "message_id": message.message_id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp,
            "metadata": message.metadata,
            "provider_message_id": message.provider_message_id,
            "provider_metadata": message.provider_metadata
        }
        
        # Insert message and update session
        await self.messages.insert_one(message_doc)
        await self.sessions.update_one(
            {"session_id": session_id},
            {
                "$inc": {"message_count": 1},
                "$set": {"last_activity": datetime.now()}
            }
        )
    
    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        role: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[SessionMessage]:
        """Get session messages from MongoDB"""
        query = {"session_id": session_id}
        
        if role:
            query["role"] = role
        if since:
            query["timestamp"] = {"$gte": since}
        
        cursor = self.messages.find(query).sort("timestamp", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        messages = []
        async for doc in cursor:
            message = SessionMessage(
                message_id=doc["message_id"],
                session_id=doc["session_id"],
                role=doc["role"],
                content=doc["content"],
                timestamp=doc["timestamp"],
                metadata=doc.get("metadata", {}),
                provider_message_id=doc.get("provider_message_id"),
                provider_metadata=doc.get("provider_metadata", {})
            )
            messages.append(message)
        
        return messages
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB connection health"""
        try:
            # Test connection
            await self.client.admin.command("ping")
            
            # Get database stats
            stats = await self.db.command("dbStats")
            
            return {
                "status": "healthy",
                "database": self.db.name,
                "collections": stats.get("collections"),
                "data_size": stats.get("dataSize"),
                "storage_size": stats.get("storageSize")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Register MongoDB backend
StorageFactory.register_backend("mongodb", MongoDBSessionStorage)
```

---

## 🔌 Custom Provider Sessions

### **Implementing Custom Provider**

```python
from langswarm.core.session.interfaces import IProviderSession

class CustomProviderSession(IProviderSession):
    """Custom LLM provider session implementation"""
    
    def __init__(
        self,
        api_key: str,
        session_id: str,
        model: str,
        config: Dict[str, Any] = None
    ):
        """Initialize custom provider session
        
        Args:
            api_key: Provider API key
            session_id: LangSwarm session ID
            model: Model name
            config: Provider-specific configuration
        """
        self.api_key = api_key
        self.session_id = session_id
        self.model = model
        self.config = config or {}
        
        # Initialize provider client
        self.client = self._create_client()
        
        # Provider-specific session ID (if applicable)
        self._provider_session_id = None
        
        # Conversation history for providers without native sessions
        self._conversation_history = []
    
    @property
    def provider_session_id(self) -> Optional[str]:
        """Provider-specific session ID"""
        return self._provider_session_id
    
    def _create_client(self):
        """Create provider client"""
        # Initialize your provider's client here
        # This is provider-specific
        from custom_llm_provider import CustomLLMClient
        
        return CustomLLMClient(
            api_key=self.api_key,
            base_url=self.config.get("base_url"),
            timeout=self.config.get("timeout", 30)
        )
    
    async def send_message(
        self,
        content: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message using custom provider API"""
        try:
            # Add message to conversation history
            user_message = {
                "role": role,
                "content": content,
                "metadata": metadata or {}
            }
            self._conversation_history.append(user_message)
            
            # Prepare messages for provider
            provider_messages = self._format_messages_for_provider()
            
            # Call provider API
            response = await self._call_provider_api(provider_messages)
            
            # Parse provider response
            assistant_message = self._parse_provider_response(response)
            
            # Add assistant response to history
            self._conversation_history.append({
                "role": "assistant",
                "content": assistant_message["content"],
                "metadata": assistant_message.get("metadata", {})
            })
            
            # Create SessionMessage
            session_message = SessionMessage(
                message_id=self._generate_message_id(),
                session_id=self.session_id,
                role="assistant",
                content=assistant_message["content"],
                timestamp=datetime.now(),
                metadata=assistant_message.get("metadata", {}),
                provider_message_id=response.get("id"),
                provider_metadata={
                    "model": self.model,
                    "usage": response.get("usage", {}),
                    "finish_reason": response.get("finish_reason")
                }
            )
            
            return session_message
            
        except Exception as e:
            raise ProviderError(
                f"Custom provider API call failed: {str(e)}",
                session_id=self.session_id,
                error_code="API_CALL_FAILED"
            )
    
    def _format_messages_for_provider(self) -> List[Dict[str, Any]]:
        """Format conversation history for provider API"""
        provider_messages = []
        
        for message in self._conversation_history:
            # Convert to provider format
            provider_message = {
                "role": message["role"],
                "content": message["content"]
            }
            
            # Add provider-specific fields if needed
            if "system_prompt" in message.get("metadata", {}):
                provider_message["system"] = message["metadata"]["system_prompt"]
            
            provider_messages.append(provider_message)
        
        return provider_messages
    
    async def _call_provider_api(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call the custom provider API"""
        request_data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2048),
            "stream": False
        }
        
        # Add any custom provider parameters
        if "custom_params" in self.config:
            request_data.update(self.config["custom_params"])
        
        # Make API call (implement based on your provider)
        response = await self.client.chat.completions.create(**request_data)
        
        return response
    
    def _parse_provider_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse provider response to standard format"""
        # Extract message content (provider-specific)
        content = response["choices"][0]["message"]["content"]
        
        # Extract metadata
        metadata = {
            "model": response.get("model"),
            "created": response.get("created"),
            "usage": response.get("usage", {}),
            "finish_reason": response["choices"][0].get("finish_reason")
        }
        
        return {
            "content": content,
            "metadata": metadata
        }
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def get_provider_metadata(self) -> Dict[str, Any]:
        """Get provider-specific metadata"""
        return {
            "provider": "custom_provider",
            "model": self.model,
            "session_id": self.session_id,
            "provider_session_id": self._provider_session_id,
            "conversation_length": len(self._conversation_history),
            "config": self.config
        }
    
    async def update_provider_config(self, config: Dict[str, Any]) -> None:
        """Update provider-specific configuration"""
        self.config.update(config)
        
        # Recreate client if needed
        if any(key in config for key in ["api_key", "base_url", "timeout"]):
            self.client = self._create_client()
    
    async def cleanup_provider_resources(self) -> None:
        """Clean up provider-specific resources"""
        # Close client connections
        if hasattr(self.client, "close"):
            await self.client.close()
        
        # Clear conversation history if needed
        self._conversation_history.clear()

# Register custom provider
from langswarm.core.session.providers import ProviderSessionFactory

class CustomProviderFactory:
    """Factory for custom provider sessions"""
    
    @staticmethod
    def create_session(
        session_id: str,
        model: str,
        config: Dict[str, Any]
    ) -> CustomProviderSession:
        return CustomProviderSession(
            api_key=config["api_key"],
            session_id=session_id,
            model=model,
            config=config
        )

# Register with the provider factory
ProviderSessionFactory.register_provider(
    "custom_provider",
    CustomProviderFactory.create_session,
    default_config={
        "temperature": 0.7,
        "max_tokens": 2048,
        "timeout": 30
    }
)

# Usage
manager = create_session_manager(
    storage="sqlite",
    providers={
        "custom_provider": "your_custom_api_key"
    }
)

session = await manager.create_session(
    user_id="user123",
    provider="custom_provider",
    model="custom-model-v1"
)
```

### **Streaming Provider Support**

```python
class StreamingProviderSession(IProviderSession):
    """Provider session with streaming support"""
    
    async def send_message_stream(
        self,
        content: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """Send message and stream response"""
        
        # Add user message to history
        user_message = {
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self._conversation_history.append(user_message)
        
        # Prepare streaming request
        request_data = {
            "model": self.model,
            "messages": self._format_messages_for_provider(),
            "stream": True,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2048)
        }
        
        # Stream response
        full_response = ""
        async for chunk in self.client.chat.completions.create(**request_data):
            if chunk.choices[0].delta.content:
                content_chunk = chunk.choices[0].delta.content
                full_response += content_chunk
                yield content_chunk
        
        # Add complete response to history
        self._conversation_history.append({
            "role": "assistant", 
            "content": full_response,
            "metadata": {"streaming": True}
        })
    
    async def send_message(
        self,
        content: str,
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message and collect full response"""
        full_response = ""
        
        async for chunk in self.send_message_stream(content, role, metadata):
            full_response += chunk
        
        return SessionMessage(
            message_id=self._generate_message_id(),
            session_id=self.session_id,
            role="assistant",
            content=full_response,
            timestamp=datetime.now(),
            metadata=metadata or {},
            provider_metadata={"streaming": True}
        )

# Usage with streaming
async def handle_streaming_response():
    session = await manager.create_session(
        user_id="user123",
        provider="streaming_provider",
        model="stream-model"
    )
    
    print("Assistant: ", end="")
    async for chunk in session.provider_session.send_message_stream("Hello!"):
        print(chunk, end="", flush=True)
    print()  # New line after complete response
```

---

## 🔧 Custom Middleware

### **Message Processing Middleware**

```python
from langswarm.core.session.interfaces import ISessionMiddleware

class ContentFilterMiddleware(ISessionMiddleware):
    """Filter inappropriate content from messages"""
    
    def __init__(self, filter_config: Dict[str, Any] = None):
        self.filter_config = filter_config or {}
        self.blocked_words = self.filter_config.get("blocked_words", [])
        self.replacement_text = self.filter_config.get("replacement", "[FILTERED]")
        
    async def process_message(
        self,
        session_id: str,
        message: SessionMessage,
        context: SessionContext
    ) -> SessionMessage:
        """Filter message content"""
        
        # Only filter user messages
        if message.role != "user":
            return message
        
        # Apply content filters
        filtered_content = await self._filter_content(message.content)
        
        # Log if content was filtered
        if filtered_content != message.content:
            await self._log_filtered_content(session_id, message.content, filtered_content)
        
        # Update message content
        message.content = filtered_content
        
        # Add filter metadata
        message.metadata["content_filtered"] = filtered_content != message.content
        
        return message
    
    async def _filter_content(self, content: str) -> str:
        """Apply content filtering"""
        filtered_content = content
        
        # Simple word filtering
        for word in self.blocked_words:
            filtered_content = filtered_content.replace(word, self.replacement_text)
        
        # Advanced filtering (could integrate with external services)
        if self.filter_config.get("use_ai_filter"):
            filtered_content = await self._ai_content_filter(filtered_content)
        
        return filtered_content
    
    async def _ai_content_filter(self, content: str) -> str:
        """Use AI-based content filtering"""
        # Integrate with content moderation API
        # This is a placeholder for actual implementation
        return content
    
    async def _log_filtered_content(self, session_id: str, original: str, filtered: str):
        """Log filtered content for review"""
        import logging
        
        logger = logging.getLogger("content_filter")
        logger.warning(
            f"Content filtered in session {session_id}: "
            f"'{original[:50]}...' -> '{filtered[:50]}...'"
        )

class PersonalizationMiddleware(ISessionMiddleware):
    """Personalize messages based on user context"""
    
    def __init__(self, personalization_service):
        self.personalization_service = personalization_service
    
    async def process_message(
        self,
        session_id: str,
        message: SessionMessage,
        context: SessionContext
    ) -> SessionMessage:
        """Add personalization to messages"""
        
        if message.role == "user":
            # Enhance user message with context
            user_profile = context.user_context.get("profile", {})
            
            # Add user preferences to metadata
            message.metadata.update({
                "user_experience_level": user_profile.get("experience_level"),
                "preferred_style": user_profile.get("communication_style"),
                "interests": user_profile.get("interests", [])
            })
            
        elif message.role == "assistant":
            # Personalize assistant response
            personalized_content = await self.personalization_service.personalize(
                content=message.content,
                user_context=context.user_context
            )
            message.content = personalized_content
            message.metadata["personalized"] = True
        
        return message

class AnalyticsMiddleware(ISessionMiddleware):
    """Collect analytics on message patterns"""
    
    def __init__(self, analytics_service):
        self.analytics_service = analytics_service
    
    async def process_message(
        self,
        session_id: str,
        message: SessionMessage,
        context: SessionContext
    ) -> SessionMessage:
        """Collect message analytics"""
        
        # Extract analytics data
        analytics_data = {
            "session_id": session_id,
            "message_id": message.message_id,
            "role": message.role,
            "content_length": len(message.content),
            "timestamp": message.timestamp,
            "user_id": context.user_context.get("user_id"),
            "provider": context.system_context.get("provider"),
            "model": context.system_context.get("model")
        }
        
        # Add content analysis
        if message.role == "user":
            analytics_data.update({
                "intent": await self._detect_intent(message.content),
                "sentiment": await self._analyze_sentiment(message.content),
                "complexity": self._calculate_complexity(message.content)
            })
        
        # Send to analytics service
        await self.analytics_service.record_message(analytics_data)
        
        return message
    
    async def _detect_intent(self, content: str) -> str:
        """Detect user intent from message content"""
        # Implement intent detection
        return "question"  # Placeholder
    
    async def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment of message"""
        # Implement sentiment analysis
        return "neutral"  # Placeholder
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate message complexity score"""
        # Simple complexity based on length and structure
        word_count = len(content.split())
        return min(word_count / 50.0, 1.0)  # Normalized complexity
```

### **Middleware Chain Management**

```python
class MiddlewareChain:
    """Manage middleware execution order and dependencies"""
    
    def __init__(self):
        self.middleware = []
        self.middleware_metadata = {}
    
    def add_middleware(
        self,
        middleware: ISessionMiddleware,
        priority: int = 0,
        dependencies: List[str] = None,
        conditions: Dict[str, Any] = None
    ):
        """Add middleware with execution metadata"""
        self.middleware.append(middleware)
        self.middleware_metadata[middleware] = {
            "priority": priority,
            "dependencies": dependencies or [],
            "conditions": conditions or {},
            "name": middleware.__class__.__name__
        }
        
        # Sort by priority
        self.middleware.sort(
            key=lambda m: self.middleware_metadata[m]["priority"],
            reverse=True
        )
    
    async def process_message(
        self,
        session_id: str,
        message: SessionMessage,
        context: SessionContext
    ) -> SessionMessage:
        """Process message through middleware chain"""
        
        processed_message = message
        
        for middleware in self.middleware:
            metadata = self.middleware_metadata[middleware]
            
            # Check conditions
            if not self._check_conditions(metadata["conditions"], context):
                continue
            
            # Check dependencies
            if not self._check_dependencies(metadata["dependencies"], context):
                continue
            
            try:
                processed_message = await middleware.process_message(
                    session_id, processed_message, context
                )
            except Exception as e:
                # Handle middleware errors
                await self._handle_middleware_error(middleware, e, session_id, context)
                # Continue with other middleware
                continue
        
        return processed_message
    
    def _check_conditions(self, conditions: Dict[str, Any], context: SessionContext) -> bool:
        """Check if middleware conditions are met"""
        for key, expected_value in conditions.items():
            if key == "user_type":
                user_type = context.user_context.get("type")
                if user_type != expected_value:
                    return False
            elif key == "provider":
                provider = context.system_context.get("provider")
                if provider != expected_value:
                    return False
        
        return True
    
    def _check_dependencies(self, dependencies: List[str], context: SessionContext) -> bool:
        """Check if middleware dependencies are satisfied"""
        # Check if required middleware have already processed
        processed_middleware = context.system_context.get("processed_middleware", [])
        
        for dependency in dependencies:
            if dependency not in processed_middleware:
                return False
        
        return True
    
    async def _handle_middleware_error(
        self,
        middleware: ISessionMiddleware,
        error: Exception,
        session_id: str,
        context: SessionContext
    ):
        """Handle middleware processing errors"""
        import logging
        
        logger = logging.getLogger("middleware")
        logger.error(
            f"Middleware {middleware.__class__.__name__} failed "
            f"for session {session_id}: {error}"
        )
        
        # Call middleware error handler if available
        if hasattr(middleware, "on_error"):
            await middleware.on_error(session_id, error, context)

# Usage
middleware_chain = MiddlewareChain()

# Add middleware with priorities and conditions
middleware_chain.add_middleware(
    ContentFilterMiddleware(),
    priority=100,  # High priority - run first
    conditions={"user_type": "free"}  # Only for free users
)

middleware_chain.add_middleware(
    PersonalizationMiddleware(personalization_service),
    priority=50,   # Medium priority
    dependencies=["ContentFilterMiddleware"]  # Run after content filter
)

middleware_chain.add_middleware(
    AnalyticsMiddleware(analytics_service),
    priority=10    # Low priority - run last
)
```

---

## 🔗 Custom Lifecycle Hooks

### **Advanced Lifecycle Hooks**

```python
from langswarm.core.session.interfaces import ISessionLifecycleHook

class AdvancedMetricsHook(ISessionLifecycleHook):
    """Advanced metrics collection and analysis"""
    
    def __init__(self, metrics_backend, alert_thresholds: Dict[str, float] = None):
        self.metrics_backend = metrics_backend
        self.alert_thresholds = alert_thresholds or {}
        self.session_timers = {}
    
    async def on_session_created(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str
    ) -> None:
        """Track session creation metrics"""
        # Record session creation
        await self.metrics_backend.increment("sessions_created")
        await self.metrics_backend.increment(f"sessions_created_{provider}")
        
        # Start session timer
        self.session_timers[session_id] = datetime.now()
        
        # Track user engagement
        await self.metrics_backend.track_user_event(user_id, "session_created", {
            "provider": provider,
            "model": model
        })
    
    async def on_message_sent(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Track message metrics and patterns"""
        # Basic message metrics
        await self.metrics_backend.increment("messages_sent")
        await self.metrics_backend.increment(f"messages_{message.role}")
        
        # Content analysis
        content_stats = self._analyze_message_content(message.content)
        await self.metrics_backend.record_histogram(
            "message_length",
            content_stats["length"]
        )
        
        # Response time tracking (for assistant messages)
        if message.role == "assistant":
            processing_time = message.metadata.get("processing_time_ms")
            if processing_time:
                await self.metrics_backend.record_histogram(
                    "response_time_ms",
                    processing_time
                )
                
                # Check for slow responses
                if processing_time > self.alert_thresholds.get("slow_response_ms", 5000):
                    await self._send_alert(
                        "slow_response",
                        f"Slow response in session {session_id}: {processing_time}ms"
                    )
        
        # Token usage tracking
        if "token_count" in message.metadata:
            await self.metrics_backend.record_histogram(
                "token_usage",
                message.metadata["token_count"]
            )
    
    async def on_session_archived(self, session_id: str) -> None:
        """Track session completion metrics"""
        # Calculate session duration
        if session_id in self.session_timers:
            start_time = self.session_timers[session_id]
            duration = (datetime.now() - start_time).total_seconds()
            
            await self.metrics_backend.record_histogram(
                "session_duration_seconds",
                duration
            )
            
            # Clean up timer
            del self.session_timers[session_id]
        
        await self.metrics_backend.increment("sessions_archived")
    
    def _analyze_message_content(self, content: str) -> Dict[str, Any]:
        """Analyze message content for metrics"""
        return {
            "length": len(content),
            "word_count": len(content.split()),
            "has_code": "```" in content,
            "has_question": "?" in content
        }
    
    async def _send_alert(self, alert_type: str, message: str):
        """Send alert for important metrics"""
        # Implement alerting logic
        pass

class UserBehaviorHook(ISessionLifecycleHook):
    """Track user behavior patterns"""
    
    def __init__(self, behavior_analytics):
        self.behavior_analytics = behavior_analytics
        self.user_sessions = {}  # Track active sessions per user
    
    async def on_session_created(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str
    ) -> None:
        """Track user session patterns"""
        # Track concurrent sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        
        self.user_sessions[user_id].add(session_id)
        
        # Analyze user behavior
        await self.behavior_analytics.record_session_start(
            user_id=user_id,
            session_id=session_id,
            provider=provider,
            model=model,
            concurrent_sessions=len(self.user_sessions[user_id])
        )
        
        # Check for unusual patterns
        if len(self.user_sessions[user_id]) > 5:
            await self._flag_unusual_behavior(
                user_id,
                "high_concurrent_sessions",
                {"session_count": len(self.user_sessions[user_id])}
            )
    
    async def on_message_sent(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Analyze message patterns"""
        # Extract user from session (would need session context)
        # This is simplified for example
        
        if message.role == "user":
            # Analyze user message patterns
            pattern_data = {
                "message_length": len(message.content),
                "timestamp": message.timestamp,
                "contains_code": "```" in message.content,
                "contains_url": "http" in message.content
            }
            
            await self.behavior_analytics.record_user_message(
                session_id=session_id,
                pattern_data=pattern_data
            )
    
    async def _flag_unusual_behavior(
        self,
        user_id: str,
        behavior_type: str,
        data: Dict[str, Any]
    ):
        """Flag unusual user behavior"""
        await self.behavior_analytics.flag_behavior(
            user_id=user_id,
            behavior_type=behavior_type,
            data=data,
            timestamp=datetime.now()
        )

class SessionBackupHook(ISessionLifecycleHook):
    """Backup session data to external storage"""
    
    def __init__(self, backup_service, backup_triggers: List[str] = None):
        self.backup_service = backup_service
        self.backup_triggers = backup_triggers or ["archived", "every_10_messages"]
        self.message_counts = {}
    
    async def on_session_created(
        self,
        session_id: str,
        user_id: str,
        provider: str,
        model: str
    ) -> None:
        """Initialize backup tracking"""
        self.message_counts[session_id] = 0
        
        if "created" in self.backup_triggers:
            await self._backup_session(session_id, "session_created")
    
    async def on_message_sent(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Track messages for backup triggers"""
        self.message_counts[session_id] = self.message_counts.get(session_id, 0) + 1
        
        # Check for message count triggers
        if "every_10_messages" in self.backup_triggers:
            if self.message_counts[session_id] % 10 == 0:
                await self._backup_session(session_id, "message_milestone")
    
    async def on_session_archived(self, session_id: str) -> None:
        """Backup when session is archived"""
        if "archived" in self.backup_triggers:
            await self._backup_session(session_id, "session_archived")
        
        # Clean up tracking
        self.message_counts.pop(session_id, None)
    
    async def _backup_session(self, session_id: str, trigger: str):
        """Backup session data"""
        try:
            # Get session data (would need access to session manager)
            session_data = await self._get_session_data(session_id)
            
            # Upload to backup service
            backup_id = await self.backup_service.backup_session(
                session_id=session_id,
                data=session_data,
                trigger=trigger,
                timestamp=datetime.now()
            )
            
            logger.info(f"Session {session_id} backed up: {backup_id}")
            
        except Exception as e:
            logger.error(f"Failed to backup session {session_id}: {e}")
    
    async def _get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get complete session data for backup"""
        # This would need access to the session storage
        # Implementation depends on your backup requirements
        return {"session_id": session_id}  # Placeholder
```

---

## 🎯 Session Behavior Extensions

### **Custom Session Types**

```python
from langswarm.core.session.base import BaseSession

class MultiModalSession(BaseSession):
    """Session that supports text, images, and files"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.supported_modalities = ["text", "image", "file"]
    
    async def send_image_message(
        self,
        image_data: bytes,
        image_format: str,
        caption: str = "",
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message with image"""
        # Process image
        processed_image = await self._process_image(image_data, image_format)
        
        # Create message content
        content = {
            "type": "image",
            "image": processed_image,
            "caption": caption
        }
        
        # Send through provider
        response = await self.provider_session.send_multimodal_message(
            content=content,
            modality="image"
        )
        
        return response
    
    async def send_file_message(
        self,
        file_data: bytes,
        filename: str,
        file_type: str,
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message with file attachment"""
        # Process file
        processed_file = await self._process_file(file_data, filename, file_type)
        
        # Create message content
        content = {
            "type": "file",
            "file": processed_file,
            "filename": filename,
            "file_type": file_type
        }
        
        # Send through provider
        response = await self.provider_session.send_multimodal_message(
            content=content,
            modality="file"
        )
        
        return response
    
    async def _process_image(self, image_data: bytes, image_format: str) -> Dict[str, Any]:
        """Process image for provider"""
        # Implement image processing (resize, format conversion, etc.)
        return {
            "data": image_data,
            "format": image_format,
            "size": len(image_data)
        }
    
    async def _process_file(self, file_data: bytes, filename: str, file_type: str) -> Dict[str, Any]:
        """Process file for provider"""
        # Implement file processing (validation, conversion, etc.)
        return {
            "data": file_data,
            "filename": filename,
            "type": file_type,
            "size": len(file_data)
        }

class CollaborativeSession(BaseSession):
    """Session that supports multiple users"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.participants = set()
        self.participant_permissions = {}
    
    async def add_participant(
        self,
        user_id: str,
        permissions: List[str] = None
    ) -> None:
        """Add participant to collaborative session"""
        self.participants.add(user_id)
        self.participant_permissions[user_id] = permissions or ["read", "write"]
        
        # Notify other participants
        await self._notify_participants(
            f"User {user_id} joined the session",
            exclude=[user_id]
        )
    
    async def remove_participant(self, user_id: str) -> None:
        """Remove participant from session"""
        self.participants.discard(user_id)
        self.participant_permissions.pop(user_id, None)
        
        # Notify other participants
        await self._notify_participants(
            f"User {user_id} left the session",
            exclude=[user_id]
        )
    
    async def send_message_as_participant(
        self,
        user_id: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> SessionMessage:
        """Send message as specific participant"""
        # Check permissions
        if user_id not in self.participants:
            raise SessionError(f"User {user_id} is not a participant")
        
        if "write" not in self.participant_permissions.get(user_id, []):
            raise SessionError(f"User {user_id} does not have write permission")
        
        # Add participant info to metadata
        participant_metadata = {
            "participant_id": user_id,
            "collaborative_session": True,
            "participant_count": len(self.participants)
        }
        
        if metadata:
            metadata.update(participant_metadata)
        else:
            metadata = participant_metadata
        
        # Send message
        response = await self.send_message(content, metadata=metadata)
        
        # Notify other participants
        await self._notify_participants(
            f"New message from {user_id}",
            exclude=[user_id]
        )
        
        return response
    
    async def _notify_participants(
        self,
        notification: str,
        exclude: List[str] = None
    ):
        """Notify participants of session events"""
        exclude = exclude or []
        
        for participant in self.participants:
            if participant not in exclude:
                # Send notification (implement based on your notification system)
                await self._send_participant_notification(participant, notification)
    
    async def _send_participant_notification(self, user_id: str, message: str):
        """Send notification to specific participant"""
        # Implement notification delivery
        pass

class TemplatedSession(BaseSession):
    """Session with predefined templates and workflows"""
    
    def __init__(self, template_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_name = template_name
        self.template_config = self._load_template(template_name)
        self.workflow_state = {}
    
    def _load_template(self, template_name: str) -> Dict[str, Any]:
        """Load session template configuration"""
        templates = {
            "customer_support": {
                "system_prompt": "You are a helpful customer support agent.",
                "workflow_steps": ["greeting", "issue_identification", "solution", "follow_up"],
                "suggested_responses": ["How can I help you?", "Let me look into that.", "Is there anything else?"]
            },
            "code_review": {
                "system_prompt": "You are an expert code reviewer.",
                "workflow_steps": ["code_analysis", "feedback", "suggestions", "approval"],
                "code_standards": ["PEP8", "security", "performance", "maintainability"]
            },
            "interview": {
                "system_prompt": "You are conducting a technical interview.",
                "workflow_steps": ["introduction", "technical_questions", "coding_challenge", "wrap_up"],
                "difficulty_levels": ["junior", "mid", "senior"]
            }
        }
        
        return templates.get(template_name, {})
    
    async def start_workflow(self) -> Dict[str, Any]:
        """Start the template workflow"""
        if not self.template_config:
            raise SessionError(f"Template {self.template_name} not found")
        
        # Initialize workflow state
        self.workflow_state = {
            "current_step": 0,
            "steps": self.template_config.get("workflow_steps", []),
            "completed_steps": [],
            "started_at": datetime.now()
        }
        
        # Send initial system message
        if "system_prompt" in self.template_config:
            await self.send_system_message(self.template_config["system_prompt"])
        
        # Start first step
        if self.workflow_state["steps"]:
            return await self._execute_workflow_step(0)
        
        return {"status": "workflow_started", "template": self.template_name}
    
    async def next_workflow_step(self) -> Dict[str, Any]:
        """Proceed to next workflow step"""
        current_step = self.workflow_state.get("current_step", 0)
        steps = self.workflow_state.get("steps", [])
        
        if current_step < len(steps) - 1:
            next_step = current_step + 1
            return await self._execute_workflow_step(next_step)
        else:
            return await self._complete_workflow()
    
    async def _execute_workflow_step(self, step_index: int) -> Dict[str, Any]:
        """Execute specific workflow step"""
        steps = self.workflow_state["steps"]
        step_name = steps[step_index]
        
        # Update workflow state
        self.workflow_state["current_step"] = step_index
        
        # Execute step-specific logic
        if step_name == "greeting":
            await self.send_message("Hello! How can I assist you today?")
        elif step_name == "issue_identification":
            await self.send_message("Could you please describe the issue you're experiencing?")
        # Add more step implementations as needed
        
        return {
            "status": "step_executed",
            "step": step_name,
            "step_index": step_index,
            "total_steps": len(steps)
        }
    
    async def _complete_workflow(self) -> Dict[str, Any]:
        """Complete the workflow"""
        self.workflow_state["completed_at"] = datetime.now()
        self.workflow_state["completed_steps"] = self.workflow_state["steps"].copy()
        
        return {
            "status": "workflow_completed",
            "template": self.template_name,
            "duration": (
                self.workflow_state["completed_at"] - 
                self.workflow_state["started_at"]
            ).total_seconds()
        }
```

---

## 📚 Extension Best Practices

### **Storage Backend Guidelines**
- **Interface Compliance**: Always implement the complete ISessionStorage interface
- **Async Operations**: Use async/await for all operations to avoid blocking
- **Error Handling**: Provide clear error messages and handle connection failures
- **Performance**: Implement proper indexing and connection pooling
- **Health Checks**: Provide meaningful health check information

### **Provider Integration Guidelines**
- **Native Capabilities**: Leverage provider-specific features when available
- **Unified Interface**: Maintain consistency with the IProviderSession interface
- **Error Recovery**: Handle provider API errors gracefully
- **Rate Limiting**: Respect provider rate limits and implement backoff
- **Security**: Secure API key handling and data transmission

### **Middleware Development Guidelines**
- **Single Purpose**: Each middleware should have a clear, single purpose
- **Non-Destructive**: Avoid irreversibly modifying message content
- **Error Handling**: Handle errors gracefully without breaking the chain
- **Performance**: Keep processing fast to avoid session delays
- **Configurable**: Make middleware configurable for different use cases

### **Lifecycle Hook Guidelines**
- **Lightweight**: Keep hook processing fast and lightweight
- **Error Isolation**: Don't let hook errors affect session functionality
- **Async Operations**: Use async operations for external calls
- **Resource Cleanup**: Clean up resources in hook handlers
- **Monitoring**: Provide monitoring and alerting capabilities

---

**LangSwarm V2's session management system provides comprehensive extension capabilities, allowing developers to customize every aspect of session behavior while maintaining compatibility with the core system and native provider features.**
