#!/usr/bin/env python3
"""
Demo: OpenAI Realtime API Integration with LangSwarm

This demo shows how to use LangSwarm with OpenAI's Realtime API for
voice-enabled conversations with full MCP tool integration.

Requirements:
- pip install openai websockets
- export OPENAI_API_KEY=your_key_here
- Microphone access for full demo
"""

import asyncio
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_basic_realtime():
    """Demo 1: Basic realtime voice conversation"""
    print("\n🎤 Demo 1: Basic Realtime Voice Conversation")
    print("=" * 50)
    
    try:
        from langswarm.core.wrappers.realtime_wrapper import create_realtime_agent
        
        # Create voice agent
        agent = create_realtime_agent(
            name="demo_assistant",
            voice="alloy",
            system_prompt="You are a helpful demo assistant. Keep responses brief and friendly.",
            memory_enabled=True
        )
        
        print(f"✅ Created realtime agent: {agent.name}")
        print(f"📊 Agent status: {agent.get_realtime_status()}")
        
        # Simulate text-to-voice conversation
        print("\n📝 Starting text conversation (simulated voice)...")
        
        # Send text message through realtime API
        conversation_count = 0
        async for event in agent.chat_realtime("Hello! Tell me a short joke."):
            conversation_count += 1
            
            if event["type"] == "text_chunk":
                print(f"🤖 Assistant: {event['data']}", end="", flush=True)
            elif event["type"] == "transcription":
                print(f"\n👤 You said: {event['data']}")
            elif event["type"] == "audio_chunk":
                print("🔊 [Audio chunk received]", end="")
            elif event["type"] == "error":
                print(f"\n❌ Error: {event['data']}")
                break
            
            # Limit demo length
            if conversation_count > 20:
                print(f"\n✅ Demo conversation completed ({conversation_count} events)")
                break
        
        # Clean up
        await agent.close_realtime_session()
        print("\n🏁 Basic demo completed successfully!")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Run: pip install openai websockets")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Basic demo error: {e}")

async def demo_mcp_tools_integration():
    """Demo 2: MCP tools in realtime conversations"""
    print("\n🛠️ Demo 2: MCP Tools in Realtime Conversations")
    print("=" * 50)
    
    try:
        from langswarm.core.wrappers.realtime_wrapper import create_realtime_agent
        from langswarm.mcp.tools.filesystem.main import FilesystemMCPTool
        from langswarm.mcp.tools.realtime_voice.main import RealtimeVoiceMCPTool
        
        # Create agent with tools
        agent = create_realtime_agent(
            name="tool_assistant", 
            voice="nova",
            system_prompt="You are an assistant with file system and voice processing capabilities.",
            memory_enabled=True
        )
        
        # Add MCP tools
        agent.tool_registry = agent.tool_registry or {}
        agent.tool_registry["filesystem"] = FilesystemMCPTool("fs_tool")
        agent.tool_registry["voice"] = RealtimeVoiceMCPTool("voice_tool")
        
        print(f"✅ Agent created with {len(agent.tool_registry)} tools:")
        for tool_name in agent.tool_registry.keys():
            print(f"   - {tool_name}")
        
        # Reconfigure with tools
        agent.configure_realtime({
            "voice": "nova",
            "modalities": ["text", "audio"],
            "instructions": "You have access to filesystem and voice processing tools. Use them when helpful."
        })
        
        print(f"📊 Realtime status: {agent.get_realtime_status()}")
        
        # Test tool integration
        print("\n🔍 Testing tool integration...")
        tool_test_count = 0
        
        async for event in agent.chat_realtime("What files are in the current directory? Also optimize this text for speech: 'Hello, world!'"):
            tool_test_count += 1
            
            if event["type"] == "function_call_result":
                print(f"\n🔧 Tool executed: {event['data']['success']}")
                if 'result' in event['data']:
                    result = event['data']['result']
                    if isinstance(result, dict) and len(str(result)) > 100:
                        print(f"🔧 Tool result: [Large result with {len(str(result))} characters]")
                    else:
                        print(f"🔧 Tool result: {result}")
            elif event["type"] == "text_chunk":
                print(f"🤖 {event['data']}", end="", flush=True)
            elif event["type"] == "error":
                print(f"\n❌ Error: {event['data']}")
                break
            
            # Limit demo
            if tool_test_count > 30:
                print(f"\n✅ Tool integration demo completed ({tool_test_count} events)")
                break
        
        await agent.close_realtime_session()
        print("\n🏁 MCP tools demo completed successfully!")
        
    except Exception as e:
        print(f"❌ MCP tools demo failed: {e}")
        logger.error(f"MCP demo error: {e}")

async def demo_voice_processing():
    """Demo 3: Voice processing capabilities"""
    print("\n🎵 Demo 3: Voice Processing Capabilities")
    print("=" * 50)
    
    try:
        from langswarm.mcp.tools.realtime_voice.main import RealtimeVoiceMCPTool
        
        # Create voice processing tool
        voice_tool = RealtimeVoiceMCPTool("demo_voice")
        
        print("✅ Voice processing tool created")
        
        # Test 1: Text optimization for speech
        print("\n📝 Testing text optimization for speech...")
        optimize_result = voice_tool.run({
            "method": "optimize_voice_response",
            "params": {
                "text": "Hello! Here's your data: item1, item2, item3. Dr. Smith said it's ready at 3 p.m.",
                "speaking_style": "conversational",
                "include_pauses": True,
                "optimize_for_clarity": True
            }
        })
        
        print(f"Original: Hello! Here's your data: item1, item2, item3. Dr. Smith said it's ready at 3 p.m.")
        print(f"Optimized: {optimize_result.get('optimized_text', 'Error')}")
        print(f"Modifications: {optimize_result.get('modifications_made', [])}")
        
        # Test 2: Voice configuration
        print("\n⚙️ Testing voice configuration...")
        config_result = voice_tool.run({
            "method": "configure_voice",
            "params": {
                "voice": "alloy",
                "settings": {
                    "speed": 1.2,
                    "format": "mp3",
                    "model": "tts-1"
                }
            }
        })
        
        print(f"Voice config success: {config_result.get('success', False)}")
        print(f"Applied settings: {config_result.get('applied_settings', {})}")
        print(f"Available voices: {config_result.get('available_voices', [])}")
        
        # Test 3: TTS (requires API key)
        if os.getenv("OPENAI_API_KEY"):
            print("\n🔊 Testing text-to-speech...")
            tts_result = voice_tool.run({
                "method": "text_to_speech",
                "params": {
                    "text": "Hello from LangSwarm! This is a test of the text-to-speech integration.",
                    "voice": "alloy",
                    "speed": 1.0,
                    "format": "mp3"
                }
            })
            
            print(f"TTS success: {tts_result.get('success', False)}")
            if tts_result.get('success'):
                print(f"Audio duration: {tts_result.get('duration_ms', 0)}ms")
                print(f"Audio format: {tts_result.get('format')}")
                audio_size = len(tts_result.get('audio_base64', ''))
                print(f"Audio data size: {audio_size} characters (base64)")
            else:
                print(f"TTS error: {tts_result.get('error', 'Unknown error')}")
        else:
            print("\n⚠️ Skipping TTS test (OPENAI_API_KEY not set)")
        
        print("\n🏁 Voice processing demo completed!")
        
    except Exception as e:
        print(f"❌ Voice processing demo failed: {e}")
        logger.error(f"Voice processing error: {e}")

async def demo_webrtc_setup():
    """Demo 4: WebRTC configuration for browsers"""
    print("\n🌐 Demo 4: WebRTC Browser Configuration")
    print("=" * 50)
    
    try:
        from langswarm.core.wrappers.webrtc_handler import WebRTCRealtimeHandler
        from langswarm.core.wrappers.realtime_wrapper import create_realtime_agent
        
        # Create agent for WebRTC
        agent = create_realtime_agent(
            name="browser_assistant",
            voice="echo", 
            system_prompt="You are a browser-based voice assistant."
        )
        
        # Set up WebRTC handler
        webrtc = WebRTCRealtimeHandler(agent_wrapper=agent)
        webrtc.configure_session({
            "voice": "echo",
            "modalities": ["text", "audio"],
            "instructions": "You are a helpful browser-based assistant."
        })
        
        print("✅ WebRTC handler configured")
        
        # Generate client configuration
        if os.getenv("OPENAI_API_KEY"):
            client_config = webrtc.get_client_connection_config(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            print(f"✅ Client config generated with {len(client_config)} settings")
            print(f"   Voice: {client_config.get('voice')}")
            print(f"   Tools: {len(client_config.get('tools', []))} available")
        else:
            print("⚠️ Skipping client config (OPENAI_API_KEY not set)")
        
        # Generate example HTML
        html_example = webrtc.get_html_example("http://localhost:8000")
        html_size = len(html_example)
        print(f"✅ Generated HTML example ({html_size} characters)")
        print("   Contains: JavaScript client, tool integration, audio handling")
        
        # Show JavaScript client code sample
        js_code = webrtc.get_javascript_client_code()
        js_lines = js_code.count('\n')
        print(f"✅ Generated JavaScript client ({js_lines} lines)")
        print("   Features: WebRTC connection, tool calls, audio streaming")
        
        print("\n📋 To use WebRTC integration:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Start LangSwarm server with WebRTC handler")
        print("3. Serve generated HTML to browsers")
        print("4. Users can connect directly to OpenAI with tool access")
        
        print("\n🏁 WebRTC demo completed!")
        
    except Exception as e:
        print(f"❌ WebRTC demo failed: {e}")
        logger.error(f"WebRTC error: {e}")

async def main():
    """Run all demos"""
    print("🚀 LangSwarm OpenAI Realtime API Integration Demo")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    print("\n🔍 Checking prerequisites...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OPENAI_API_KEY is set")
    else:
        print("⚠️ OPENAI_API_KEY not set (some features will be limited)")
    
    try:
        import websockets
        print("✅ websockets library available")
    except ImportError:
        print("❌ websockets library missing (pip install websockets)")
    
    try:
        import openai
        print("✅ openai library available")
    except ImportError:
        print("❌ openai library missing (pip install openai)")
    
    # Run demos
    demos = [
        ("Basic Realtime Conversation", demo_basic_realtime),
        ("MCP Tools Integration", demo_mcp_tools_integration), 
        ("Voice Processing", demo_voice_processing),
        ("WebRTC Browser Setup", demo_webrtc_setup)
    ]
    
    for demo_name, demo_func in demos:
        try:
            await demo_func()
        except KeyboardInterrupt:
            print(f"\n⏹️ Demo '{demo_name}' interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Demo '{demo_name}' failed: {e}")
            logger.error(f"Demo {demo_name} failed", exc_info=True)
        
        print("\n" + "─" * 60)
    
    print(f"\n🎉 All demos completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📚 Next steps:")
    print("1. Set OPENAI_API_KEY for full functionality")
    print("2. Install missing dependencies (openai, websockets)")
    print("3. Check docs/simplification/05-openai-realtime-api-integration.md")
    print("4. Try the WebRTC browser example")

if __name__ == "__main__":
    asyncio.run(main())


