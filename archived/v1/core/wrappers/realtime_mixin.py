# langswarm/core/wrappers/realtime_mixin.py

import asyncio
import json
import websockets
import base64
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RealtimeMixin:
    """
    Mixin for OpenAI Realtime API integration with LangSwarm agents.
    
    Extends existing LangSwarm agents with realtime voice capabilities while
    preserving all existing functionality and MCP tool integration.
    """
    
    def __init__(self):
        self.realtime_session = None
        self.realtime_config = None
        self.audio_buffer = []
        self.conversation_items = []
        self.realtime_enabled = False
        
    def configure_realtime(self, config: Dict[str, Any]):
        """
        Configure OpenAI Realtime API settings.
        
        Args:
            config: Realtime configuration dict with:
                - api_key: OpenAI API key
                - model: Realtime model (e.g., 'gpt-4o-realtime-preview')
                - voice: Voice type ('alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer')
                - modalities: List of ['text', 'audio']
                - instructions: System instructions for the model
                - input_audio_format: 'pcm16' or 'g711_ulaw' or 'g711_alaw'
                - output_audio_format: 'pcm16' or 'g711_ulaw' or 'g711_alaw'
                - input_audio_transcription: dict with model config
                - turn_detection: dict with type and threshold
                - tools: List of available tools (auto-populated from MCP registry)
        """
        self.realtime_config = {
            "model": config.get("model", "gpt-4o-realtime-preview"),
            "voice": config.get("voice", "alloy"),
            "modalities": config.get("modalities", ["text", "audio"]),
            "instructions": config.get("instructions", getattr(self, 'system_prompt', '')),
            "input_audio_format": config.get("input_audio_format", "pcm16"),
            "output_audio_format": config.get("output_audio_format", "pcm16"),
            "input_audio_transcription": config.get("input_audio_transcription", {"model": "whisper-1"}),
            "turn_detection": config.get("turn_detection", {"type": "server_vad", "threshold": 0.5}),
            "tools": self._get_realtime_tools(),
            "tool_choice": "auto",
            "temperature": config.get("temperature", 0.8),
            "max_response_output_tokens": config.get("max_response_output_tokens", 4096)
        }
        self.realtime_enabled = True
        logger.info(f"Realtime API configured for model: {self.realtime_config['model']}")
    
    def _get_realtime_tools(self) -> list:
        """
        Convert LangSwarm MCP tools to OpenAI Realtime API function schema.
        
        Leverages existing tool_registry to automatically make all MCP tools
        available in realtime conversations.
        """
        if not hasattr(self, 'tool_registry') or not self.tool_registry:
            return []
        
        realtime_tools = []
        for tool_name, tool_instance in self.tool_registry.items():
            if hasattr(tool_instance, 'mcp_server'):
                # Get MCP server schema
                mcp_server = tool_instance.mcp_server
                for task_name, task_meta in mcp_server.tasks.items():
                    function_schema = {
                        "type": "function",
                        "name": f"{tool_name}_{task_name}",
                        "description": task_meta["description"],
                        "parameters": task_meta["input_model"].schema()
                    }
                    realtime_tools.append(function_schema)
            elif hasattr(tool_instance, 'description'):
                # Fallback for non-MCP tools
                function_schema = {
                    "type": "function", 
                    "name": tool_name,
                    "description": getattr(tool_instance, 'description', f"Tool: {tool_name}"),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {"type": "string", "description": "Tool input"}
                        }
                    }
                }
                realtime_tools.append(function_schema)
        
        logger.info(f"Registered {len(realtime_tools)} tools for realtime API")
        return realtime_tools
    
    async def start_realtime_session(self, api_key: str = None) -> bool:
        """
        Start a new OpenAI Realtime API session.
        
        Args:
            api_key: OpenAI API key (uses environment variable if not provided)
            
        Returns:
            bool: True if session started successfully
        """
        if not self.realtime_enabled:
            logger.error("Realtime not configured. Call configure_realtime() first.")
            return False
        
        api_key = api_key or getattr(self, 'api_key', None)
        if not api_key:
            logger.error("OpenAI API key required for realtime session")
            return False
        
        try:
            # OpenAI Realtime WebSocket endpoint
            url = "wss://api.openai.com/v1/realtime"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            self.realtime_session = await websockets.connect(url, extra_headers=headers)
            
            # Send session configuration
            session_update = {
                "type": "session.update", 
                "session": self.realtime_config
            }
            await self.realtime_session.send(json.dumps(session_update))
            
            logger.info("OpenAI Realtime session started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start realtime session: {e}")
            return False
    
    async def send_audio(self, audio_data: bytes):
        """
        Send audio data to the realtime session.
        
        Args:
            audio_data: Raw audio bytes in configured format
        """
        if not self.realtime_session:
            logger.error("No active realtime session")
            return
        
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Send audio append event
        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }
        await self.realtime_session.send(json.dumps(event))
    
    async def send_text(self, text: str):
        """
        Send text input to the realtime session.
        
        Args:
            text: Text message to send
        """
        if not self.realtime_session:
            logger.error("No active realtime session")
            return
        
        # Create conversation item
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user", 
                "content": [{"type": "input_text", "text": text}]
            }
        }
        await self.realtime_session.send(json.dumps(event))
        
        # Trigger response
        response_event = {"type": "response.create"}
        await self.realtime_session.send(json.dumps(response_event))
    
    async def handle_realtime_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Handle incoming events from OpenAI Realtime API.
        
        Yields:
            Dict containing event data and processed responses
        """
        if not self.realtime_session:
            logger.error("No active realtime session")
            return
        
        try:
            async for message in self.realtime_session:
                event = json.loads(message)
                event_type = event.get("type")
                
                # Handle different event types
                if event_type == "response.audio.delta":
                    # Audio response chunk
                    audio_data = base64.b64decode(event["delta"])
                    yield {
                        "type": "audio_chunk",
                        "data": audio_data,
                        "response_id": event.get("response_id")
                    }
                
                elif event_type == "response.text.delta":
                    # Text response chunk  
                    yield {
                        "type": "text_chunk",
                        "data": event["delta"],
                        "response_id": event.get("response_id")
                    }
                
                elif event_type == "response.function_call_arguments.delta":
                    # Function call in progress
                    yield {
                        "type": "function_call_delta", 
                        "data": event,
                        "call_id": event.get("call_id")
                    }
                
                elif event_type == "response.function_call_arguments.done":
                    # Function call complete - execute MCP tool
                    result = await self._execute_mcp_tool(event)
                    yield {
                        "type": "function_call_result",
                        "data": result,
                        "call_id": event.get("call_id")
                    }
                
                elif event_type == "input_audio_buffer.speech_started":
                    yield {"type": "speech_started", "data": event}
                
                elif event_type == "input_audio_buffer.speech_stopped":
                    yield {"type": "speech_stopped", "data": event}
                
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    yield {"type": "transcription", "data": event["transcript"]}
                
                elif event_type == "error":
                    logger.error(f"Realtime API error: {event}")
                    yield {"type": "error", "data": event}
                
                else:
                    # Pass through other events
                    yield {"type": event_type, "data": event}
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Realtime session connection closed")
        except Exception as e:
            logger.error(f"Error handling realtime events: {e}")
    
    async def _execute_mcp_tool(self, function_call_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute MCP tool based on OpenAI Realtime function call.
        
        Args:
            function_call_event: Function call event from OpenAI Realtime API
            
        Returns:
            Dict with tool execution result
        """
        try:
            call_id = function_call_event.get("call_id")
            function_name = function_call_event.get("name", "")
            arguments = json.loads(function_call_event.get("arguments", "{}"))
            
            # Parse tool name and task from function name
            if "_" in function_name:
                tool_name, task_name = function_name.split("_", 1)
            else:
                tool_name = function_name
                task_name = "run"
            
            # Execute tool via existing MCP infrastructure
            if hasattr(self, 'tool_registry') and tool_name in self.tool_registry:
                tool_instance = self.tool_registry[tool_name]
                
                if hasattr(tool_instance, 'mcp_server'):
                    # MCP tool execution
                    result = tool_instance.mcp_server.call_task(task_name, arguments)
                else:
                    # Fallback tool execution
                    result = tool_instance.run(arguments)
                
                # Send function call output back to OpenAI
                output_event = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(result)
                    }
                }
                await self.realtime_session.send(json.dumps(output_event))
                
                return {"success": True, "result": result, "call_id": call_id}
            
            else:
                error_msg = f"Tool '{tool_name}' not found in registry"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "call_id": call_id}
                
        except Exception as e:
            error_msg = f"Error executing MCP tool: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "call_id": call_id}
    
    async def close_realtime_session(self):
        """Close the realtime session."""
        if self.realtime_session:
            await self.realtime_session.close()
            self.realtime_session = None
            logger.info("Realtime session closed")
    
    def supports_realtime(self) -> bool:
        """Check if this agent supports realtime capabilities."""
        return self.realtime_enabled and hasattr(self, 'model') and 'realtime' in self.model.lower()


