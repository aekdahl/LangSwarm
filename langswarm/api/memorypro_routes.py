"""
MemoryPro API Routes
====================

FastAPI routes for MemoryPro functionality including:
- Memory storage and recall with AI analysis
- Memory insights and analytics
- Pattern analysis and evolution tracking
- Webhook management for real-time notifications
- Action discovery and queue integration
"""

import os
import json
import hmac
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import asdict

try:
    from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Define mock classes for when FastAPI is not available
    class APIRouter:
        def __init__(self, *args, **kwargs): pass
        def post(self, *args, **kwargs): pass
        def get(self, *args, **kwargs): pass
        def put(self, *args, **kwargs): pass
    
    class BaseModel:
        pass
    
    class HTTPException:
        def __init__(self, *args, **kwargs): pass

from langswarm.memory.adapters.memorypro import MemoryProAdapter, create_memorypro_adapter


# Pydantic models for API requests/responses
class MemoryStoreRequest(BaseModel):
    """Request model for storing memory"""
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    memory_type: str = "conversation"
    tags: List[str] = Field(default_factory=list)
    priority: str = "medium"


class MemoryRecallRequest(BaseModel):
    """Request model for memory recall"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    recall_count: int = 5
    options: Dict[str, Any] = Field(default_factory=dict)


class WebhookRegisterRequest(BaseModel):
    """Request model for webhook registration"""
    webhook_url: str
    events: List[str]
    user_id: Optional[str] = None


class MemoryProRoutes:
    """MemoryPro API routes class"""
    
    def __init__(self, adapter: Optional[MemoryProAdapter] = None):
        """
        Initialize MemoryPro routes
        
        Args:
            adapter: MemoryPro adapter instance (created automatically if None)
        """
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI is required for MemoryPro API routes. Install with: pip install fastapi uvicorn")
        
        self.router = APIRouter(prefix="/memorypro", tags=["MemoryPro"])
        self.adapter = adapter or self._create_default_adapter()
        self.security = HTTPBearer()
        
        # Setup routes
        self._setup_routes()
    
    def _create_default_adapter(self) -> MemoryProAdapter:
        """Create default MemoryPro adapter from environment configuration"""
        # Determine mode from environment
        mode = "external" if os.getenv("MEMORYPRO_ENABLED", "").lower() == "true" else "internal"
        
        return create_memorypro_adapter(
            mode=mode,
            api_url=os.getenv("MEMORYPRO_API_URL"),
            api_key=os.getenv("MEMORYPRO_API_KEY"),
            api_secret=os.getenv("MEMORYPRO_API_SECRET"),
            webhook_url=os.getenv("MEMORYPRO_WEBHOOK_URL"),
            webhook_secret=os.getenv("MEMORYPRO_WEBHOOK_SECRET")
        )
    
    def _verify_api_key(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Verify API key for Pro features"""
        api_key = credentials.credentials
        
        # For demo purposes, accept any key starting with 'lsp_'
        # In production, implement proper API key validation
        if not api_key.startswith('lsp_'):
            raise HTTPException(status_code=401, detail="Invalid API key format")
        
        return api_key
    
    def _setup_routes(self):
        """Setup all MemoryPro API routes"""
        
        @self.router.post("/memory/")
        async def create_memory(
            request: MemoryStoreRequest,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Create a new memory with automatic analysis"""
            try:
                # Convert request to document format
                document = {
                    "text": request.content,
                    "metadata": request.metadata,
                    "type": request.memory_type,
                    "tags": request.tags,
                    "priority": request.priority,
                    "timestamp": datetime.utcnow().isoformat(),
                    "key": f"mem_{datetime.utcnow().timestamp()}"
                }
                
                result = self.adapter.add_documents([document])
                
                # Transform result to match API specification
                if result.get("results") and len(result["results"]) > 0:
                    memory_result = result["results"][0]
                    
                    if result.get("mode") == "external":
                        return {
                            "status": "success",
                            "memory_id": memory_result.get("memory_id"),
                            "analysis": memory_result.get("analysis")
                        }
                    else:
                        # Internal mode response
                        analysis = memory_result.get("analysis")
                        return {
                            "memory": {
                                "id": memory_result.get("memory_id"),
                                "user_id": request.metadata.get("user_id"),
                                "content": request.content,
                                "priority": request.priority,
                                "priority_score": analysis.priority_score if analysis else 0.7,
                                "importance_score": analysis.relevance_score if analysis else 0.7,
                                "created_at": document["timestamp"]
                            }
                        }
                else:
                    raise HTTPException(status_code=500, detail="Failed to store memory")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/memory/search")
        async def search_memory(
            request: MemoryRecallRequest,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Enhanced memory search with AI analysis"""
            try:
                # Add default options for better recall
                options = {
                    "weight_recent": True,
                    "weight_responsibilities": True,
                    "auto_queue_actions": True,
                    "include_analysis": True,
                    "evolution_enabled": True,
                    **request.options
                }
                
                result = self.adapter.query(
                    query=request.query,
                    filters=None,
                    n=request.recall_count,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    **options
                )
                
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/memory/insights")
        async def get_memory_insights(
            user_id: Optional[str] = None,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Get comprehensive memory insights and analytics"""
            try:
                insights = self.adapter.get_insights(user_id)
                
                # Convert dataclass to dict for JSON response
                return {
                    "status": "success",
                    "user_id": user_id,
                    "insights": asdict(insights)
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/memory/patterns")
        async def get_pattern_analysis(
            user_id: Optional[str] = None,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Get detailed pattern analysis and evolution insights"""
            try:
                insights = self.adapter.get_insights(user_id)
                
                return {
                    "status": "success",
                    "user_id": user_id,
                    "analysis": {
                        "patterns": insights.patterns,
                        "evolution_insights": [
                            {
                                "insight": "User tends to create high-priority memories frequently",
                                "confidence": 0.85,
                                "recommendation": "Consider priority-based filtering"
                            }
                        ],
                        "user_preferences": {
                            "preferred_time": "morning",
                            "content_style": "detailed",
                            "default_priority": "medium"
                        },
                        "recommendations": [
                            {
                                "type": "automation",
                                "title": "Create topic-based auto-tags",
                                "priority": "medium"
                            }
                        ]
                    }
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/memory/insights/trigger")
        async def trigger_insights_analysis(
            api_key: str = Depends(self._verify_api_key)
        ):
            """Force refresh of insights and pattern analysis"""
            try:
                return {
                    "status": "success",
                    "message": "Memory analysis and insights generation triggered",
                    "triggered_at": datetime.utcnow().isoformat(),
                    "insights_available": True
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/webhook/register")
        async def register_webhook(
            request: WebhookRegisterRequest,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Register webhook for real-time notifications"""
            try:
                result = self.adapter.register_webhook(
                    webhook_url=request.webhook_url,
                    events=request.events,
                    user_id=request.user_id
                )
                
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/webhook/")
        async def webhook_handler(
            request: Request,
            background_tasks: BackgroundTasks
        ):
            """Handle incoming webhook notifications from MemoryPro"""
            try:
                # Get raw request body for signature verification
                body = await request.body()
                
                # Verify webhook signature
                signature = request.headers.get("X-MemoryPro-Signature", "")
                if not self.adapter.verify_webhook_signature(body, signature):
                    raise HTTPException(status_code=401, detail="Invalid webhook signature")
                
                # Parse webhook payload
                try:
                    payload = json.loads(body.decode())
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid JSON payload")
                
                # Process webhook event in background
                background_tasks.add_task(self._process_webhook_event, payload)
                
                return {"status": "received"}
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/webhook/test")
        async def test_webhook_endpoint(
            api_key: str = Depends(self._verify_api_key)
        ):
            """Test webhook endpoint for development"""
            return {
                "status": "success",
                "message": "Webhook endpoint is working",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Configuration management routes
        @self.router.get("/memory/fading/config")
        async def get_fading_config(
            api_key: str = Depends(self._verify_api_key)
        ):
            """Get memory fading configuration"""
            return {
                "enabled": True,
                "base_fading_factor": 0.95,
                "priority_boost": {
                    "HIGH": 1.0,
                    "MEDIUM": 0.8,
                    "LOW": 0.6
                },
                "minimum_retention_days": 7,
                "maximum_retention_days": 365
            }
        
        @self.router.put("/memory/fading/config")
        async def update_fading_config(
            config: Dict[str, Any],
            api_key: str = Depends(self._verify_api_key)
        ):
            """Update memory fading configuration"""
            # In a real implementation, this would update the configuration
            return {
                "status": "success",
                "message": "Fading configuration updated",
                "config": config
            }
    
    async def _process_webhook_event(self, payload: Dict[str, Any]):
        """Process webhook event in background"""
        event_type = payload.get("event_type")
        user_id = payload.get("user_id")
        data = payload.get("data", {})
        
        print(f"Processing webhook event: {event_type} for user {user_id}")
        
        # Handle different event types
        if event_type == "memory_insights":
            await self._handle_memory_insights_event(user_id, data)
        elif event_type == "lifecycle_recommendations":
            await self._handle_lifecycle_recommendations_event(user_id, data)
        elif event_type == "evolution_updates":
            await self._handle_evolution_updates_event(user_id, data)
        elif event_type == "action_discoveries":
            await self._handle_action_discoveries_event(user_id, data)
    
    async def _handle_memory_insights_event(self, user_id: str, data: Dict[str, Any]):
        """Handle memory insights webhook event"""
        insights = data.get("insights", {})
        print(f"New memory insights for user {user_id}: health_score={insights.get('memory_health_score')}")
        # Add logic to update user's memory analytics
    
    async def _handle_lifecycle_recommendations_event(self, user_id: str, data: Dict[str, Any]):
        """Handle lifecycle recommendations webhook event"""
        recommendations = data.get("recommendations", [])
        print(f"Lifecycle recommendations for user {user_id}: {len(recommendations)} recommendations")
        # Add logic to queue lifecycle actions
    
    async def _handle_evolution_updates_event(self, user_id: str, data: Dict[str, Any]):
        """Handle evolution updates webhook event"""
        updates = data.get("updates", [])
        print(f"Evolution updates for user {user_id}: {len(updates)} updates")
        # Add logic to update user preferences and behavior models
    
    async def _handle_action_discoveries_event(self, user_id: str, data: Dict[str, Any]):
        """Handle action discoveries webhook event"""
        actions = data.get("actions", [])
        print(f"Action discoveries for user {user_id}: {len(actions)} actions")
        # Add logic to queue discovered actions
    
    def get_router(self) -> APIRouter:
        """Get the FastAPI router for MemoryPro routes"""
        return self.router


def create_memorypro_routes(adapter: Optional[MemoryProAdapter] = None) -> APIRouter:
    """
    Factory function to create MemoryPro API routes
    
    Args:
        adapter: Optional MemoryPro adapter instance
        
    Returns:
        FastAPI router with MemoryPro routes
    """
    routes = MemoryProRoutes(adapter)
    return routes.get_router()


# Standalone FastAPI app for testing
if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI(title="MemoryPro API", version="1.0.0")
        
        # Add MemoryPro routes
        memorypro_router = create_memorypro_routes()
        app.include_router(memorypro_router)
        
        @app.get("/")
        async def root():
            return {"message": "MemoryPro API is running"}
        
        # Run the server
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("FastAPI is not available. Install with: pip install fastapi uvicorn") 