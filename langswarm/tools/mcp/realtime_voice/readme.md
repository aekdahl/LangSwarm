# Realtime Voice MCP Tool

## Description
Provides real-time voice processing capabilities for LangSwarm agents. This tool enables voice input/output, speech-to-text, text-to-speech, and voice-based interactions in conversational AI applications.

## Capabilities
- **Speech-to-Text**: Convert voice input to text for processing
- **Text-to-Speech**: Generate voice output from text responses
- **Voice Commands**: Process voice-based commands and interactions
- **Real-time Processing**: Stream voice processing for conversational AI

## Configuration
Required environment variables:
- `OPENAI_API_KEY`: OpenAI API key for voice processing (if using OpenAI models)

Optional configuration:
- Default voice model: OpenAI's voice processing
- Audio format: WAV, MP3 support
- Streaming: Real-time audio processing

## Usage Examples

### Intent-Based Calling (Recommended)
Express what you want to accomplish:
```json
{
  "tool": "realtime_voice",
  "intent": "process voice input",
  "context": "user speaking voice command for task management"
}
```

### Direct Parameter Calling
Process speech to text:
```json
{
  "method": "speech_to_text",
  "params": {
    "audio_data": "base64_encoded_audio",
    "format": "wav"
  }
}
```

## Integration
This tool integrates with LangSwarm agents to provide voice interaction capabilities for conversational AI applications, enabling hands-free operation and natural voice-based user interfaces.
