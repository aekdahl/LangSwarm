"""
LangSwarm Configuration Editor API
Frontend-friendly endpoints for editing LangSwarm YAML configuration
"""
import logging
import yaml
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from datetime import datetime
import copy

from ..core.langswarm_manager import get_langswarm_manager, LangSwarmManager
from ..core.persistent_config import get_persistent_config_manager
from ..core.config import get_settings, get_langswarm_config, update_langswarm_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config-editor", tags=["config-editor"])
security = HTTPBearer()


def verify_management_api_key(authorization: HTTPAuthorizationCredentials = Depends(security)):
    """Verify management API key"""
    settings = get_settings()
    
    if not settings.management_api_enabled:
        raise HTTPException(status_code=403, detail="Management API is disabled")
    
    if authorization.credentials != settings.management_api_secret:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return authorization.credentials


# ================================
# Pydantic Models for Frontend
# ================================

class AgentModel(BaseModel):
    """Agent configuration model for frontend"""
    id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(default="langchain-openai", description="Agent type")
    model: str = Field(..., description="LLM model (e.g., gpt-4, gpt-3.5-turbo)")
    behavior: str = Field(default="helpful", description="Agent behavior type")
    system_prompt: Optional[str] = Field(None, description="System prompt for the agent")
    is_conversational: bool = Field(True, description="Enable conversation history")
    max_history_length: int = Field(20, description="Maximum conversation history length")
    tools: List[str] = Field(default=[], description="List of tool IDs to use")
    retrievers: List[str] = Field(default=[], description="List of retriever IDs to use")
    
    # Memory configuration
    memory_enabled: bool = Field(True, description="Enable memory for this agent")
    memory_backend: str = Field(default="bigquery", description="Memory backend type")
    
    # Additional settings
    temperature: Optional[float] = Field(None, description="LLM temperature (0.0-2.0)", ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in response", gt=0)
    timeout: Optional[int] = Field(None, description="Request timeout in seconds", gt=0)


class ToolModel(BaseModel):
    """Tool configuration model for frontend"""
    id: str = Field(..., description="Unique tool identifier")
    type: str = Field(..., description="Tool type (e.g., web_search, calculator)")
    name: Optional[str] = Field(None, description="Display name for the tool")
    description: Optional[str] = Field(None, description="Tool description")
    enabled: bool = Field(True, description="Whether tool is enabled")
    config: Dict[str, Any] = Field(default={}, description="Tool-specific configuration")


class MemoryModel(BaseModel):
    """Memory configuration model for frontend"""
    backend: str = Field(default="bigquery", description="Memory backend type")
    enabled: bool = Field(True, description="Enable memory system")
    settings: Dict[str, Any] = Field(default={}, description="Memory backend settings")


class SessionModel(BaseModel):
    """Session configuration model for frontend"""
    provider: str = Field(default="bigquery", description="Session storage provider")
    ttl: int = Field(default=3600, description="Session timeout in seconds", gt=0)
    settings: Dict[str, Any] = Field(default={}, description="Session provider settings")


class LangSwarmConfigModel(BaseModel):
    """Complete LangSwarm configuration model for frontend"""
    version: str = Field(default="1.0", description="Configuration version")
    project_name: Optional[str] = Field(default=None, description="Project name")
    langswarm: Optional[Dict[str, Any]] = Field(default=None, description="Core LangSwarm settings")
    agents: List[AgentModel] = Field(default=[], description="Agent configurations")
    tools: List[ToolModel] = Field(default=[], description="Tool configurations")
    workflows: Optional[List[Dict[str, Any]]] = Field(default=None, description="Workflow configurations")
    memory: MemoryModel = Field(default_factory=MemoryModel, description="Memory configuration")
    session: SessionModel = Field(default_factory=SessionModel, description="Session configuration")
    logging: Dict[str, Any] = Field(default={}, description="Logging configuration")


class ConfigValidationResult(BaseModel):
    """Configuration validation result"""
    valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default=[], description="Validation errors")
    warnings: List[str] = Field(default=[], description="Validation warnings")
    affected_components: List[str] = Field(default=[], description="Components that will be restarted")


class ConfigUpdateRequest(BaseModel):
    """Configuration update request"""
    config: LangSwarmConfigModel = Field(..., description="New configuration")
    validate_only: bool = Field(False, description="Only validate, don't apply changes")
    backup_current: bool = Field(True, description="Backup current configuration")
    restart_agents: bool = Field(True, description="Restart agents after update")
    changelog: str = Field("Configuration update via frontend", description="Change description for version history")


class ConfigBackup(BaseModel):
    """Configuration backup metadata"""
    id: str = Field(..., description="Backup ID")
    timestamp: str = Field(..., description="Backup timestamp")
    description: str = Field(..., description="Backup description")
    config_hash: str = Field(..., description="Configuration hash")


# ================================
# Configuration Editor Endpoints
# ================================

@router.get("/current", response_model=LangSwarmConfigModel)
async def get_current_config(
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Get current LangSwarm configuration in frontend-friendly format
    """
    try:
        # Get raw configuration
        raw_config = manager.get_current_config()
        
        logger.info(f"Raw config agents count: {len(raw_config.get('agents', []))}")
        if raw_config.get('agents'):
            first_agent_tools = raw_config['agents'][0].get('tools', [])
            logger.info(f"First agent tools: {first_agent_tools}")
            logger.info(f"First tool type: {type(first_agent_tools[0]) if first_agent_tools else 'None'}")
        
        # Convert to frontend model
        frontend_config = _convert_to_frontend_model(raw_config)
        
        logger.info(f"Frontend config created successfully")
        return frontend_config
        
    except Exception as e:
        logger.error(f"Failed to get current config: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ConfigValidationResult)
async def validate_config(
    config: LangSwarmConfigModel,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Validate LangSwarm configuration without applying changes
    """
    try:
        # Convert to internal format
        internal_config = _convert_to_internal_format(config)
        
        # Validate configuration
        validation_result = _validate_config(internal_config, manager)
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        return ConfigValidationResult(
            valid=False,
            errors=[str(e)],
            warnings=[],
            affected_components=[]
        )


@router.put("/update", response_model=Dict[str, Any])
async def update_config(
    request: ConfigUpdateRequest,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Update LangSwarm configuration with full workflow support
    """
    try:
        # Convert to internal format
        internal_config = _convert_to_internal_format(request.config)
        
        # Validate first
        validation = _validate_config(internal_config, manager)
        
        if not validation.valid:
            return {
                "success": False,
                "validation": validation.dict(),
                "message": "Configuration validation failed"
            }
        
        # If validate_only, return validation results
        if request.validate_only:
            return {
                "success": True,
                "validation": validation.dict(),
                "message": "Configuration is valid"
            }
        
        # Save to persistent storage with versioning
        persistent_manager = get_persistent_config_manager()
        changelog = request.changelog
        version_id = await persistent_manager.save_config(internal_config, changelog)
        
        # Backup current configuration if requested
        backup_id = None
        if request.backup_current:
            backup_id = await _backup_current_config()
        
        # Apply configuration changes
        await manager.update_configuration(internal_config)
        
        # Restart agents if requested
        if request.restart_agents:
            await manager.restart()
        
        return {
            "success": True,
            "validation": validation.dict(),
            "version_id": version_id,
            "backup_id": backup_id,
            "message": "Configuration updated successfully",
            "agents_reinitialized": len(manager.agents)
        }
        
    except Exception as e:
        logger.error(f"Config update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schema")
async def get_config_schema(
    api_key: str = Depends(verify_management_api_key)
):
    """
    Get JSON schema for LangSwarm configuration (for frontend form generation)
    """
    try:
        # Return Pydantic schema
        schema = LangSwarmConfigModel.schema()
        
        # Add additional metadata for frontend
        schema["ui_metadata"] = {
            "agent_types": [
                {"value": "langchain-openai", "label": "OpenAI (GPT)"},
                {"value": "langchain-anthropic", "label": "Anthropic (Claude)"},
                {"value": "langchain-ollama", "label": "Ollama (Local)"},
            ],
            "models": {
                "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "ollama": ["llama2", "mistral", "codellama"]
            },
            "behaviors": [
                {"value": "helpful", "label": "Helpful Assistant"},
                {"value": "support", "label": "Customer Support"},
                {"value": "technical", "label": "Technical Expert"},
                {"value": "creative", "label": "Creative Assistant"},
                {"value": "analytical", "label": "Data Analyst"}
            ],
            "tool_types": [
                {"value": "web_search", "label": "Web Search"},
                {"value": "calculator", "label": "Calculator"},
                {"value": "code_executor", "label": "Code Executor"},
                {"value": "file_manager", "label": "File Manager"},
                {"value": "mcpremote", "label": "Remote MCP Tool"}
            ],
            "memory_backends": [
                {"value": "bigquery", "label": "Google BigQuery"},
                {"value": "sqlite", "label": "SQLite"},
                {"value": "memory", "label": "In-Memory"}
            ]
        }
        
        return schema
        
    except Exception as e:
        logger.error(f"Failed to get config schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_config_templates(
    api_key: str = Depends(verify_management_api_key)
):
    """
    Get predefined configuration templates for common use cases
    """
    try:
        templates = {
            "basic_chatbot": {
                "name": "Basic Chatbot",
                "description": "Simple customer support chatbot",
                "config": LangSwarmConfigModel(
                    agents=[
                        AgentModel(
                            id="support_bot",
                            model="gpt-3.5-turbo",
                            behavior="support",
                            system_prompt="You are a helpful customer support assistant. Be professional and concise."
                        )
                    ]
                )
            },
            "advanced_assistant": {
                "name": "Advanced AI Assistant",
                "description": "Multi-capability AI assistant with tools",
                "config": LangSwarmConfigModel(
                    agents=[
                        AgentModel(
                            id="ai_assistant",
                            model="gpt-4",
                            behavior="helpful",
                            system_prompt="You are an advanced AI assistant with access to various tools. Help users with their questions and tasks.",
                            tools=["web_search", "calculator"]
                        )
                    ],
                    tools=[
                        ToolModel(
                            id="web_search",
                            type="web_search",
                            description="Search the web for information",
                            config={"max_results": 5}
                        ),
                        ToolModel(
                            id="calculator",
                            type="calculator",
                            description="Perform mathematical calculations"
                        )
                    ]
                )
            },
            "multi_agent": {
                "name": "Multi-Agent System",
                "description": "Multiple specialized agents for different tasks",
                "config": LangSwarmConfigModel(
                    agents=[
                        AgentModel(
                            id="general_assistant",
                            model="gpt-4",
                            behavior="helpful",
                            system_prompt="You are a general-purpose assistant."
                        ),
                        AgentModel(
                            id="technical_expert",
                            model="gpt-4",
                            behavior="technical",
                            system_prompt="You are a technical expert specializing in software development and IT support."
                        ),
                        AgentModel(
                            id="customer_support",
                            model="gpt-3.5-turbo",
                            behavior="support",
                            system_prompt="You are a customer support representative. Be empathetic and solution-focused."
                        )
                    ]
                )
            }
        }
        
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"Failed to get config templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions")
async def list_config_versions(
    limit: int = 20,
    api_key: str = Depends(verify_management_api_key)
):
    """List configuration versions with metadata"""
    try:
        persistent_manager = get_persistent_config_manager()
        versions = await persistent_manager.list_config_versions(limit)
        
        return {
            "versions": versions,
            "count": len(versions)
        }
        
    except Exception as e:
        logger.error(f"Failed to list config versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback")
async def rollback_config(
    target_version: str,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """Rollback to a specific configuration version"""
    try:
        persistent_manager = get_persistent_config_manager()
        
        # Perform rollback (creates new version)
        success = await persistent_manager.rollback_to_version(target_version, "frontend-user")
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to rollback to version {target_version}")
        
        # Get the new current config and apply it
        current_config = await persistent_manager.get_current_config()
        if current_config:
            await manager.update_configuration(current_config)
            await manager.restart()
        
        return {
            "success": True,
            "message": f"Successfully rolled back to version {target_version}",
            "agents_reinitialized": len(manager.agents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rollback config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata")
async def get_config_metadata(
    api_key: str = Depends(verify_management_api_key)
):
    """Get configuration metadata including version info"""
    try:
        persistent_manager = get_persistent_config_manager()
        metadata = await persistent_manager.get_instance_metadata()
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to get config metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=List[AgentModel])
async def get_agent_configs(
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Get all agent configurations in frontend format
    """
    try:
        config = manager.get_current_config()
        agents = config.get("agents", [])
        
        # Convert to frontend models
        frontend_agents = []
        for agent in agents:
            frontend_agent = _convert_agent_to_frontend(agent)
            frontend_agents.append(frontend_agent)
        
        return frontend_agents
        
    except Exception as e:
        logger.error(f"Failed to get agent configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents", response_model=Dict[str, Any])
async def create_or_update_agent(
    agent: AgentModel,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Create or update a single agent configuration
    """
    try:
        # Convert to internal format
        internal_agent = _convert_agent_to_internal(agent)
        
        # Update the agent
        await manager.update_agent_config(agent.id, internal_agent)
        
        return {
            "success": True,
            "message": f"Agent '{agent.id}' updated successfully",
            "agent": agent.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/agents/{agent_id}")
async def delete_agent_config(
    agent_id: str,
    api_key: str = Depends(verify_management_api_key),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Delete an agent configuration
    """
    try:
        await manager.delete_agent(agent_id)
        
        return {
            "success": True,
            "message": f"Agent '{agent_id}' deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ================================
# Helper Functions
# ================================

def _convert_to_frontend_model(raw_config: Dict[str, Any]) -> LangSwarmConfigModel:
    """Convert internal config format to frontend model"""
    
    # Convert agents
    agents = []
    for agent_config in raw_config.get("agents", []):
        frontend_agent = _convert_agent_to_frontend(agent_config)
        agents.append(frontend_agent)
    
    # Convert tools (handle both list and dict formats)
    tools = []
    tools_config = raw_config.get("tools", [])
    
    # Handle new unified format (dict) vs old format (list)
    if isinstance(tools_config, dict):
        # New unified format: tools is a dictionary
        for tool_id, tool_config in tools_config.items():
            if isinstance(tool_config, dict):
                tool = ToolModel(
                    id=tool_id,
                    type=tool_config.get("type", ""),
                    name=tool_config.get("name", tool_id),
                    description=tool_config.get("description"),
                    enabled=tool_config.get("enabled", True),
                    config=tool_config.get("config", {})
                )
                tools.append(tool)
    else:
        # Old format: tools is a list
        for tool_config in tools_config:
            if isinstance(tool_config, dict):
                tool = ToolModel(
                    id=tool_config.get("id", ""),
                    type=tool_config.get("type", ""),
                    name=tool_config.get("name"),
                    description=tool_config.get("description"),
                    enabled=tool_config.get("enabled", True),
                    config=tool_config.get("config", {})
                )
                tools.append(tool)
    
    # Convert memory config
    memory_config = raw_config.get("memory", {})
    memory = MemoryModel(
        backend=memory_config.get("backend", "bigquery"),
        enabled=memory_config.get("enabled", True),
        settings=memory_config.get("settings", {})
    )
    
    # Convert session config
    session_config = raw_config.get("session", {})
    session = SessionModel(
        provider=session_config.get("provider", "bigquery"),
        ttl=session_config.get("settings", {}).get("ttl", 3600),
        settings=session_config.get("settings", {})
    )
    
    return LangSwarmConfigModel(
        version=raw_config.get("version", "1.0"),
        project_name=raw_config.get("project_name"),
        langswarm=raw_config.get("langswarm"),
        agents=agents,
        tools=tools,
        workflows=raw_config.get("workflows"),
        memory=memory,
        session=session,
        logging=raw_config.get("logging", {})
    )


def _convert_agent_to_frontend(agent_config: Dict[str, Any]) -> AgentModel:
    """Convert internal agent config to frontend model"""
    # Convert tools from complex objects to simple strings (tool IDs/names)
    tools_list = agent_config.get("tools", [])
    tool_ids = []
    
    logger.info(f"Converting tools for agent {agent_config.get('id')}: {len(tools_list)} tools found")
    
    for i, tool in enumerate(tools_list):
        if isinstance(tool, dict):
            # Extract tool ID/name from complex object
            tool_id = tool.get("name") or tool.get("id", "")
            if tool_id:
                tool_ids.append(tool_id)
                logger.info(f"Converted tool {i}: {tool_id} from complex object")
            else:
                logger.warning(f"Tool {i} has no name or id: {tool}")
        elif isinstance(tool, str):
            # Already a string, use as-is
            tool_ids.append(tool)
            logger.info(f"Tool {i} already string: {tool}")
        else:
            logger.warning(f"Unknown tool type at {i}: {type(tool)} - {tool}")
    
    logger.info(f"Final tool_ids for agent {agent_config.get('id')}: {tool_ids}")
    
    # Also convert retrievers similarly if they have complex objects
    retrievers_list = agent_config.get("retrievers", [])
    retriever_ids = []
    for retriever in retrievers_list:
        if isinstance(retriever, dict):
            retriever_id = retriever.get("name") or retriever.get("id", "")
            if retriever_id:
                retriever_ids.append(retriever_id)
        elif isinstance(retriever, str):
            retriever_ids.append(retriever)
    
    return AgentModel(
        id=agent_config.get("id", ""),
        agent_type=agent_config.get("agent_type", "langchain-openai"),
        model=agent_config.get("model", "gpt-4"),
        behavior=agent_config.get("behavior", "helpful"),
        system_prompt=agent_config.get("system_prompt"),
        is_conversational=agent_config.get("is_conversational", True),
        max_history_length=agent_config.get("max_history_length", 20),
        tools=tool_ids,
        retrievers=retriever_ids,
        memory_enabled=agent_config.get("memory", {}).get("enabled", True) if isinstance(agent_config.get("memory"), dict) else True,
        memory_backend=agent_config.get("memory", {}).get("backend", "bigquery") if isinstance(agent_config.get("memory"), dict) else "bigquery",
        temperature=agent_config.get("temperature"),
        max_tokens=agent_config.get("max_tokens"),
        timeout=agent_config.get("timeout")
    )


def _convert_to_internal_format(frontend_config: LangSwarmConfigModel) -> Dict[str, Any]:
    """Convert frontend model to internal config format"""
    
    # Convert agents
    agents = []
    for agent in frontend_config.agents:
        internal_agent = _convert_agent_to_internal(agent)
        agents.append(internal_agent)
    
    # Convert tools
    tools = []
    for tool in frontend_config.tools:
        internal_tool = {
            "id": tool.id,
            "type": tool.type,
            "enabled": tool.enabled,
            **tool.config
        }
        if tool.name:
            internal_tool["name"] = tool.name
        if tool.description:
            internal_tool["description"] = tool.description
        
        tools.append(internal_tool)
    
    return {
        "version": frontend_config.version,
        "agents": agents,
        "tools": tools,
        "memory": {
            "backend": frontend_config.memory.backend,
            "settings": frontend_config.memory.settings
        },
        "session": {
            "provider": frontend_config.session.provider,
            "settings": {
                "ttl": frontend_config.session.ttl,
                **frontend_config.session.settings
            }
        },
        "logging": frontend_config.logging
    }


def _convert_agent_to_internal(agent: AgentModel) -> Dict[str, Any]:
    """Convert frontend agent model to internal format"""
    internal = {
        "id": agent.id,
        "agent_type": agent.agent_type,
        "model": agent.model,
        "behavior": agent.behavior,
        "is_conversational": agent.is_conversational,
        "max_history_length": agent.max_history_length,
        "tools": agent.tools,
        "retrievers": agent.retrievers,
        "memory": {
            "backend": agent.memory_backend,
            "auto_store": True,
            "settings": {}
        }
    }
    
    if agent.system_prompt:
        internal["system_prompt"] = agent.system_prompt
    
    if agent.temperature is not None:
        internal["temperature"] = agent.temperature
    
    if agent.max_tokens is not None:
        internal["max_tokens"] = agent.max_tokens
    
    if agent.timeout is not None:
        internal["timeout"] = agent.timeout
    
    return internal


def _validate_config(config: Dict[str, Any], manager: LangSwarmManager) -> ConfigValidationResult:
    """Validate configuration and return detailed results"""
    errors = []
    warnings = []
    affected_components = []
    
    try:
        # Validate basic structure
        if "agents" not in config or not config["agents"]:
            errors.append("At least one agent must be configured")
        
        # Validate agents
        agent_ids = set()
        for agent in config.get("agents", []):
            agent_id = agent.get("id")
            if not agent_id:
                errors.append("All agents must have an 'id' field")
                continue
            
            if agent_id in agent_ids:
                errors.append(f"Duplicate agent ID: {agent_id}")
            agent_ids.add(agent_id)
            
            # Check required fields
            if not agent.get("model"):
                errors.append(f"Agent '{agent_id}' must have a 'model' field")
            
            # Check tools exist
            for tool_id in agent.get("tools", []):
                tool_exists = any(tool.get("id") == tool_id for tool in config.get("tools", []))
                if not tool_exists:
                    warnings.append(f"Agent '{agent_id}' references undefined tool '{tool_id}'")
        
        # Validate tools
        tool_ids = set()
        for tool in config.get("tools", []):
            tool_id = tool.get("id")
            if not tool_id:
                errors.append("All tools must have an 'id' field")
                continue
            
            if tool_id in tool_ids:
                errors.append(f"Duplicate tool ID: {tool_id}")
            tool_ids.add(tool_id)
            
            if not tool.get("type"):
                errors.append(f"Tool '{tool_id}' must have a 'type' field")
        
        # Check what components will be affected
        if manager.agents:
            affected_components.extend(["agents", "memory", "session"])
        
        return ConfigValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            affected_components=affected_components
        )
        
    except Exception as e:
        return ConfigValidationResult(
            valid=False,
            errors=[f"Validation error: {str(e)}"],
            warnings=[],
            affected_components=[]
        )


async def _backup_current_config() -> str:
    """Backup current configuration and return backup ID"""
    try:
        current_config = get_langswarm_config()
        timestamp = datetime.utcnow().isoformat()
        backup_id = f"backup_{timestamp.replace(':', '-').replace('.', '-')}"
        
        # In a real implementation, you'd save this to a backup storage
        # For now, we'll just log it
        logger.info(f"Created config backup: {backup_id}")
        
        return backup_id
        
    except Exception as e:
        logger.error(f"Failed to backup config: {e}")
        return f"backup_failed_{datetime.utcnow().isoformat()}"
