"""
AAF Backend - Main FastAPI Application
LangSwarm-powered chatbot backend for company websites
"""
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

# Add the parent directory to the path so we can import langswarm
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.config import get_settings
from app.core.langswarm_manager import langswarm_manager
from app.api import chat, websocket, management, config_editor, demo, tenant_ui, chat_v2, uploads, tools, multi_tools, knowledge
from app.api.models import HealthResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AAF Backend...")
    settings = get_settings()
    
    try:
        # Initialize LangSwarm manager
        await langswarm_manager.initialize()
        logger.info("LangSwarm manager initialized successfully")
        
        # Initialize custom tools (multi-tool manager)
        from app.core.multi_tool_manager import get_multi_tool_manager
        await get_multi_tool_manager()
        logger.info("Multi-tool manager initialized successfully")
        
        # Initialize persistent configuration manager
        from app.core.persistent_config import get_persistent_config_manager
        persistent_config = get_persistent_config_manager()
        logger.info(f"Persistent config manager initialized for instance {persistent_config.instance_id}")
        
        # Log configuration info
        agents = langswarm_manager.list_agents()
        logger.info(f"Loaded {len(agents)} agents")
        for agent in agents:
            logger.info(f"  - {agent['id']}: {agent['model']} ({agent['behavior']})")
        
        logger.info(f"AAF Backend started on {settings.app_host}:{settings.port}")
        
    except Exception as e:
        logger.error(f"Failed to initialize AAF Backend: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AAF Backend...")
    
    # Close custom tools
    try:
        from app.core.multi_tool_manager import close_multi_tool_manager
        await close_multi_tool_manager()
        logger.info("Multi-tool manager closed successfully")
    except Exception as e:
        logger.error(f"Error closing multi-tool manager: {e}")
    
    logger.info("AAF Backend shutdown complete")


# Create FastAPI application
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="AAF Backend",
        description="LangSwarm-powered chatbot backend for company websites",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Include routers
    app.include_router(chat.router, prefix="/api")
    app.include_router(websocket.router, prefix="/api")
    app.include_router(demo.router, prefix="/api")
    
    # New widget/SPA APIs
    app.include_router(tenant_ui.router, prefix="/api")
    app.include_router(chat_v2.router, prefix="/api")
    app.include_router(uploads.router, prefix="/api")
    app.include_router(tools.router, prefix="/api")
    app.include_router(multi_tools.router, prefix="/api")
    app.include_router(knowledge.router)
    
    # Include management API if enabled
    if settings.management_api_enabled:
        app.include_router(management.router, prefix="/api")
        app.include_router(config_editor.router, prefix="/api")
        logger.info("Management API and Config Editor enabled")
    
    # Clean demo URL route (MUST be after all other routes)
    from app.core.demo_manager import get_demo_manager
    from datetime import datetime
    
    @app.get("/demo/{demo_id}", response_class=HTMLResponse)
    async def clean_demo_url(demo_id: str, demo_manager = Depends(get_demo_manager)):
        """Clean demo URL for client sharing - redirects to API endpoint logic"""
        try:
            # Get demo metadata
            metadata = await demo_manager.get_demo(demo_id)
            if not metadata:
                raise HTTPException(status_code=404, detail="Demo not found")
            
            # Check if demo is active and not expired
            if metadata.status != "active":
                raise HTTPException(status_code=410, detail="Demo is no longer available")
            
            # Check expiration only if expires_at is set
            if metadata.expires_at:
                if metadata.expires_at < datetime.utcnow():
                    raise HTTPException(status_code=410, detail="Demo has expired")
            
            # Get HTML content
            html_content = await demo_manager.get_demo_html(demo_id)
            if not html_content:
                raise HTTPException(status_code=404, detail="Demo content not found")
            
            # Increment view count
            await demo_manager.increment_view_count(demo_id)
            
            return HTMLResponse(content=html_content)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to view demo {demo_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load demo: {str(e)}"
            )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "AAF Backend",
            "description": "LangSwarm-powered chatbot backend",
            "version": "1.0.0",
            "status": "running"
        }
    
    # Health check endpoint
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint"""
        try:
            # Check LangSwarm manager status
            agents = langswarm_manager.list_agents()
            langswarm_status = "ready" if agents else "no_agents"
            
            return HealthResponse(
                status="healthy",
                version="1.0.0",
                langswarm_status=langswarm_status,
                agents_count=len(agents)
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthResponse(
                status="unhealthy",
                version="1.0.0",
                langswarm_status="error",
                agents_count=0
            )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler"""
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal server error",
                detail=str(exc) if settings.log_level == "DEBUG" else None
            ).dict()
        )
    
    return app


# Create the app instance
app = create_app()


# Development server
if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.port,
        reload=settings.app_reload,
        log_level=settings.log_level.lower()
    )
