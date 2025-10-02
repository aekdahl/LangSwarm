# langswarm/core/wrappers/webrtc_handler.py

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class WebRTCRealtimeHandler:
    """
    WebRTC connection handler for browser-based OpenAI Realtime API integration.
    
    Enables direct browser-to-OpenAI connections while maintaining LangSwarm
    MCP tool integration and session management.
    """
    
    def __init__(self, agent_wrapper=None):
        self.agent_wrapper = agent_wrapper
        self.connection_state = "disconnected"
        self.session_config = None
        self.event_handlers = {}
        
    def configure_session(self, config: Dict[str, Any]):
        """
        Configure the realtime session for WebRTC connection.
        
        Args:
            config: Session configuration dict with:
                - model: Realtime model name
                - voice: Voice configuration
                - modalities: Supported modalities
                - instructions: System instructions
                - tools: Available tools (from LangSwarm MCP registry)
        """
        self.session_config = config
        logger.info("WebRTC session configured")
    
    def get_client_connection_config(self, api_key: str) -> Dict[str, Any]:
        """
        Generate configuration for client-side WebRTC connection.
        
        This configuration is sent to the browser client to establish
        the WebRTC connection directly to OpenAI.
        
        Args:
            api_key: OpenAI API key for client connection
            
        Returns:
            Dict: Client configuration for WebRTC connection
        """
        if not self.session_config:
            raise ValueError("Session not configured. Call configure_session() first.")
        
        # Base configuration for client
        client_config = {
            "apiKey": api_key,
            "dangerouslyAllowAPIKeyInBrowser": True,
            "instructions": self.session_config.get("instructions", ""),
            "voice": self.session_config.get("voice", "alloy"),
            "inputAudioFormat": "pcm16",
            "outputAudioFormat": "pcm16",
            "inputAudioTranscription": {"model": "whisper-1"},
            "turnDetection": {"type": "server_vad", "threshold": 0.5},
            "tools": self._get_webrtc_tools(),
            "toolChoice": "auto"
        }
        
        return client_config
    
    def _get_webrtc_tools(self) -> list:
        """
        Get tools configuration for WebRTC client.
        
        Note: In WebRTC mode, tool execution happens on the server side
        via webhooks/callbacks to maintain MCP integration.
        """
        if not self.agent_wrapper or not hasattr(self.agent_wrapper, 'tool_registry'):
            return []
        
        tools = []
        for tool_name, tool_instance in self.agent_wrapper.tool_registry.items():
            if hasattr(tool_instance, 'mcp_server'):
                mcp_server = tool_instance.mcp_server
                for task_name, task_meta in mcp_server.tasks.items():
                    # Create tool definition for client
                    tool_def = {
                        "type": "function",
                        "name": f"{tool_name}_{task_name}",
                        "description": task_meta["description"],
                        "parameters": task_meta["input_model"].schema(),
                        # Add metadata for server-side routing
                        "langswarm_meta": {
                            "tool_name": tool_name,
                            "task_name": task_name,
                            "mcp_enabled": True
                        }
                    }
                    tools.append(tool_def)
        
        return tools
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """
        Register event handler for WebRTC session events.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        self.event_handlers[event_type] = handler
    
    async def handle_tool_call(self, tool_call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tool call from WebRTC client.
        
        This method is called via webhook when the client receives a
        function call from OpenAI that needs to be executed on the server.
        
        Args:
            tool_call_data: Tool call information from client
            
        Returns:
            Dict: Tool execution result
        """
        try:
            function_name = tool_call_data.get("name", "")
            arguments = tool_call_data.get("arguments", {})
            call_id = tool_call_data.get("call_id")
            
            # Extract LangSwarm metadata
            meta = tool_call_data.get("langswarm_meta", {})
            tool_name = meta.get("tool_name")
            task_name = meta.get("task_name", "run")
            
            if not tool_name:
                # Fallback parsing
                if "_" in function_name:
                    tool_name, task_name = function_name.split("_", 1)
                else:
                    tool_name = function_name
            
            # Execute via LangSwarm MCP infrastructure
            if (self.agent_wrapper and 
                hasattr(self.agent_wrapper, 'tool_registry') and 
                tool_name in self.agent_wrapper.tool_registry):
                
                tool_instance = self.agent_wrapper.tool_registry[tool_name]
                
                if hasattr(tool_instance, 'mcp_server'):
                    result = tool_instance.mcp_server.call_task(task_name, arguments)
                else:
                    result = tool_instance.run(arguments)
                
                logger.info(f"Executed tool {tool_name}_{task_name} successfully")
                return {
                    "success": True,
                    "result": result,
                    "call_id": call_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            else:
                error_msg = f"Tool '{tool_name}' not found"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "call_id": call_id
                }
                
        except Exception as e:
            error_msg = f"Error executing tool: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "call_id": tool_call_data.get("call_id")
            }
    
    def get_javascript_client_code(self) -> str:
        """
        Generate JavaScript client code for WebRTC connection.
        
        Returns:
            str: JavaScript code for browser client
        """
        return '''
// LangSwarm WebRTC Realtime Client
class LangSwarmRealtimeClient {
    constructor(config) {
        this.config = config;
        this.session = null;
        this.connectionState = 'disconnected';
        this.onAudioChunk = null;
        this.onTextResponse = null;
        this.onToolCall = null;
        this.onTranscription = null;
        this.onError = null;
    }
    
    async connect() {
        try {
            // Import OpenAI Realtime SDK
            const { RealtimeSession } = await import('@openai/agents/realtime');
            
            // Create session
            this.session = new RealtimeSession({
                apiKey: this.config.apiKey,
                dangerouslyAllowAPIKeyInBrowser: this.config.dangerouslyAllowAPIKeyInBrowser,
                instructions: this.config.instructions,
                voice: this.config.voice,
                inputAudioFormat: this.config.inputAudioFormat,
                outputAudioFormat: this.config.outputAudioFormat,
                inputAudioTranscription: this.config.inputAudioTranscription,
                turnDetection: this.config.turnDetection,
                tools: this.config.tools,
                toolChoice: this.config.toolChoice
            });
            
            // Set up event handlers
            this.session.on('audio.delta', (event) => {
                if (this.onAudioChunk) {
                    this.onAudioChunk(event.delta);
                }
            });
            
            this.session.on('text.delta', (event) => {
                if (this.onTextResponse) {
                    this.onTextResponse(event.delta);
                }
            });
            
            this.session.on('function_call', async (event) => {
                if (this.onToolCall) {
                    const result = await this.onToolCall(event);
                    // Send result back to session
                    this.session.sendFunctionCallOutput(event.call_id, result);
                }
            });
            
            this.session.on('transcription', (event) => {
                if (this.onTranscription) {
                    this.onTranscription(event.transcript);
                }
            });
            
            this.session.on('error', (event) => {
                if (this.onError) {
                    this.onError(event.error);
                }
            });
            
            // Connect to OpenAI
            await this.session.connect();
            this.connectionState = 'connected';
            
            console.log('LangSwarm Realtime client connected');
            return true;
            
        } catch (error) {
            console.error('Failed to connect:', error);
            this.connectionState = 'error';
            if (this.onError) {
                this.onError(error);
            }
            return false;
        }
    }
    
    async sendText(text) {
        if (this.session && this.connectionState === 'connected') {
            await this.session.sendText(text);
        }
    }
    
    async sendAudio(audioData) {
        if (this.session && this.connectionState === 'connected') {
            await this.session.sendAudio(audioData);
        }
    }
    
    async disconnect() {
        if (this.session) {
            await this.session.disconnect();
            this.session = null;
            this.connectionState = 'disconnected';
        }
    }
}

// Export for use
window.LangSwarmRealtimeClient = LangSwarmRealtimeClient;
        '''.strip()
    
    def get_html_example(self, server_endpoint: str = "http://localhost:8000") -> str:
        """
        Generate HTML example for WebRTC realtime connection.
        
        Args:
            server_endpoint: Server endpoint for tool execution callbacks
            
        Returns:
            str: Complete HTML example
        """
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LangSwarm Realtime Voice Agent</title>
    <script type="module" src="https://unpkg.com/@openai/agents@latest/dist/index.js"></script>
</head>
<body>
    <div id="app">
        <h1>LangSwarm Realtime Voice Agent</h1>
        <div>
            <button id="connectBtn">Connect</button>
            <button id="disconnectBtn" disabled>Disconnect</button>
        </div>
        <div>
            <input type="text" id="textInput" placeholder="Type a message..." />
            <button id="sendTextBtn" disabled>Send Text</button>
        </div>
        <div>
            <button id="startRecordingBtn" disabled>Start Recording</button>
            <button id="stopRecordingBtn" disabled>Stop Recording</button>
        </div>
        <div id="status">Disconnected</div>
        <div id="transcript"></div>
        <div id="responses"></div>
        <audio id="audioOutput" autoplay></audio>
    </div>

    <script>
        {self.get_javascript_client_code()}
        
        // Application logic
        let client = null;
        let mediaRecorder = null;
        let audioChunks = [];
        
        // Configuration (replace with your API key)
        const config = {self.session_config};
        config.apiKey = 'your-openai-api-key-here';
        config.dangerouslyAllowAPIKeyInBrowser = true;
        
        // UI elements
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        const sendTextBtn = document.getElementById('sendTextBtn');
        const textInput = document.getElementById('textInput');
        const startRecordingBtn = document.getElementById('startRecordingBtn');
        const stopRecordingBtn = document.getElementById('stopRecordingBtn');
        const status = document.getElementById('status');
        const transcript = document.getElementById('transcript');
        const responses = document.getElementById('responses');
        const audioOutput = document.getElementById('audioOutput');
        
        // Event handlers
        connectBtn.addEventListener('click', async () => {{
            client = new LangSwarmRealtimeClient(config);
            
            // Set up callbacks
            client.onAudioChunk = (audioData) => {{
                // Play audio response
                const blob = new Blob([audioData], {{type: 'audio/pcm'}});
                const url = URL.createObjectURL(blob);
                audioOutput.src = url;
            }};
            
            client.onTextResponse = (text) => {{
                responses.innerHTML += '<div><strong>Assistant:</strong> ' + text + '</div>';
            }};
            
            client.onToolCall = async (toolCall) => {{
                // Send to LangSwarm server for execution
                try {{
                    const response = await fetch('{server_endpoint}/realtime/tool-call', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(toolCall)
                    }});
                    return await response.json();
                }} catch (error) {{
                    return {{success: false, error: error.message}};
                }}
            }};
            
            client.onTranscription = (text) => {{
                transcript.innerHTML += '<div><strong>You:</strong> ' + text + '</div>';
            }};
            
            client.onError = (error) => {{
                console.error('Client error:', error);
                status.textContent = 'Error: ' + error.message;
            }};
            
            // Connect
            const connected = await client.connect();
            if (connected) {{
                status.textContent = 'Connected';
                connectBtn.disabled = true;
                disconnectBtn.disabled = false;
                sendTextBtn.disabled = false;
                startRecordingBtn.disabled = false;
            }}
        }});
        
        disconnectBtn.addEventListener('click', async () => {{
            if (client) {{
                await client.disconnect();
                status.textContent = 'Disconnected';
                connectBtn.disabled = false;
                disconnectBtn.disabled = true;
                sendTextBtn.disabled = true;
                startRecordingBtn.disabled = true;
                stopRecordingBtn.disabled = true;
            }}
        }});
        
        sendTextBtn.addEventListener('click', async () => {{
            const text = textInput.value.trim();
            if (text && client) {{
                await client.sendText(text);
                responses.innerHTML += '<div><strong>You:</strong> ' + text + '</div>';
                textInput.value = '';
            }}
        }});
        
        // Audio recording
        startRecordingBtn.addEventListener('click', async () => {{
            const stream = await navigator.mediaDevices.getUserMedia({{audio: true}});
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {{
                audioChunks.push(event.data);
            }};
            
            mediaRecorder.onstop = async () => {{
                const audioBlob = new Blob(audioChunks, {{type: 'audio/wav'}});
                const audioBuffer = await audioBlob.arrayBuffer();
                const uint8Array = new Uint8Array(audioBuffer);
                
                if (client) {{
                    await client.sendAudio(uint8Array);
                }}
            }};
            
            mediaRecorder.start();
            startRecordingBtn.disabled = true;
            stopRecordingBtn.disabled = false;
        }});
        
        stopRecordingBtn.addEventListener('click', () => {{
            if (mediaRecorder) {{
                mediaRecorder.stop();
                startRecordingBtn.disabled = false;
                stopRecordingBtn.disabled = true;
            }}
        }});
    </script>
</body>
</html>
        '''.strip()


