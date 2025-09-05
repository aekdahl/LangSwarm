# 🎤 OpenAI Realtime API Integration

**LangSwarm now supports OpenAI's Realtime API for low-latency voice agents with full MCP tool integration.**

---

## 🎯 **Overview**

LangSwarm's OpenAI Realtime API integration enables:
- **Speech-to-Speech Conversations**: Natural voice interactions
- **Multimodal Input/Output**: Audio, text, and images  
- **Real-time Tool Calling**: MCP tools work seamlessly in voice conversations
- **Multiple Connection Types**: WebSocket, WebRTC, and SIP support
- **Backward Compatibility**: All existing LangSwarm features preserved

## ⚡ **Quick Start**

### **Option 1: Simple Voice Agent**

```python
from langswarm.core.wrappers.realtime_wrapper import create_realtime_agent

# Create voice agent with one line
agent = create_realtime_agent(
    name="voice_assistant",
    voice="alloy",  # or: echo, fable, onyx, nova, shimmer
    system_prompt="You are a helpful voice assistant.",
    memory_enabled=True
)

# Start voice conversation
async def voice_chat():
    async for event in agent.chat_realtime("Hello! Can you help me?"):
        if event["type"] == "audio_chunk":
            # Play audio response
            play_audio(event["data"])
        elif event["type"] == "text_chunk":
            # Display text response
            print(event["data"])
        elif event["type"] == "transcription":
            # Show what user said
            print(f"You said: {event['data']}")

# Run the conversation
import asyncio
asyncio.run(voice_chat())
```

### **Option 2: Configuration-Based Setup**

```yaml
# langswarm.yaml
version: "1.0"
agents:
  - id: "voice_assistant"
    model: "gpt-4o-realtime-preview"
    behavior: "helpful voice assistant"
    memory: true
    realtime_config:
      voice: "alloy"
      modalities: ["text", "audio"]
      input_audio_format: "pcm16"
      output_audio_format: "pcm16"
      tools: true  # Include all MCP tools
workflows:
  - "voice_assistant -> user"
```

---

## 🏗️ **Architecture**

LangSwarm's Realtime API integration leverages existing infrastructure:

```
┌─────────────────────────────────────────────────┐
│            LangSwarm Application               │
├─────────────────────────────────────────────────┤
│  RealtimeAgentWrapper                          │
│  ├─ Existing AgentWrapper (unchanged)          │
│  ├─ RealtimeMixin (voice capabilities)         │
│  └─ WebRTCHandler (browser connections)        │
├─────────────────────────────────────────────────┤
│  Enhanced MCP Tools                            │
│  ├─ Existing Tools (filesystem, workflow, etc.) │
│  └─ RealtimeVoiceMCPTool (TTS, transcription)  │
├─────────────────────────────────────────────────┤
│  OpenAI Realtime API                           │
│  ├─ WebSocket Connection                        │
│  ├─ WebRTC Connection                           │
│  └─ SIP Connection                              │
└─────────────────────────────────────────────────┘
```

**Key Benefits:**
- ✅ **Zero Breaking Changes**: Existing agents work unchanged
- ✅ **Full MCP Integration**: All tools work in voice conversations
- ✅ **Multiple Interfaces**: WebSocket, WebRTC, SIP support
- ✅ **Hybrid Sessions**: Voice + text in same conversation

---

## 🔧 **Connection Methods**

### **1. WebSocket Connection (Server-Side)**

Best for server applications with consistent network connections:

```python
from langswarm.core.wrappers.realtime_wrapper import RealtimeAgentWrapper

# Configure agent with realtime capabilities
agent = RealtimeAgentWrapper(
    name="server_voice_agent",
    agent=my_existing_agent,  # Use any existing LangSwarm agent
    model="gpt-4o-realtime-preview",
    realtime_config={
        "voice": "nova",
        "modalities": ["text", "audio"],
        "instructions": "You are a helpful assistant with tool access."
    }
)

# Start WebSocket conversation
async def websocket_conversation():
    # Send initial message
    async for event in agent.chat_realtime("What files are in my directory?"):
        if event["type"] == "function_call_result":
            # MCP tool was executed
            print(f"Tool result: {event['data']}")
        elif event["type"] == "audio_chunk":
            # Stream audio response
            await stream_audio_to_speakers(event["data"])

asyncio.run(websocket_conversation())
```

### **2. WebRTC Connection (Browser-Based)**

Best for browser applications with direct client connections:

```python
from langswarm.core.wrappers.webrtc_handler import WebRTCRealtimeHandler

# Set up WebRTC handler
webrtc = WebRTCRealtimeHandler(agent_wrapper=agent)
webrtc.configure_session({
    "voice": "alloy",
    "modalities": ["text", "audio"],
    "instructions": "You are a browser-based voice assistant."
})

# Get client configuration
client_config = webrtc.get_client_connection_config(api_key="your-openai-key")

# Generate HTML client
html_client = webrtc.get_html_example(server_endpoint="http://localhost:8000")
```

### **3. SIP Connection (Telephony)**

Leverage existing Twilio integration for phone calls:

```python
from langswarm.ui.twilio_gateway import TwilioAgentGateway
from langswarm.core.wrappers.realtime_wrapper import create_realtime_agent

# Create voice agent for phone calls
phone_agent = create_realtime_agent(
    name="phone_assistant",
    voice="onyx",  # Good for phone audio
    system_prompt="You are a phone-based assistant. Keep responses concise."
)

# Set up Twilio gateway
gateway = TwilioAgentGateway(agent=phone_agent)
gateway.run()  # Handles voice calls via SIP
```

---

## 🛠️ **MCP Tool Integration**

**All existing LangSwarm MCP tools work automatically in realtime conversations:**

### **Existing Tools Work Unchanged**

```python
# These tools work in voice conversations without modification:
- filesystem: "Read my config file"
- workflow_executor: "Run the data processing workflow"  
- tasklist: "Add this to my todo list"
- bigquery_vector_search: "Search for similar documents"
- dynamic_forms: "Create a feedback form"
```

### **Voice-Enhanced Tools**

The new `RealtimeVoiceMCPTool` adds voice-specific capabilities:

```python
# Voice-specific operations
agent.tool_registry["realtime_voice"] = RealtimeVoiceMCPTool("voice_tool")

# In conversation:
# User: "Convert this text to speech with a cheerful voice"
# Tool automatically handles TTS generation

# User: "What did I just say?" 
# Tool provides transcription of recent audio
```

### **Tool Call Flow in Voice Conversations**

```python
# 1. User speaks: "What files are in my home directory?"
# 2. OpenAI Realtime API transcribes speech
# 3. Model calls filesystem tool
# 4. LangSwarm executes MCP tool
# 5. Tool result sent back to OpenAI
# 6. Model generates voice response with results
# 7. User hears: "I found 23 files in your home directory, including..."
```

---

## 📱 **Browser Integration**

### **Complete HTML Example**

```html
<!DOCTYPE html>
<html>
<head>
    <title>LangSwarm Voice Agent</title>
    <script type="module" src="https://unpkg.com/@openai/agents@latest/dist/index.js"></script>
</head>
<body>
    <div>
        <button id="connect">Connect</button>
        <button id="disconnect">Disconnect</button>
        <div id="status">Disconnected</div>
        <div id="transcript"></div>
        <audio id="output" autoplay></audio>
    </div>

    <script>
        // LangSwarm WebRTC integration
        import { RealtimeSession } from '@openai/agents/realtime';
        
        const session = new RealtimeSession({
            apiKey: 'your-openai-key',
            instructions: 'You are a helpful assistant with tool access.',
            voice: 'alloy',
            tools: [
                // Tools automatically populated from LangSwarm MCP registry
                {
                    type: 'function',
                    name: 'filesystem_read_file',
                    description: 'Read file contents',
                    parameters: {
                        type: 'object',
                        properties: {
                            path: { type: 'string', description: 'File path' }
                        }
                    }
                }
            ]
        });
        
        // Handle tool calls via LangSwarm server
        session.on('function_call', async (toolCall) => {
            const response = await fetch('/realtime/tool-call', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(toolCall)
            });
            return await response.json();
        });
        
        // Handle audio responses
        session.on('audio.delta', (event) => {
            // Play audio chunks as they arrive
            playAudioChunk(event.delta);
        });
        
        document.getElementById('connect').onclick = () => session.connect();
        document.getElementById('disconnect').onclick = () => session.disconnect();
    </script>
</body>
</html>
```

---

## ⚙️ **Configuration Options**

### **Complete Configuration Reference**

```python
realtime_config = {
    # Model Configuration
    "model": "gpt-4o-realtime-preview",  # Realtime model
    "modalities": ["text", "audio"],     # Input/output types
    
    # Voice Configuration  
    "voice": "alloy",                    # Voice type
    "input_audio_format": "pcm16",       # Audio input format
    "output_audio_format": "pcm16",      # Audio output format
    
    # Speech Processing
    "input_audio_transcription": {
        "model": "whisper-1"             # Transcription model
    },
    "turn_detection": {
        "type": "server_vad",            # Voice activity detection
        "threshold": 0.5                 # Detection sensitivity
    },
    
    # Generation Settings
    "instructions": "Your system prompt here",
    "temperature": 0.8,                  # Response creativity
    "max_response_output_tokens": 4096,  # Response length limit
    
    # Tool Integration
    "tools": "auto",                     # Auto-include MCP tools
    "tool_choice": "auto"                # Automatic tool selection
}
```

### **Voice Options**

| **Voice** | **Description** | **Best For** |
|-----------|-----------------|--------------|
| **alloy** | Neutral, clear | General use |
| **echo** | Warm, friendly | Customer service |
| **fable** | Expressive, storytelling | Content creation |
| **onyx** | Deep, authoritative | Professional use |
| **nova** | Bright, energetic | Marketing, sales |
| **shimmer** | Soft, gentle | Healthcare, support |

---

## 🔍 **Advanced Features**

### **1. Hybrid Text + Voice Sessions**

```python
# Start with text, switch to voice
response = agent.chat("Hello, I'd like to start a voice conversation")
print(response)  # Text response

# Continue with voice
async for event in agent.chat_realtime():
    # Now voice-enabled
    handle_voice_event(event)
```

### **2. Custom Audio Processing**

```python
from langswarm.mcp.tools.realtime_voice.main import RealtimeVoiceMCPTool

voice_tool = RealtimeVoiceMCPTool("voice_processor")

# Optimize text for speech
result = voice_tool.run({
    "method": "optimize_voice_response",
    "params": {
        "text": "Hello! Here's your data: item1, item2, item3.",
        "speaking_style": "conversational",
        "include_pauses": True
    }
})

print(result["optimized_text"])
# "Hello! <break time='0.5s'/> Here's your data: <break time='0.2s'/> item one, <break time='0.2s'/> item two, <break time='0.2s'/> item three."
```

### **3. Audio Transcription**

```python
# Transcribe audio files
result = voice_tool.run({
    "method": "transcribe_audio", 
    "params": {
        "audio_base64": "base64_encoded_audio_data",
        "language": "en",
        "response_format": "verbose_json"
    }
})

print(result["transcript"])
print(result["segments"])  # Detailed timing information
```

---

## 🧪 **Testing & Examples**

### **1. Quick Test Script**

```python
# test_realtime.py
import asyncio
from langswarm.core.wrappers.realtime_wrapper import create_realtime_agent

async def test_voice_agent():
    agent = create_realtime_agent(
        name="test_agent",
        voice="alloy",
        system_prompt="You are a test assistant."
    )
    
    print("Starting voice conversation...")
    async for event in agent.chat_realtime("Can you tell me a joke?"):
        if event["type"] == "text_chunk":
            print(f"Text: {event['data']}")
        elif event["type"] == "transcription":
            print(f"You: {event['data']}")
        elif event["type"] == "error":
            print(f"Error: {event['data']}")

# Run test
asyncio.run(test_voice_agent())
```

### **2. Tool Integration Test**

```python
# test_tools_in_voice.py
import asyncio
from langswarm.core.wrappers.realtime_wrapper import create_realtime_agent
from langswarm.mcp.tools.filesystem.main import FilesystemMCPTool

async def test_voice_with_tools():
    # Create agent with filesystem tool
    agent = create_realtime_agent(
        name="file_assistant",
        voice="nova",
        system_prompt="You can help with file operations."
    )
    
    # Add filesystem tool
    agent.tool_registry["filesystem"] = FilesystemMCPTool("fs")
    
    # Test voice conversation with tool usage
    async for event in agent.chat_realtime("What files are in the current directory?"):
        if event["type"] == "function_call_result":
            print(f"Tool executed: {event['data']}")
        # Agent will speak the file list

asyncio.run(test_voice_with_tools())
```

---

## 🚨 **Error Handling & Troubleshooting**

### **Common Issues**

1. **"Realtime not configured" Error**
   ```python
   # Solution: Configure before use
   agent.configure_realtime({
       "voice": "alloy",
       "modalities": ["text", "audio"]
   })
   ```

2. **"OPENAI_API_KEY not set" Error**
   ```bash
   # Solution: Set environment variable
   export OPENAI_API_KEY=your_key_here
   ```

3. **WebSocket Connection Failed**
   ```python
   # Solution: Check network and API key
   session_started = await agent.start_realtime_session(api_key="explicit_key")
   if not session_started:
       print("Check API key and network connection")
   ```

4. **Tools Not Available in Voice**
   ```python
   # Solution: Ensure tools are registered
   print(agent.get_realtime_status())  # Check tool count
   ```

### **Debugging**

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check realtime status
status = agent.get_realtime_status()
print(f"Realtime enabled: {status['realtime_enabled']}")
print(f"Session active: {status['session_active']}")
print(f"Tools available: {status['tools_count']}")
```

---

## 📈 **Performance & Best Practices**

### **Optimization Tips**

1. **Audio Quality**: Use `pcm16` format for best quality
2. **Response Speed**: Set appropriate `turn_detection` threshold
3. **Tool Performance**: Keep MCP tool responses under 5 seconds
4. **Memory Usage**: Use memory-enabled agents for context persistence

### **Production Considerations**

```python
# Production configuration
production_config = {
    "model": "gpt-4o-realtime-preview",
    "voice": "alloy",
    "modalities": ["text", "audio"],
    "turn_detection": {
        "type": "server_vad",
        "threshold": 0.6  # Higher threshold for noisy environments
    },
    "max_response_output_tokens": 2048,  # Limit response length
    "temperature": 0.7  # Balanced creativity
}
```

---

## 🎉 **Summary**

LangSwarm's OpenAI Realtime API integration provides:

✅ **Zero Learning Curve**: Use existing LangSwarm knowledge  
✅ **Full Tool Access**: All MCP tools work in voice conversations  
✅ **Multiple Interfaces**: WebSocket, WebRTC, SIP support  
✅ **Production Ready**: Error handling, debugging, optimization  
✅ **Backward Compatible**: Existing code continues to work  

**Start building voice agents today with the same simplicity LangSwarm brings to text-based AI systems!**


