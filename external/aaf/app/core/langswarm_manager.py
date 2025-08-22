"""
LangSwarm Manager for AAF Backend
Handles LangSwarm agent lifecycle and configuration
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
import yaml

from langswarm.core.config import LangSwarmConfig
from langswarm.core.base.log import GlobalLogger

from .config import get_settings, get_langswarm_config, update_langswarm_config
from .bigquery_session_manager import create_session_manager

logger = logging.getLogger(__name__)


class MinimalUtils:
    """Minimal utilities class to avoid tokenizer initialization issues in containers"""
    
    def __init__(self):
        self.bot_logs = []
    
    def _get_api_key(self, provider, api_key):
        """Get API key from environment or provided key"""
        import os
        env_var_map = {
            "langchain": "OPENAI_API_KEY",
            "langchain-openai": "OPENAI_API_KEY", 
            "openai": "OPENAI_API_KEY",
        }
        env_var = env_var_map.get(provider.lower())
        
        if env_var and (key_from_env := os.getenv(env_var)):
            return key_from_env
        
        if api_key:
            return api_key
        
        raise ValueError(f"API key for {provider} not found. Set {env_var} or pass the key explicitly.")
    
    def bot_log(self, bot, message):
        """Simple logging without tokenizer dependency"""
        self.bot_logs.append((bot, message))
    
    def clean_text(self, text: str, remove_linebreaks: bool = False) -> str:
        """Clean text without complex dependencies"""
        import unicodedata
        
        # Handle Mock objects and non-string types
        if hasattr(text, '_mock_name') or not isinstance(text, str):
            return str(text)
        
        # Normalize unicode and replace non-breaking space with normal space
        text = text.replace("\u00a0", " ")
        
        # Remove line breaks if requested
        if remove_linebreaks:
            text = text.replace('\n', ' ').replace('\r', ' ')
        
        return unicodedata.normalize("NFKD", text)
    
    def safe_json_loads(self, text: str):
        """Safe JSON loading without complex parsing"""
        import json
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def update_price_tokens_use_estimates(self, *args, **kwargs):
        """Stub method for token usage tracking - no-op in minimal utils"""
        pass


class LangSwarmManager:
    """Manages LangSwarm configuration and agents"""
    
    def __init__(self):
        self.settings = get_settings()
        self.config: Optional[LangSwarmConfig] = None
        self.agents: Dict[str, Any] = {}
        self.default_agent_id = "aaf_chatbot"
        self.session_manager = None
        
    async def initialize(self):
        """Initialize LangSwarm configuration and agents"""
        try:
            # Load configuration
            await self.load_config()
            
            # Initialize session manager
            await self.initialize_session_manager()
            
            # Initialize agents
            await self.initialize_agents()
            
            logger.info("LangSwarm Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangSwarm Manager: {e}")
            raise
    
    async def load_config(self):
        """Load LangSwarm configuration"""
        try:
            config_dict = get_langswarm_config()
            # Initialize LangSwarmConfig with the data attribute
            self.config = LangSwarmConfig()
            self.config.data = config_dict
            logger.info(f"Loaded LangSwarm config from {self.settings.langswarm_config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load LangSwarm config: {e}")
            raise
    
    async def initialize_session_manager(self):
        """Initialize BigQuery session manager"""
        try:
            session_config = self.config.data.get('session', {})
            provider = session_config.get('provider', 'bigquery')
            
            if provider == 'bigquery':
                session_settings = session_config.get('settings', {})
                self.session_manager = create_session_manager(
                    project_id=session_settings.get('project_id', self.settings.google_cloud_project),
                    dataset_id=session_settings.get('dataset_id', self.settings.bigquery_dataset_id),
                    table_id=session_settings.get('table_id', 'sessions'),
                    ttl=session_settings.get('ttl', 3600)
                )
                logger.info("BigQuery session manager initialized")
            else:
                logger.warning(f"Unsupported session provider: {provider}")
                
        except Exception as e:
            logger.error(f"Failed to initialize session manager: {e}")
            # Continue without session manager
            self.session_manager = None
    
    async def initialize_agents(self):
        """Initialize all configured agents"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        # Clear existing agents
        self.agents.clear()
        
        # Initialize agents from config
        agents_config = self.config.data.get('agents', [])
        for agent_config in agents_config:
            try:
                # Use the basic LLM class from LangSwarm instead of complex AgentWrapper
                from langswarm.core.base.bot import LLM
                
                agent_id = agent_config.get('id', 'unknown')
                
                # Create minimal utils without tokenizer initialization
                minimal_utils = MinimalUtils()
                
                # Create agent with OpenAI provider and minimal utils
                agent = LLM(
                    name=agent_id,
                    model=agent_config.get('model', 'gpt-4o'),
                    provider='openai',
                    api_key=self.settings.openai_api_key,
                    temperature=agent_config.get('temperature', 0.7),
                    system_prompt=agent_config.get('system_prompt', 'You are a helpful assistant.'),
                    verbose=False,
                    utils=minimal_utils
                )
                
                self.agents[agent_id] = agent
                logger.info(f"Initialized LangSwarm LLM agent: {agent_id} with model {agent_config.get('model', 'gpt-4o')}")
                
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_config.get('id', 'unknown')}: {e}")
                raise
        
        # Ensure default agent exists
        if self.default_agent_id not in self.agents:
            logger.warning(f"Default agent '{self.default_agent_id}' not found in configuration")
    
    def get_agent(self, agent_id: Optional[str] = None):
        """Get an agent by ID, or return the default agent"""
        if not agent_id:
            agent_id = self.default_agent_id
        
        if agent_id not in self.agents:
            available_agents = list(self.agents.keys())
            raise ValueError(f"Agent '{agent_id}' not found. Available agents: {available_agents}")
        
        return self.agents[agent_id]
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents with their basic info"""
        agent_list = []
        for agent_id, agent in self.agents.items():
            agent_info = {
                "id": agent_id,
                "model": getattr(agent, 'model', 'unknown'),
                "behavior": getattr(agent, 'specialization', 'helpful'),
                "is_conversational": True,  # LLM agents are conversational
                "has_memory": hasattr(agent, 'memory') and agent.memory is not None,
                "has_tools": False  # Basic LLM doesn't have tools
            }
            agent_list.append(agent_info)
        
        return agent_list
    
    async def chat(self, message: str, agent_id: Optional[str] = None, 
                   session_id: Optional[str] = None, **kwargs) -> str:
        """Send a chat message to an agent"""
        agent = self.get_agent(agent_id)
        
        # Handle session management
        if session_id and self.session_manager:
            # Get or create session
            session = await self.session_manager.get_session(session_id)
            if not session:
                await self.session_manager.create_session(
                    session_id=session_id,
                    agent_id=agent_id or self.default_agent_id
                )
            
            # Increment message count
            await self.session_manager.increment_message_count(session_id)
            
                    # LLM.chat() doesn't accept session_id, so we don't pass kwargs
        return agent.chat(message)
    
    async def chat_stream(self, message: str, agent_id: Optional[str] = None,
                         session_id: Optional[str] = None, **kwargs):
        """Stream a chat response from an agent"""
        agent = self.get_agent(agent_id)
        
        # Handle session management
        if session_id and self.session_manager:
            # Get or create session
            session = await self.session_manager.get_session(session_id)
            if not session:
                await self.session_manager.create_session(
                    session_id=session_id,
                    agent_id=agent_id or self.default_agent_id
                )
            
            # Increment message count
            await self.session_manager.increment_message_count(session_id)
            
        # Since LLM class doesn't have chat_stream, use regular chat and simulate streaming
        try:
            # LLM.chat() doesn't accept session_id or other kwargs
            response = agent.chat(message)
            
            # Simulate streaming by yielding words
            words = response.split()
            for word in words:
                yield word + " "
                
        except Exception as e:
            logger.error(f"Error in chat_stream: {e}")
            yield f"Error: {str(e)}"
    
    async def update_configuration(self, new_config: Dict[str, Any]):
        """Update LangSwarm configuration and reinitialize agents"""
        try:
            # Validate the new configuration
            LangSwarmConfig(new_config)
            
            # Save the new configuration
            update_langswarm_config(new_config)
            
            # Reload configuration and reinitialize agents
            await self.load_config()
            await self.initialize_agents()
            
            logger.info("Configuration updated and agents reinitialized")
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise
    
    async def update_agent_config(self, agent_id: str, agent_config: Dict[str, Any]):
        """Update a specific agent's configuration"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        # Find and update the agent in the configuration
        config_dict = get_langswarm_config()
        agents = config_dict.get('agents', [])
        
        agent_updated = False
        for i, agent in enumerate(agents):
            if agent.get('id') == agent_id:
                agents[i] = agent_config
                agent_updated = True
                break
        
        if not agent_updated:
            # Add new agent
            agents.append(agent_config)
        
        # Update the full configuration
        config_dict['agents'] = agents
        await self.update_configuration(config_dict)
    
    async def delete_agent(self, agent_id: str):
        """Delete an agent from the configuration"""
        if agent_id == self.default_agent_id:
            raise ValueError(f"Cannot delete default agent '{self.default_agent_id}'")
        
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        # Remove agent from configuration
        config_dict = get_langswarm_config()
        agents = config_dict.get('agents', [])
        
        agents = [agent for agent in agents if agent.get('id') != agent_id]
        config_dict['agents'] = agents
        
        # Update the configuration
        await self.update_configuration(config_dict)
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current LangSwarm configuration as dict"""
        return get_langswarm_config()
    
    async def restart(self):
        """Restart the LangSwarm manager (reload config and reinitialize agents)"""
        logger.info("Restarting LangSwarm Manager...")
        await self.initialize()
        logger.info("LangSwarm Manager restarted successfully")
    
    # Session management methods
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if self.session_manager:
            return await self.session_manager.get_session(session_id)
        return None
    
    async def create_session(self, session_id: Optional[str] = None, **kwargs) -> str:
        """Create a new session"""
        if self.session_manager:
            return await self.session_manager.create_session(session_id, **kwargs)
        return session_id or str(__import__('uuid').uuid4())
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if self.session_manager:
            return await self.session_manager.delete_session(session_id)
        return True
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        if self.session_manager:
            return await self.session_manager.get_session_stats()
        return {"error": "Session manager not available"}
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List active sessions"""
        if self.session_manager:
            return await self.session_manager.list_active_sessions()
        return []


# Global manager instance
langswarm_manager = LangSwarmManager()


async def get_langswarm_manager() -> LangSwarmManager:
    """Get the global LangSwarm manager instance"""
    return langswarm_manager
