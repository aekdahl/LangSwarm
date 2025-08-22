"""
Management API endpoints for AAF Backend
Configuration management, agent control, and system administration
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import signal
import sys

from ..core.langswarm_manager import get_langswarm_manager, LangSwarmManager
from ..core.config import get_settings
from .models import (
    AgentConfigRequest, ConfigurationResponse, ConfigurationUpdateRequest,
    RestartRequest, RestartResponse, ToolConfigRequest, PromptTemplate,
    ModelConfigRequest, AgentInfo, ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/management", tags=["management"])
security = HTTPBearer()


def verify_management_api_key(authorization: HTTPAuthorizationCredentials = Depends(security)):
    """Verify management API key"""
    settings = get_settings()
    
    if not settings.management_api_enabled:
        raise HTTPException(status_code=403, detail="Management API is disabled")
    
    if authorization.credentials != settings.management_api_secret:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return authorization.credentials


@router.get("/config", response_model=ConfigurationResponse)
async def get_configuration(
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Get current LangSwarm configuration"""
    try:
        config = manager.get_current_config()
        agents = manager.list_agents()
        
        return ConfigurationResponse(
            config=config,
            agents=[AgentInfo(**agent) for agent in agents]
        )
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_configuration(
    request: ConfigurationUpdateRequest,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Update LangSwarm configuration"""
    try:
        await manager.update_configuration(request.config)
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "agents_count": len(manager.agents)
        }
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents")
async def create_agent(
    request: AgentConfigRequest,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Create or update an agent configuration"""
    try:
        agent_config = request.dict(exclude_unset=True)
        await manager.update_agent_config(request.id, agent_config)
        
        return {
            "success": True,
            "message": f"Agent '{request.id}' created/updated successfully",
            "agent_id": request.id
        }
    except Exception as e:
        logger.error(f"Failed to create/update agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents")
async def list_agents(
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """List all configured agents"""
    try:
        agents = manager.list_agents()
        return {
            "agents": agents,
            "count": len(agents),
            "default_agent": manager.default_agent_id
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent_config(
    agent_id: str,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Get detailed configuration for a specific agent"""
    try:
        agent = manager.get_agent(agent_id)
        
        # Get agent configuration from the loaded config
        config = manager.get_current_config()
        agent_configs = config.get('agents', [])
        agent_config = None
        
        for ac in agent_configs:
            if ac.get('id') == agent_id:
                agent_config = ac
                break
        
        if not agent_config:
            raise HTTPException(status_code=404, detail=f"Agent configuration not found: {agent_id}")
        
        return {
            "agent_id": agent_id,
            "config": agent_config,
            "status": {
                "initialized": True,
                "has_memory": agent.has_memory(),
                "has_tools": agent.has_tools()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get agent config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}")
async def update_agent_config(
    agent_id: str,
    request: AgentConfigRequest,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Update an existing agent configuration"""
    try:
        # Ensure the agent_id matches
        if request.id != agent_id:
            raise HTTPException(status_code=400, detail="Agent ID mismatch")
        
        agent_config = request.dict(exclude_unset=True)
        await manager.update_agent_config(agent_id, agent_config)
        
        return {
            "success": True,
            "message": f"Agent '{agent_id}' updated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to update agent config: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Delete an agent configuration"""
    try:
        await manager.delete_agent(agent_id)
        
        return {
            "success": True,
            "message": f"Agent '{agent_id}' deleted successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart", response_model=RestartResponse)
async def restart_application(
    request: RestartRequest = RestartRequest(),
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Restart the application with new configuration"""
    try:
        logger.info("Application restart requested via management API")
        
        # Backup current configuration if requested
        if request.backup_config:
            # This could be enhanced to actually backup the config
            logger.info("Configuration backup requested (not implemented)")
        
        # Get agent count before restart
        agents_count = len(manager.agents)
        
        # Restart LangSwarm manager
        await manager.restart()
        
        # For Cloud Run, we can send a signal to restart the container
        # This is handled gracefully by the container runtime
        response = RestartResponse(
            success=True,
            message="Application restarted successfully",
            agents_reinitialized=len(manager.agents)
        )
        
        # Send response before restarting (for Cloud Run)
        if os.getenv("K_SERVICE"):  # Running in Cloud Run
            logger.info("Triggering Cloud Run container restart")
            # Schedule a delayed restart to allow response to be sent
            import asyncio
            asyncio.create_task(delayed_restart())
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to restart application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def delayed_restart():
    """Delayed restart for Cloud Run environments"""
    import asyncio
    await asyncio.sleep(1)  # Allow response to be sent
    logger.info("Performing delayed restart")
    os.kill(os.getpid(), signal.SIGTERM)


@router.get("/health")
async def health_check(
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Management API health check"""
    try:
        agents = manager.list_agents()
        
        return {
            "status": "healthy",
            "langswarm_status": "ready",
            "agents_count": len(agents),
            "management_api": "enabled"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "management_api": "enabled"
        }


@router.post("/tools")
async def add_tool_config(
    request: ToolConfigRequest,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Add or update a tool configuration"""
    try:
        # Get current configuration
        config = manager.get_current_config()
        
        # Add or update tool
        tools = config.get('tools', [])
        
        # Check if tool exists
        tool_exists = False
        for i, tool in enumerate(tools):
            if tool.get('id') == request.name:
                tools[i] = {
                    'id': request.name,
                    'type': request.type,
                    'enabled': request.enabled,
                    **request.config
                }
                tool_exists = True
                break
        
        if not tool_exists:
            tools.append({
                'id': request.name,
                'type': request.type,
                'enabled': request.enabled,
                **request.config
            })
        
        config['tools'] = tools
        
        # Update configuration
        await manager.update_configuration(config)
        
        return {
            "success": True,
            "message": f"Tool '{request.name}' configured successfully"
        }
    except Exception as e:
        logger.error(f"Failed to configure tool: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tools")
async def list_tools(
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """List all configured tools"""
    try:
        config = manager.get_current_config()
        tools = config.get('tools', [])
        
        return {
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models")
async def add_model_config(
    request: ModelConfigRequest,
    api_key: str = Depends(verify_management_api_key)
):
    """Add or update a model configuration"""
    try:
        # This would integrate with LangSwarm's model registry
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Model '{request.model_name}' configuration received",
            "note": "Model configuration integration pending"
        }
    except Exception as e:
        logger.error(f"Failed to configure model: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/prompts/templates")
async def list_prompt_templates(
    api_key: str = Depends(verify_management_api_key)
):
    """List available prompt templates"""
    try:
        # This would integrate with LangSwarm's prompt template system
        # For now, return default templates
        templates = [
            PromptTemplate(
                id="customer_support",
                name="Customer Support",
                template="You are a helpful customer support assistant for {company_name}. {additional_instructions}",
                variables=["company_name", "additional_instructions"],
                description="Template for customer support agents"
            ),
            PromptTemplate(
                id="technical_assistant",
                name="Technical Assistant",
                template="You are a technical assistant specializing in {domain}. Help users with {task_type} tasks. {technical_guidelines}",
                variables=["domain", "task_type", "technical_guidelines"],
                description="Template for technical assistance"
            )
        ]
        
        return {
            "templates": [template.dict() for template in templates],
            "count": len(templates)
        }
    except Exception as e:
        logger.error(f"Failed to list prompt templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
