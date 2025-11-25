# langswarm/mcp/tools/realtime_voice/main.py

"""
OpenAI Realtime Voice MCP Tool for LangSwarm

Provides voice-specific MCP capabilities including:
- Text-to-speech generation
- Audio transcription
- Voice response optimization
- Audio file processing
- Speech synthesis controls
"""

import asyncio
import json
import base64
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.tools.base import BaseTool
from langswarm.tools.mcp.protocol_interface import MCPProtocolMixin

logger = logging.getLogger(__name__)

# === Input/Output Models ===

class TextToSpeechInput(BaseModel):
    """Input model for text-to-speech generation"""
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field(default="alloy", description="Voice type: alloy, echo, fable, onyx, nova, shimmer")
    speed: float = Field(default=1.0, description="Speech speed (0.25 to 4.0)")
    format: str = Field(default="mp3", description="Audio format: mp3, opus, aac, flac")
    model: str = Field(default="tts-1", description="TTS model: tts-1 or tts-1-hd")

class TextToSpeechOutput(BaseModel):
    """Output model for text-to-speech generation"""
    success: bool = Field(..., description="Whether TTS generation succeeded")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio data")
    audio_url: Optional[str] = Field(None, description="URL to audio file if saved")
    format: str = Field(..., description="Audio format used")
    duration_ms: Optional[int] = Field(None, description="Audio duration in milliseconds")
    voice: str = Field(..., description="Voice used")
    error: Optional[str] = Field(None, description="Error message if failed")

class TranscribeAudioInput(BaseModel):
    """Input model for audio transcription"""
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio data")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    language: Optional[str] = Field(None, description="Language code (auto-detect if not specified)")
    model: str = Field(default="whisper-1", description="Transcription model")
    response_format: str = Field(default="json", description="Response format: json, text, srt, verbose_json, vtt")
    temperature: float = Field(default=0, description="Sampling temperature (0 to 1)")

class TranscribeAudioOutput(BaseModel):
    """Output model for audio transcription"""
    success: bool = Field(..., description="Whether transcription succeeded")
    transcript: Optional[str] = Field(None, description="Transcribed text")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    segments: Optional[List[Dict]] = Field(None, description="Detailed segments if verbose format")
    error: Optional[str] = Field(None, description="Error message if failed")

class OptimizeVoiceResponseInput(BaseModel):
    """Input model for voice response optimization"""
    text: str = Field(..., description="Text to optimize for voice")
    target_duration_seconds: Optional[float] = Field(None, description="Target response duration")
    speaking_style: str = Field(default="conversational", description="Style: conversational, formal, casual, energetic")
    include_pauses: bool = Field(default=True, description="Whether to include natural pauses")
    optimize_for_clarity: bool = Field(default=True, description="Optimize for speech clarity")

class OptimizeVoiceResponseOutput(BaseModel):
    """Output model for voice response optimization"""
    success: bool = Field(..., description="Whether optimization succeeded")
    optimized_text: str = Field(..., description="Text optimized for voice synthesis")
    estimated_duration_seconds: Optional[float] = Field(None, description="Estimated speaking duration")
    modifications_made: List[str] = Field(default_factory=list, description="List of optimizations applied")
    ssml_markup: Optional[str] = Field(None, description="SSML markup if applicable")
    error: Optional[str] = Field(None, description="Error message if failed")

class VoiceConfigInput(BaseModel):
    """Input model for voice configuration"""
    voice: str = Field(..., description="Voice name to configure")
    settings: Dict[str, Any] = Field(..., description="Voice settings to apply")

class VoiceConfigOutput(BaseModel):
    """Output model for voice configuration"""
    success: bool = Field(..., description="Whether configuration succeeded")
    voice: str = Field(..., description="Voice name")
    applied_settings: Dict[str, Any] = Field(..., description="Settings that were applied")
    available_voices: List[str] = Field(default_factory=list, description="List of available voices")
    error: Optional[str] = Field(None, description="Error message if failed")

# === Core Functions ===

async def text_to_speech(text: str, voice: str = "alloy", speed: float = 1.0, 
                        format: str = "mp3", model: str = "tts-1") -> Dict[str, Any]:
    """
    Generate speech from text using OpenAI TTS API.
    
    Args:
        text: Text to convert to speech
        voice: Voice type
        speed: Speech speed
        format: Audio format
        model: TTS model to use
        
    Returns:
        Dict with audio data and metadata
    """
    try:
        # Import OpenAI here to avoid dependency issues
        try:
            import openai
        except ImportError:
            return {
                "success": False,
                "error": "OpenAI library not installed. Run: pip install openai",
                "voice": voice,
                "format": format
            }
        
        # Get API key from environment
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY environment variable not set",
                "voice": voice,
                "format": format
            }
        
        client = openai.OpenAI(api_key=api_key)
        
        # Generate speech
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
            response_format=format
        )
        
        # Convert to base64
        audio_data = response.content
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Estimate duration (rough calculation)
        # Average speaking rate is ~150 words per minute
        word_count = len(text.split())
        estimated_duration_ms = int((word_count / 150) * 60 * 1000 / speed)
        
        return {
            "success": True,
            "audio_base64": audio_base64,
            "format": format,
            "duration_ms": estimated_duration_ms,
            "voice": voice
        }
        
    except Exception as e:
        logger.error(f"Text-to-speech error: {e}")
        return {
            "success": False,
            "error": str(e),
            "voice": voice,
            "format": format
        }

async def transcribe_audio(audio_base64: Optional[str] = None, 
                          audio_url: Optional[str] = None,
                          language: Optional[str] = None,
                          model: str = "whisper-1",
                          response_format: str = "json",
                          temperature: float = 0) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper API.
    
    Args:
        audio_base64: Base64 encoded audio data
        audio_url: URL to audio file
        language: Language code
        model: Whisper model
        response_format: Response format
        temperature: Sampling temperature
        
    Returns:
        Dict with transcription results
    """
    try:
        import openai
        import os
        import tempfile
        import requests
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY environment variable not set"
            }
        
        client = openai.OpenAI(api_key=api_key)
        
        # Get audio data
        if audio_base64:
            audio_data = base64.b64decode(audio_base64)
        elif audio_url:
            response = requests.get(audio_url)
            response.raise_for_status()
            audio_data = response.content
        else:
            return {
                "success": False,
                "error": "Either audio_base64 or audio_url must be provided"
            }
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe
            with open(temp_file_path, 'rb') as audio_file:
                transcript_response = client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=language,
                    response_format=response_format,
                    temperature=temperature
                )
            
            # Parse response based on format
            if response_format == "json" or response_format == "verbose_json":
                result = {
                    "success": True,
                    "transcript": transcript_response.text,
                    "language": getattr(transcript_response, 'language', None),
                    "duration": getattr(transcript_response, 'duration', None)
                }
                
                if hasattr(transcript_response, 'segments'):
                    result["segments"] = transcript_response.segments
                    
            else:
                # Text, SRT, VTT formats
                result = {
                    "success": True,
                    "transcript": str(transcript_response)
                }
            
            return result
            
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Audio transcription error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def optimize_voice_response(text: str, 
                                 target_duration_seconds: Optional[float] = None,
                                 speaking_style: str = "conversational",
                                 include_pauses: bool = True,
                                 optimize_for_clarity: bool = True) -> Dict[str, Any]:
    """
    Optimize text for voice synthesis and natural speech.
    
    Args:
        text: Original text
        target_duration_seconds: Target speaking duration
        speaking_style: Style of speech
        include_pauses: Whether to add pauses
        optimize_for_clarity: Whether to optimize for clarity
        
    Returns:
        Dict with optimized text and metadata
    """
    try:
        modifications = []
        optimized_text = text
        
        # Basic text cleanup for voice
        if optimize_for_clarity:
            # Expand abbreviations
            abbreviations = {
                "Dr.": "Doctor", "Mr.": "Mister", "Mrs.": "Missus", 
                "Ms.": "Miss", "Prof.": "Professor", "etc.": "etcetera",
                "i.e.": "that is", "e.g.": "for example", "vs.": "versus"
            }
            
            for abbrev, full in abbreviations.items():
                if abbrev in optimized_text:
                    optimized_text = optimized_text.replace(abbrev, full)
                    modifications.append(f"Expanded '{abbrev}' to '{full}'")
        
        # Add natural pauses
        if include_pauses:
            # Add brief pauses after periods and commas
            optimized_text = optimized_text.replace(". ", ". <break time='0.5s'/> ")
            optimized_text = optimized_text.replace(", ", ", <break time='0.2s'/> ")
            modifications.append("Added natural pauses")
        
        # Adjust for speaking style
        if speaking_style == "energetic":
            # Add emphasis
            optimized_text = optimized_text.replace("!", " <emphasis level='strong'>!</emphasis>")
            modifications.append("Added energetic emphasis")
        elif speaking_style == "formal":
            # Ensure proper punctuation
            if not optimized_text.endswith(('.', '!', '?')):
                optimized_text += "."
            modifications.append("Added formal punctuation")
        
        # Estimate duration
        word_count = len(optimized_text.split())
        # Average 150 words per minute for conversational speech
        estimated_duration = (word_count / 150) * 60
        
        # Adjust length if target duration specified
        if target_duration_seconds and abs(estimated_duration - target_duration_seconds) > 5:
            if estimated_duration > target_duration_seconds:
                # Text too long - suggest shortening
                target_words = int((target_duration_seconds / 60) * 150)
                modifications.append(f"Text may be too long. Consider shortening to ~{target_words} words")
            else:
                # Text too short - suggest elaboration
                modifications.append("Text may be too short for target duration. Consider adding detail")
        
        # Generate basic SSML markup
        ssml_markup = f'<speak>{optimized_text}</speak>'
        
        return {
            "success": True,
            "optimized_text": optimized_text,
            "estimated_duration_seconds": estimated_duration,
            "modifications_made": modifications,
            "ssml_markup": ssml_markup
        }
        
    except Exception as e:
        logger.error(f"Voice optimization error: {e}")
        return {
            "success": False,
            "error": str(e),
            "optimized_text": text,
            "modifications_made": []
        }

async def configure_voice(voice: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configure voice settings and validate voice availability.
    
    Args:
        voice: Voice name to configure
        settings: Voice settings to apply
        
    Returns:
        Dict with configuration results
    """
    try:
        # Available OpenAI voices
        available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        if voice not in available_voices:
            return {
                "success": False,
                "error": f"Voice '{voice}' not available",
                "voice": voice,
                "applied_settings": {},
                "available_voices": available_voices
            }
        
        # Validate and apply settings
        valid_settings = {}
        
        # Speed setting
        if "speed" in settings:
            speed = settings["speed"]
            if 0.25 <= speed <= 4.0:
                valid_settings["speed"] = speed
            else:
                logger.warning(f"Speed {speed} out of range (0.25-4.0), using 1.0")
                valid_settings["speed"] = 1.0
        
        # Format setting
        if "format" in settings:
            format_val = settings["format"]
            valid_formats = ["mp3", "opus", "aac", "flac"]
            if format_val in valid_formats:
                valid_settings["format"] = format_val
            else:
                logger.warning(f"Format {format_val} not supported, using mp3")
                valid_settings["format"] = "mp3"
        
        # Model setting
        if "model" in settings:
            model = settings["model"]
            valid_models = ["tts-1", "tts-1-hd"]
            if model in valid_models:
                valid_settings["model"] = model
            else:
                logger.warning(f"Model {model} not supported, using tts-1")
                valid_settings["model"] = "tts-1"
        
        return {
            "success": True,
            "voice": voice,
            "applied_settings": valid_settings,
            "available_voices": available_voices
        }
        
    except Exception as e:
        logger.error(f"Voice configuration error: {e}")
        return {
            "success": False,
            "error": str(e),
            "voice": voice,
            "applied_settings": {},
            "available_voices": []
        }

# === MCP Server Setup ===

# Initialize server
server = BaseMCPToolServer(
    name="realtime_voice",
    description="OpenAI Realtime Voice capabilities for LangSwarm including TTS, transcription, and voice optimization",
    local_mode=True
)

# Register tasks
server.add_task(
    name="text_to_speech",
    description="Convert text to speech using OpenAI TTS API",
    input_model=TextToSpeechInput,
    output_model=TextToSpeechOutput,
    handler=lambda **kwargs: asyncio.run(text_to_speech(**kwargs))
)

server.add_task(
    name="transcribe_audio", 
    description="Transcribe audio to text using OpenAI Whisper API",
    input_model=TranscribeAudioInput,
    output_model=TranscribeAudioOutput,
    handler=lambda **kwargs: asyncio.run(transcribe_audio(**kwargs))
)

server.add_task(
    name="optimize_voice_response",
    description="Optimize text for natural voice synthesis and speech",
    input_model=OptimizeVoiceResponseInput,
    output_model=OptimizeVoiceResponseOutput,
    handler=lambda **kwargs: asyncio.run(optimize_voice_response(**kwargs))
)

server.add_task(
    name="configure_voice",
    description="Configure voice settings and validate voice availability",
    input_model=VoiceConfigInput,
    output_model=VoiceConfigOutput,
    handler=lambda **kwargs: asyncio.run(configure_voice(**kwargs))
)

# Build app
app = server.build_app()

# === LangChain-Compatible Tool Class ===

class RealtimeVoiceMCPTool(MCPProtocolMixin, BaseTool):
    """
    Realtime Voice MCP tool for speech processing operations.
    
    Provides voice-specific capabilities including:
    - Text-to-speech generation
    - Audio transcription  
    - Voice response optimization
    - Voice configuration management
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True, 
                 mcp_url: str = None, **kwargs):
        
        description = kwargs.pop('description', "Advanced voice processing tool with TTS, transcription, and optimization")
        instruction = kwargs.pop('instruction', "Use this tool for voice-related operations including speech generation and audio processing")
        brief = kwargs.pop('brief', "Realtime Voice MCP Tool")
        
        # Add MCP server reference
        
        # Set MCP tool attributes
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
        
        # Initialize with BaseTool
        super().__init__(
            name=name or "RealtimeVoiceMCPTool",
            description=description,
            tool_id=identifier,
            **kwargs
        )
    
    # V2 Direct Method Calls - Expose operations as class methods
    async def text_to_speech(self, text: str, voice: str = "alloy", format: str = "mp3", **kwargs):
        """Convert text to speech audio"""
        return await text_to_speech(text=text, voice=voice, format=format, **kwargs)
    
    async def transcribe_audio(self, audio_data: str, language: str = None, **kwargs):
        """Transcribe audio to text"""
        return await transcribe_audio(audio_data=audio_data, language=language, **kwargs)
    
    async def optimize_voice_response(self, text: str, context: str = None, **kwargs):
        """Optimize text for voice delivery"""
        return await optimize_voice_response(text=text, context=context, **kwargs)
    
    async def configure_voice(self, settings: dict, **kwargs):
        """Configure voice settings"""
        return await configure_voice(settings=settings, **kwargs)
    
    def run(self, input_data=None):
        """Execute realtime voice MCP methods locally"""
        
        # Define method handlers
        method_handlers = {
            "text_to_speech": lambda **kwargs: asyncio.run(text_to_speech(**kwargs)),
            "transcribe_audio": lambda **kwargs: asyncio.run(transcribe_audio(**kwargs)),
            "optimize_voice_response": lambda **kwargs: asyncio.run(optimize_voice_response(**kwargs)),
            "configure_voice": lambda **kwargs: asyncio.run(configure_voice(**kwargs))
        }
        
        # Use BaseTool's common MCP input handler
        try:
            return self._handle_mcp_structured_input(input_data, method_handlers)
        except Exception as e:
            return f"Error executing realtime voice tool: {str(e)}"

if __name__ == "__main__":
    if server.local_mode:
        print("🎤 Realtime Voice MCP Tool server running in LOCAL MODE")
        print("Available methods:")
        for task_name in server.tasks.keys():
            print(f"  - {task_name}")
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)


