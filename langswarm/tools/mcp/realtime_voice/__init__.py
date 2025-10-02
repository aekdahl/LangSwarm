# langswarm/mcp/tools/realtime_voice/__init__.py

"""
OpenAI Realtime Voice MCP Tool

Provides voice-specific capabilities for LangSwarm including:
- Text-to-speech generation  
- Audio transcription
- Voice response optimization
- Speech configuration management
"""

from .main import RealtimeVoiceMCPTool, server

__all__ = ["RealtimeVoiceMCPTool", "server"]


