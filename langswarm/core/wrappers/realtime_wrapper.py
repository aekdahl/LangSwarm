# langswarm/core/wrappers/realtime_wrapper.py

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, Union
from .generic import AgentWrapper
from .realtime_mixin import RealtimeMixin
import logging

logger = logging.getLogger(__name__)

class RealtimeAgentWrapper(AgentWrapper, RealtimeMixin):
    """
    Enhanced AgentWrapper with OpenAI Realtime API capabilities.
    
    Extends the existing LangSwarm AgentWrapper to support:
    - Voice input/output via OpenAI Realtime API
    - Real-time audio streaming  
    - WebSocket and WebRTC connections
    - MCP tool integration in realtime conversations
    - Backward compatibility with all existing functionality
    """
    
    def __init__(self, 
                 name, 
                 agent,
                 model,
                 realtime_config: Optional[Dict[str, Any]] = None,
                 **kwargs):
        """
        Initialize RealtimeAgentWrapper.
        
        Args:
            name: Agent name
            agent: Underlying agent instance
            model: Model name (should be realtime-compatible for voice features)
            realtime_config: OpenAI Realtime API configuration
            **kwargs: All other AgentWrapper arguments
        """
        # Initialize parent AgentWrapper with all existing functionality
        super().__init__(name, agent, model, **kwargs)
        
        # Initialize RealtimeMixin
        RealtimeMixin.__init__(self)
        
        # Configure realtime if config provided
        if realtime_config:
            self.configure_realtime(realtime_config)
        
        logger.info(f"RealtimeAgentWrapper initialized for {name}")
    
    def chat(self, q=None, reset=False, erase_query=False, remove_linebreaks=False, 
             session_id=None, start_new_session=False, **kwargs):
        """
        Enhanced chat method with realtime fallback.
        
        Preserves all existing chat functionality. If realtime is not active,
        behaves exactly like the parent AgentWrapper.
        """
        # If realtime session is active and input is text, could optionally
        # route through realtime API for consistency, but for now maintain
        # separation between traditional chat and realtime
        
        return super().chat(q, reset, erase_query, remove_linebreaks, 
                          session_id, start_new_session, **kwargs)
    
    async def chat_realtime(self, 
                           text_input: Optional[str] = None,
                           audio_input: Optional[bytes] = None,
                           api_key: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Start a realtime conversation with voice and text capabilities.
        
        Args:
            text_input: Optional text message to start conversation
            audio_input: Optional audio data to start conversation
            api_key: OpenAI API key (uses instance key if not provided)
            
        Yields:
            Dict: Realtime events including audio chunks, text responses, 
                  transcriptions, and tool execution results
        """
        if not self.realtime_enabled:
            raise ValueError("Realtime not configured. Call configure_realtime() first.")
        
        # Start realtime session
        session_started = await self.start_realtime_session(api_key)
        if not session_started:
            raise RuntimeError("Failed to start realtime session")
        
        try:
            # Send initial input if provided
            if text_input:
                await self.send_text(text_input)
            elif audio_input:
                await self.send_audio(audio_input)
            
            # Stream realtime events
            async for event in self.handle_realtime_events():
                yield event
                
        finally:
            await self.close_realtime_session()
    
    async def send_realtime_message(self, 
                                   text: Optional[str] = None, 
                                   audio: Optional[bytes] = None):
        """
        Send a message to an active realtime session.
        
        Args:
            text: Text message to send
            audio: Audio data to send
        """
        if not self.realtime_session:
            raise RuntimeError("No active realtime session. Use chat_realtime() to start one.")
        
        if text:
            await self.send_text(text)
        elif audio:
            await self.send_audio(audio)
        else:
            raise ValueError("Either text or audio input required")
    
    def create_realtime_config(self, 
                              voice: str = "alloy",
                              modalities: list = None,
                              include_mcp_tools: bool = True,
                              **kwargs) -> Dict[str, Any]:
        """
        Helper to create realtime configuration with sensible defaults.
        
        Args:
            voice: Voice type ('alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer')
            modalities: List of modalities ['text', 'audio']
            include_mcp_tools: Whether to include MCP tools in realtime session
            **kwargs: Additional realtime configuration options
            
        Returns:
            Dict: Realtime configuration ready for configure_realtime()
        """
        config = {
            "model": kwargs.get("model", "gpt-4o-realtime-preview"),
            "voice": voice,
            "modalities": modalities or ["text", "audio"],
            "instructions": kwargs.get("instructions", getattr(self, 'system_prompt', '')),
            **kwargs
        }
        
        if not include_mcp_tools:
            config["tools"] = []
        
        return config
    
    def get_realtime_status(self) -> Dict[str, Any]:
        """
        Get current realtime session status.
        
        Returns:
            Dict: Status information including session state, configuration, etc.
        """
        return {
            "realtime_enabled": self.realtime_enabled,
            "session_active": self.realtime_session is not None,
            "model": self.realtime_config.get("model") if self.realtime_config else None,
            "voice": self.realtime_config.get("voice") if self.realtime_config else None,
            "modalities": self.realtime_config.get("modalities") if self.realtime_config else None,
            "tools_count": len(self.realtime_config.get("tools", [])) if self.realtime_config else 0,
            "conversation_items": len(self.conversation_items)
        }


# Factory function for easy creation
def create_realtime_agent(name: str, 
                         model: str = "gpt-4o-realtime-preview",
                         voice: str = "alloy",
                         system_prompt: str = None,
                         tools: list = None,
                         memory_enabled: bool = True,
                         **kwargs) -> RealtimeAgentWrapper:
    """
    Factory function to easily create a RealtimeAgentWrapper with sensible defaults.
    
    Args:
        name: Agent name
        model: Realtime-compatible model name
        voice: Voice type for audio responses
        system_prompt: System instructions for the agent
        tools: List of tool names to include
        memory_enabled: Whether to enable memory storage
        **kwargs: Additional agent configuration
        
    Returns:
        RealtimeAgentWrapper: Configured realtime agent
    """
    from langswarm.core.agents.simple import create_chat_agent
    
    # Create underlying agent with memory if requested
    agent_config = kwargs.copy()
    if memory_enabled:
        agent_config["memory"] = True
    
    # Create base agent
    base_agent = create_chat_agent(name, **agent_config)
    
    # Create realtime configuration
    realtime_config = {
        "model": model,
        "voice": voice,
        "modalities": ["text", "audio"],
        "instructions": system_prompt or f"You are {name}, a helpful AI assistant with realtime voice capabilities."
    }
    
    # Create realtime wrapper
    realtime_agent = RealtimeAgentWrapper(
        name=name,
        agent=base_agent,
        model=model,
        system_prompt=system_prompt,
        realtime_config=realtime_config,
        **kwargs
    )
    
    logger.info(f"Created realtime agent '{name}' with model '{model}' and voice '{voice}'")
    return realtime_agent


