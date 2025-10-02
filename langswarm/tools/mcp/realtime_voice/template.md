# Realtime Voice MCP Tool

## Description

Real-time voice processing tool with natural language intent understanding using standard MCP protocol.

## Instructions

🎯 **LangSwarm's Intelligent Intent Processing (Standard MCP)**

This tool supports both intelligent intent-based calling and direct method execution using the standard MCP protocol with simplified syntax.

**Preferred: Intent-Based Calling (LangSwarm USP)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "realtime_voice",
    "arguments": {
      "intent": "Convert this audio message to text and respond with a friendly voice",
      "context": "customer service, voice interaction"
    }
  }
}
```

**Alternative: Direct Method Calling (Simplified)**
```json
{
  "method": "call_tool",
  "params": {
    "name": "realtime_voice.process_speech",
    "arguments": {"audio_data": "base64_encoded_audio", "language": "en-US"}
  }
}
```

**When to use:** Speech-to-text conversion, voice responses, voice-based user interactions

**Intent examples:**
- "Listen to this customer voicemail and summarize it"
- "Generate a voice response for this support ticket"
- "Convert this meeting audio to searchable text"

**Available methods:** process_speech, text_to_speech, get_supported_languages, configure_voice

### Standard MCP Protocol Methods

This tool supports standard MCP protocol for discovery and introspection:

**Discovery Methods:**
- `list_tools()` - Discover all available tools in the system
- `call_tool(name, arguments)` - Execute with flattened name format or intent
- `list_prompts()` - Find available agent prompts for workflows  
- `list_resources()` - See available files (template.md, agents.yaml, etc.)

**Execution Methods:**
- `call_tool(name, arguments)` - Supports both `tool.method` and intent formats
- `get_prompt(name, arguments)` - Get formatted prompts with variables
- `read_resource(uri)` - Access specific resource content

**Example Protocol Discovery:**
```json
{
  "method": "list_tools",
  "params": {}
}
```

**Pro tip:** Use intent-based calls for intelligent processing, or flattened direct calls (`tool.method`) for precise control.

## Brief

Real-time voice processing with intelligent intent processing via flattened MCP protocol.
