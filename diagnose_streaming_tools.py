"""
Diagnostic Script: Debug Why Tool Calls Aren't Working in Streaming Mode

This script will help identify where the problem is occurring.
"""

import asyncio
import logging
import os
import json

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def diagnose_tool_setup():
    """Diagnose tool configuration and availability"""
    
    print("\n" + "=" * 70)
    print("🔍 DIAGNOSTIC 1: Tool Registry Status")
    print("=" * 70)
    
    try:
        from langswarm.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        print(f"✅ Tool Registry loaded")
        print(f"   Registry type: {type(registry).__name__}")
        
        # Check if auto-populate works
        print(f"\n📦 Attempting to auto-populate MCP tools...")
        try:
            registry.auto_populate_with_mcp_tools()
            print(f"✅ Auto-populate completed")
        except Exception as e:
            print(f"⚠️  Auto-populate failed: {e}")
        
        # List available tools
        available_tools = registry.list_tools()
        print(f"\n📋 Available tools in registry: {len(available_tools)}")
        for tool_name in available_tools:
            print(f"   - {tool_name}")
        
        if not available_tools:
            print(f"\n❌ NO TOOLS FOUND IN REGISTRY!")
            print(f"   This is the problem - tools must be registered first!")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import ToolRegistry: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking tool registry: {e}")
        import traceback
        traceback.print_exc()
        return False


async def diagnose_agent_config():
    """Diagnose agent configuration"""
    
    print("\n" + "=" * 70)
    print("🔍 DIAGNOSTIC 2: Agent Configuration")
    print("=" * 70)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set - some checks will be skipped")
        print("   Set with: export OPENAI_API_KEY='your-key'")
        return False
    
    try:
        from langswarm.core.agents import create_openai_agent
        from langswarm.tools.registry import ToolRegistry
        
        # Get available tools
        registry = ToolRegistry()
        available_tools = registry.list_tools()
        
        if not available_tools:
            print("❌ No tools available - cannot test agent with tools")
            return False
        
        # Use first available tool for testing
        test_tool = available_tools[0]
        print(f"\n🔧 Creating agent with tool: '{test_tool}'")
        
        # Create agent with streaming and tools
        agent = await create_openai_agent(
            name="diagnostic_agent",
            model="gpt-4o",
            system_prompt="You are a helpful assistant.",
            streaming=True,
            tools=[test_tool]
        )
        
        print(f"✅ Agent created: {agent.name}")
        
        # Check configuration
        config = agent._configuration
        print(f"\n📊 Agent Configuration:")
        print(f"   - Model: {config.model}")
        print(f"   - Provider: {config.provider}")
        print(f"   - Streaming enabled: {config.streaming_enabled}")
        print(f"   - Tools enabled: {config.tools_enabled}")
        print(f"   - Available tools: {config.available_tools}")
        print(f"   - Tool choice: {config.tool_choice}")
        print(f"   - Max tool iterations: {config.max_tool_iterations}")
        
        # Critical checks
        if not config.streaming_enabled:
            print(f"\n❌ PROBLEM: Streaming is NOT enabled!")
            return False
        
        if not config.tools_enabled:
            print(f"\n❌ PROBLEM: Tools are NOT enabled in config!")
            print(f"   This means tools won't be sent to OpenAI API")
            return False
        
        if not config.available_tools:
            print(f"\n❌ PROBLEM: No tools in available_tools list!")
            return False
        
        print(f"\n✅ Configuration looks correct!")
        return agent
        
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def diagnose_api_params(agent):
    """Diagnose OpenAI API parameters"""
    
    print("\n" + "=" * 70)
    print("🔍 DIAGNOSTIC 3: OpenAI API Parameters")
    print("=" * 70)
    
    try:
        from langswarm.core.agents.interfaces import AgentMessage
        from langswarm.core.agents.base import AgentSession
        
        # Create a mock session
        session = AgentSession()
        test_message = AgentMessage(role="user", content="Test message")
        
        # Get the provider
        provider = agent._provider
        print(f"✅ Provider: {type(provider).__name__}")
        
        # Build messages
        messages = await provider._build_openai_messages(session, test_message, agent._configuration)
        print(f"✅ Built {len(messages)} message(s)")
        
        # Build API parameters
        api_params = provider._build_api_params(agent._configuration, messages, stream=True)
        
        print(f"\n📋 OpenAI API Parameters:")
        print(f"   - Model: {api_params.get('model')}")
        print(f"   - Stream: {api_params.get('stream')}")
        print(f"   - Temperature: {api_params.get('temperature')}")
        print(f"   - Max tokens: {api_params.get('max_tokens')}")
        
        # CRITICAL CHECK: Are tools included?
        if 'tools' in api_params:
            tools = api_params['tools']
            print(f"   - Tools: {len(tools)} tool(s) defined")
            print(f"\n✅ TOOLS ARE INCLUDED IN API PARAMS!")
            print(f"\n📦 Tool Definitions Being Sent to OpenAI:")
            for i, tool in enumerate(tools, 1):
                func = tool.get('function', {})
                print(f"   {i}. {func.get('name', 'unnamed')}")
                print(f"      Description: {func.get('description', 'N/A')[:60]}...")
            return True
        else:
            print(f"\n❌ CRITICAL PROBLEM: Tools NOT included in API parameters!")
            print(f"   This means OpenAI will never know about your tools!")
            print(f"\n   API params keys: {list(api_params.keys())}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking API params: {e}")
        import traceback
        traceback.print_exc()
        return False


async def diagnose_streaming_flow(agent):
    """Test actual streaming with detailed logging"""
    
    print("\n" + "=" * 70)
    print("🔍 DIAGNOSTIC 4: Actual Streaming Test")
    print("=" * 70)
    
    # Use a query that should trigger tool use
    test_queries = [
        "What is 2 + 2?",  # Simple, might trigger calculator
        "Calculate 123 * 456",  # More explicit
        "Search for information about Python"  # Might trigger search
    ]
    
    query = test_queries[1]  # Use calculation query
    print(f"\n🧪 Test Query: '{query}'")
    print(f"   (This query should trigger a tool call)")
    
    try:
        chunk_count = 0
        content_chunks = []
        tool_calls_detected = False
        final_chunk = None
        
        print(f"\n📡 Streaming response:")
        print("-" * 70)
        
        async for chunk in agent.stream_chat(query):
            chunk_count += 1
            
            # Store final chunk
            final_chunk = chunk
            
            # Check for content
            if chunk.success and chunk.content:
                content_chunks.append(chunk.content)
                print(chunk.content, end="", flush=True)
            
            # Check for tool calls in metadata
            if chunk.message and hasattr(chunk.message, 'tool_calls') and chunk.message.tool_calls:
                tool_calls_detected = True
                print(f"\n\n🔧 TOOL CALLS DETECTED IN CHUNK #{chunk_count}!")
                print(f"   Number of tool calls: {len(chunk.message.tool_calls)}")
                for tc in chunk.message.tool_calls:
                    if hasattr(tc, 'function'):
                        print(f"   - Function: {tc.function.name}")
                        print(f"     Arguments: {tc.function.arguments[:100]}")
            
            # Check metadata
            if chunk.metadata.get('stream_complete'):
                print(f"\n\n✅ Stream marked as complete")
            
            if chunk.metadata.get('tool_executed'):
                print(f"\n🎯 TOOL EXECUTED: {chunk.metadata['tool_executed']}")
        
        print("\n" + "-" * 70)
        print(f"\n📊 Stream Results:")
        print(f"   - Total chunks: {chunk_count}")
        print(f"   - Content chunks: {len(content_chunks)}")
        print(f"   - Tool calls detected during stream: {'YES ✅' if tool_calls_detected else 'NO ❌'}")
        
        # Check final chunk
        if final_chunk:
            print(f"\n🔍 Final Chunk Analysis:")
            print(f"   - Has message: {final_chunk.message is not None}")
            if final_chunk.message:
                has_tool_calls = hasattr(final_chunk.message, 'tool_calls') and final_chunk.message.tool_calls
                print(f"   - Message has tool_calls: {has_tool_calls}")
                if has_tool_calls:
                    print(f"   - Number of tool calls: {len(final_chunk.message.tool_calls)}")
                    print(f"\n⚠️  TOOL CALLS FOUND BUT NOT EXECUTED!")
                    print(f"   This means the stream_chat fix didn't trigger!")
        
        # Final verdict
        if tool_calls_detected:
            print(f"\n✅ Tools are being sent to OpenAI (good!)")
            print(f"❌ BUT tool execution may not be happening (check logs above)")
        else:
            print(f"\n❌ No tool calls detected in entire stream")
            print(f"   Possible reasons:")
            print(f"   1. LLM chose not to use tools for this query")
            print(f"   2. Tools not properly sent to OpenAI API")
            print(f"   3. Tool definitions don't match query type")
        
    except Exception as e:
        print(f"\n❌ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all diagnostics"""
    
    print("\n" + "=" * 70)
    print("🚀 LangSwarm V2 Streaming Tool Call Diagnostics")
    print("=" * 70)
    
    # Step 1: Check tool registry
    tools_ok = await diagnose_tool_setup()
    
    if not tools_ok:
        print("\n" + "=" * 70)
        print("❌ STOP: Tool registry is empty or broken")
        print("=" * 70)
        print("\n💡 You need to:")
        print("   1. Register tools in the ToolRegistry")
        print("   2. Or ensure MCP tools are available")
        print("   3. Tools must exist BEFORE creating the agent")
        return
    
    # Step 2: Check agent configuration
    agent = await diagnose_agent_config()
    
    if not agent:
        print("\n" + "=" * 70)
        print("❌ STOP: Agent configuration failed")
        print("=" * 70)
        return
    
    # Step 3: Check API parameters
    api_ok = await diagnose_api_params(agent)
    
    if not api_ok:
        print("\n" + "=" * 70)
        print("❌ CRITICAL: Tools not included in OpenAI API calls!")
        print("=" * 70)
        print("\n💡 This is the root cause - fix the tool configuration")
        return
    
    # Step 4: Test actual streaming
    await diagnose_streaming_flow(agent)
    
    # Final summary
    print("\n" + "=" * 70)
    print("📋 DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print("\nReview the output above to identify the issue.")
    print("Look for ❌ markers indicating problems.")


if __name__ == "__main__":
    asyncio.run(main())

