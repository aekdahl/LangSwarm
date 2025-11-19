# Realtime Voice Tool

## Description

Real-time voice interaction capabilities for voice-enabled applications, transcription, and speech synthesis.

## Instructions

This tool provides voice operations with two calling approaches:

### Intent-Based Calling (Smart Voice Operations)

Use **`realtime_voice`** with intent for intelligent voice handling:

**Parameters:**
- `intent`: What voice operation you need
- `context`: Relevant details (language, voice type, use case)

**When to use:**
- Voice responses: "Read this message aloud"
- Transcription needs: "Convert the recording to text"
- Voice interaction: "Start voice conversation mode"

**Examples:**
- "Read message aloud" → intent="convert this message to speech and play it", context="user notification, clear voice"
- "Transcribe recording" → intent="convert voice recording to text", context="meeting notes"

### Direct Method Calling

**`realtime_voice.synthesize`** - Text to speech
- **Parameters:** text, voice_type, language
- **Use when:** Converting specific text to audio

**`realtime_voice.transcribe`** - Speech to text
- **Parameters:** audio_source, language
- **Use when:** Converting audio to text

**`realtime_voice.start_conversation`** - Interactive voice session
- **Parameters:** mode, language, context
- **Use when:** Starting voice interaction session

## Brief

Real-time voice interaction for speech synthesis, transcription, and voice-enabled applications.
