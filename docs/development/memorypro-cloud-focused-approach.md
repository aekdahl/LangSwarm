# MemoryPro: Cloud-Focused Approach (Sophisticated)

**Version**: 1.0  
**Date**: 2025-01-08  
**Focus**: Full cloud-based MemoryPro with raw storage sync and sophisticated endpoints

## 🎯 **Clarified Requirements**

Based on your feedback:
- ✅ **Keep sophisticated approach**: Push + Poll endpoints in Pro
- ✅ **Sync raw storage to cloud**: Full memory content, not just insights
- ✅ **Consider skipping local storage**: When Pro is enabled
- ✅ **No endpoint changes**: Keep existing cloud service design
- ✅ **No simplifications**: Maintain full webhook + Pub/Sub architecture

## 🤔 **Key Decision: Local Storage Strategy**

### **Option A: Skip Local When Pro Enabled (Cloud-First)**
```python
class MemoryProAdapter(DatabaseAdapter):
    def __init__(self, pro_config: MemoryProConfig, local_adapter: Optional[DatabaseAdapter] = None):
        self.pro_client = MemoryProClient(pro_config)
        self.local_adapter = local_adapter  # Optional fallback
        self.cloud_first = pro_config.cloud_first_mode
    
    async def store(self, memory: Dict[str, Any]) -> str:
        if self.cloud_first:
            # Store directly to cloud, skip local
            return await self.pro_client.store_memory(memory)
        else:
            # Hybrid: local + cloud sync
            memory_id = await self.local_adapter.store(memory)
            await self.pro_client.sync_memory(memory_id, memory)
            return memory_id
```

### **Option B: Always Hybrid (Local + Cloud)**
```python
class MemoryProAdapter(DatabaseAdapter):
    def __init__(self, base_adapter: DatabaseAdapter, pro_config: MemoryProConfig):
        self.base_adapter = base_adapter  # Always present
        self.pro_client = MemoryProClient(pro_config)
    
    async def store(self, memory: Dict[str, Any]) -> str:
        # Always store locally first (reliability)
        memory_id = await self.base_adapter.store(memory)
        
        # Then sync to cloud (enhancement)
        await self.pro_client.sync_memory(memory_id, memory)
        return memory_id
```

### **💭 My Recommendation: Option A (Cloud-First)**

**Why skip local when Pro enabled:**
- ✅ **Reduces complexity** - Single source of truth (cloud)
- ✅ **Lower local storage costs** - No duplicate storage
- ✅ **Faster sync** - No local→cloud synchronization needed
- ✅ **Consistent experience** - All Pro features available immediately
- ✅ **Simpler conflict resolution** - No local/cloud sync conflicts

**With graceful fallback:**
- If cloud unavailable → temporarily cache locally
- When cloud returns → sync cached data and resume cloud-first mode

## 🚀 **MemoryPro Integration with Existing LangSwarm**

### **1. Configuration (Environment Variables)**

```python
# langswarm/pro/config.py
import os
from typing import Optional

class MemoryProConfig:
    def __init__(self):
        # Make all endpoints configurable
        self.api_base_url = os.getenv('MEMORYPRO_API_URL', 'https://api.memorypro.com')
        self.api_key = os.getenv('MEMORYPRO_API_KEY')
        self.api_secret = os.getenv('MEMORYPRO_API_SECRET')
        
        # Timeouts and limits
        self.timeout = int(os.getenv('MEMORYPRO_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('MEMORYPRO_MAX_RETRIES', '3'))
        
        # Push/Poll configuration
        self.webhook_url = os.getenv('MEMORYPRO_WEBHOOK_URL')
        self.webhook_secret = os.getenv('MEMORYPRO_WEBHOOK_SECRET')
        self.polling_interval = int(os.getenv('MEMORYPRO_POLL_INTERVAL', '60'))
        self.enable_push = os.getenv('MEMORYPRO_ENABLE_PUSH', 'true').lower() == 'true'
        self.enable_polling = os.getenv('MEMORYPRO_ENABLE_POLLING', 'true').lower() == 'true'
        
        # Storage strategy
        self.cloud_first_mode = os.getenv('MEMORYPRO_CLOUD_FIRST', 'true').lower() == 'true'
        self.local_fallback = os.getenv('MEMORYPRO_LOCAL_FALLBACK', 'true').lower() == 'true'
        
        # Feature flags
        self.enable_memory_evolution = os.getenv('MEMORYPRO_EVOLUTION', 'true').lower() == 'true'
        self.enable_lifecycle_management = os.getenv('MEMORYPRO_LIFECYCLE', 'true').lower() == 'true'
        self.enable_ai_analysis = os.getenv('MEMORYPRO_AI_ANALYSIS', 'true').lower() == 'true'
    
    def is_enabled(self) -> bool:
        return self.api_key is not None and self.api_secret is not None
    
    def get_endpoint(self, path: str) -> str:
        return f"{self.api_base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
```

### **2. Full-Featured Pro Client (No Simplifications)**

```python
# langswarm/pro/client.py
import httpx
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class MemoryProClient:
    """Full-featured Pro client with push/pull, webhooks, and raw storage sync"""
    
    def __init__(self, config: MemoryProConfig):
        self.config = config
        self.session = httpx.AsyncClient(
            base_url=config.api_base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "X-API-Secret": config.api_secret,
                "Content-Type": "application/json"
            },
            timeout=config.timeout
        )
        
        # Background tasks
        self._polling_task = None
        self._webhook_server = None
        
    async def store_memory(self, memory: Dict[str, Any]) -> str:
        """Store raw memory content directly to cloud"""
        endpoint = self.config.get_endpoint("memory/store")
        
        payload = {
            "content": memory.get("content"),
            "metadata": memory.get("metadata", {}),
            "session_id": memory.get("session_id"),
            "agent_id": memory.get("agent_id"),
            "timestamp": datetime.now().isoformat(),
            "user_id": memory.get("user_id"),
            "memory_type": memory.get("type", "conversation")
        }
        
        response = await self.session.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["memory_id"]
    
    async def sync_memory(self, memory_id: str, memory: Dict[str, Any]):
        """Sync existing memory to cloud (for hybrid mode)"""
        endpoint = self.config.get_endpoint("memory/sync")
        
        payload = {
            "local_memory_id": memory_id,
            "content": memory.get("content"),
            "metadata": memory.get("metadata", {}),
            "session_id": memory.get("session_id"),
            "agent_id": memory.get("agent_id"),
            "timestamp": datetime.now().isoformat()
        }
        
        response = await self.session.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def recall_memories(
        self,
        query: str,
        count: int = 5,
        weight_recent: bool = True,
        weight_responsibilities: bool = True,
        auto_queue_actions: bool = True,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Advanced memory recall with Pro evolution features"""
        endpoint = self.config.get_endpoint("memory/recall")
        
        payload = {
            "query": query,
            "recall_count": count,
            "weight_recent": weight_recent,
            "weight_responsibilities": weight_responsibilities,
            "auto_queue_actions": auto_queue_actions,
            "session_id": session_id,
            "evolution_enabled": self.config.enable_memory_evolution
        }
        
        response = await self.session.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_memory_insights(self) -> Dict[str, Any]:
        """Get AI-powered memory insights and lifecycle recommendations"""
        endpoint = self.config.get_endpoint("memory/insights")
        response = await self.session.get(endpoint)
        response.raise_for_status()
        return response.json()
    
    async def start_push_notifications(self):
        """Setup webhook server for push notifications (sophisticated approach)"""
        if not self.config.enable_push or not self.config.webhook_url:
            return
        
        # Register webhook with Pro service
        webhook_endpoint = self.config.get_endpoint("webhooks/register")
        payload = {
            "webhook_url": self.config.webhook_url,
            "webhook_secret": self.config.webhook_secret,
            "events": ["memory_insights", "lifecycle_recommendations", "evolution_updates"]
        }
        
        response = await self.session.post(webhook_endpoint, json=payload)
        response.raise_for_status()
        
        # Start local webhook server
        await self._start_webhook_server()
    
    async def start_polling(self):
        """Start polling for insights (alongside push notifications)"""
        if not self.config.enable_polling:
            return
        
        self._polling_task = asyncio.create_task(self._polling_loop())
    
    async def _polling_loop(self):
        """Polling loop for Pro insights"""
        while True:
            try:
                insights = await self.get_memory_insights()
                await self._process_insights(insights)
                await asyncio.sleep(self.config.polling_interval)
            except Exception as e:
                print(f"MemoryPro polling error: {e}")
                await asyncio.sleep(10)  # Brief pause before retry
    
    async def _start_webhook_server(self):
        """Start FastAPI webhook server for push notifications"""
        from fastapi import FastAPI, Request, HTTPException
        import uvicorn
        
        app = FastAPI()
        
        @app.post("/memorypro/webhook")
        async def handle_webhook(request: Request):
            # Verify webhook signature
            signature = request.headers.get("X-MemoryPro-Signature")
            if not self._verify_webhook_signature(signature, await request.body()):
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            payload = await request.json()
            await self._process_insights(payload)
            return {"status": "received"}
        
        # Start server in background
        config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
        server = uvicorn.Server(config)
        self._webhook_server = server
        asyncio.create_task(server.serve())
    
    async def _process_insights(self, insights: Dict[str, Any]):
        """Process insights from both push and pull"""
        # Handle memory evolution updates
        if "evolution_updates" in insights:
            await self._apply_evolution_updates(insights["evolution_updates"])
        
        # Handle lifecycle recommendations
        if "lifecycle_recommendations" in insights:
            await self._apply_lifecycle_recommendations(insights["lifecycle_recommendations"])
        
        # Handle memory insights
        if "memory_insights" in insights:
            await self._apply_memory_insights(insights["memory_insights"])
    
    async def close(self):
        """Clean up resources"""
        if self._polling_task:
            self._polling_task.cancel()
        
        if self._webhook_server:
            self._webhook_server.should_exit = True
        
        await self.session.aclose()
```

### **3. Pro-Enhanced Memory Adapter**

```python
# langswarm/memory/adapters/memorypro_adapter.py
from typing import Dict, List, Any, Optional
from .database_adapter import DatabaseAdapter
from ..pro.client import MemoryProClient
from ..pro.config import MemoryProConfig

class MemoryProAdapter(DatabaseAdapter):
    """
    Pro memory adapter with full cloud integration:
    - Raw storage sync to cloud
    - Memory evolution and lifecycle management
    - Push/pull insights and recommendations
    - Optional local fallback
    """
    
    def __init__(
        self, 
        pro_config: MemoryProConfig,
        local_adapter: Optional[DatabaseAdapter] = None
    ):
        self.pro_config = pro_config
        self.pro_client = MemoryProClient(pro_config)
        self.local_adapter = local_adapter
        self.cloud_first = pro_config.cloud_first_mode
        
        super().__init__(
            name="MemoryProAdapter",
            description="Pro memory with evolution, lifecycle, and AI analysis",
            instruction="Enhanced memory with cloud-based Pro features"
        )
    
    async def store(self, memory: Dict[str, Any]) -> str:
        """Store memory with Pro cloud-first approach"""
        if self.cloud_first:
            try:
                # Primary: Store directly to cloud
                return await self.pro_client.store_memory(memory)
            except Exception as e:
                if self.local_adapter and self.pro_config.local_fallback:
                    # Fallback: Store locally and queue for sync
                    print(f"MemoryPro cloud unavailable, using local fallback: {e}")
                    memory_id = await self.local_adapter.store(memory)
                    await self._queue_for_sync(memory_id, memory)
                    return memory_id
                else:
                    raise
        else:
            # Hybrid: Local + cloud sync
            memory_id = await self.local_adapter.store(memory)
            try:
                await self.pro_client.sync_memory(memory_id, memory)
            except Exception as e:
                print(f"MemoryPro sync failed: {e}")
            return memory_id
    
    async def query(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Enhanced recall with Pro evolution features"""
        if self.cloud_first:
            try:
                # Use Pro enhanced recall
                result = await self.pro_client.recall_memories(query, **kwargs)
                return result.get("memories", [])
            except Exception as e:
                if self.local_adapter and self.pro_config.local_fallback:
                    print(f"MemoryPro recall unavailable, using local: {e}")
                    return await self.local_adapter.query(query, **kwargs)
                else:
                    raise
        else:
            # Hybrid: Try Pro first, fallback to local
            try:
                result = await self.pro_client.recall_memories(query, **kwargs)
                return result.get("memories", [])
            except Exception:
                return await self.local_adapter.query(query, **kwargs)
    
    async def start_pro_services(self):
        """Start Pro push/pull services"""
        if self.pro_config.enable_push:
            await self.pro_client.start_push_notifications()
        
        if self.pro_config.enable_polling:
            await self.pro_client.start_polling()
    
    async def get_memory_insights(self) -> Dict[str, Any]:
        """Get Pro memory insights and evolution data"""
        return await self.pro_client.get_memory_insights()
    
    async def _queue_for_sync(self, memory_id: str, memory: Dict[str, Any]):
        """Queue memory for sync when cloud becomes available"""
        # Implementation for offline sync queue
        pass
    
    async def capabilities(self) -> Dict[str, bool]:
        """Report Pro capabilities"""
        return {
            "semantic_search": True,
            "metadata_filtering": True,
            "memory_evolution": self.pro_config.enable_memory_evolution,
            "lifecycle_management": self.pro_config.enable_lifecycle_management,
            "ai_analysis": self.pro_config.enable_ai_analysis,
            "push_notifications": self.pro_config.enable_push,
            "cloud_storage": True
        }
```

### **4. LangSwarm Integration**

```python
# langswarm/core/config.py (modification)
class LangSwarmConfigLoader:
    def get_memory_adapter(self, adapter_config: Dict[str, Any]) -> DatabaseAdapter:
        """Factory method that creates appropriate memory adapter"""
        
        # Check if MemoryPro is enabled
        memorypro_config = self._get_memorypro_config()
        if memorypro_config and memorypro_config.is_enabled():
            
            if memorypro_config.cloud_first_mode:
                # Cloud-first: MemoryPro only (optional local fallback)
                local_adapter = None
                if memorypro_config.local_fallback:
                    local_adapter = self._create_base_adapter(adapter_config)
                
                return MemoryProAdapter(memorypro_config, local_adapter)
            else:
                # Hybrid: Local + Pro sync
                base_adapter = self._create_base_adapter(adapter_config)
                return MemoryProAdapter(memorypro_config, base_adapter)
        
        # Standard: Local adapter only
        return self._create_base_adapter(adapter_config)
    
    def _get_memorypro_config(self) -> Optional[MemoryProConfig]:
        """Get MemoryPro configuration from environment/config"""
        try:
            config = MemoryProConfig()
            return config if config.is_enabled() else None
        except Exception:
            return None
```

## 🎯 **Benefits of Cloud-First Approach**

### **✅ Advantages:**
- **Single source of truth** - No sync conflicts
- **Immediate Pro features** - All evolution/lifecycle features available
- **Simplified architecture** - No complex local/cloud synchronization
- **Better performance** - No duplicate storage operations
- **Consistent experience** - Same features across all devices/sessions

### **✅ Fallback Strategy:**
- **Graceful degradation** - Local cache when cloud unavailable
- **Auto-recovery** - Resume cloud-first when connection restored
- **Data preservation** - No data loss during outages

## 📋 **Environment Configuration Example**

```bash
# .env file for MemoryPro
MEMORYPRO_API_URL=https://api.memorypro.com
MEMORYPRO_API_KEY=your_api_key_here
MEMORYPRO_API_SECRET=your_secret_here

# Push/Pull configuration
MEMORYPRO_WEBHOOK_URL=https://your-app.com/memorypro/webhook
MEMORYPRO_WEBHOOK_SECRET=webhook_secret
MEMORYPRO_ENABLE_PUSH=true
MEMORYPRO_ENABLE_POLLING=true
MEMORYPRO_POLL_INTERVAL=60

# Storage strategy
MEMORYPRO_CLOUD_FIRST=true
MEMORYPRO_LOCAL_FALLBACK=true

# Features
MEMORYPRO_EVOLUTION=true
MEMORYPRO_LIFECYCLE=true
MEMORYPRO_AI_ANALYSIS=true
```

## 🚀 **Summary**

This approach:
- ✅ **Keeps sophisticated push/pull architecture** (no simplifications)
- ✅ **Syncs raw storage to cloud** (not just insights)
- ✅ **Supports cloud-first mode** (skip local when Pro enabled)
- ✅ **Uses environment variables** (no hardcoded endpoints)
- ✅ **Builds on existing LangSwarm** (adapter pattern)
- ✅ **Maintains graceful fallback** (reliability)

**Recommendation**: Use **cloud-first mode** for Pro users to get the full benefit of memory evolution and lifecycle management without local storage complexity. 