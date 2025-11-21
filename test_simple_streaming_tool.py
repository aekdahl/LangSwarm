"""
Simple test to verify tool calls in streaming mode with actual OpenAI API
"""

import asyncio
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_streaming_tool_calls():
    """Test that tool calls actually work in streaming"""
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Set OPENAI_API_KEY environment variable first")
        return
    
    print("=" * 70)
    print("Testing Streaming + Tool Calls")
    print("=" * 70)
    
    try:
        from langswarm.core.agents import create_openai_agent
        from langswarm.tools.registry import ToolRegistry
        
        # Check what tools are available
        registry = ToolRegistry()
        registry.auto_populate_with_mcp_tools()
        tool_ids = list(registry._tools.keys())
        
        print(f"\n✅ Available tools: {tool_ids[:3]}...")  # Show first 3
        
        if not tool_ids:
            print("❌ No tools available!")
            return
        
        # Use bigquery_vector_search if available, otherwise first tool
        test_tool = "bigquery_vector_search" if "bigquery_vector_search" in tool_ids else tool_ids[0]
        print(f"\n🔧 Creating agent with tool: '{test_tool}'")
        
        # Create agent with streaming and tools
        agent = await create_openai_agent(
            name="test_agent",
            model="gpt-4o",
            system_prompt=f"You are a helpful assistant with access to {test_tool}. Use it when appropriate.",
            streaming=True,
            tools=[test_tool]
        )
        
        print(f"✅ Agent created")
        print(f"   - Streaming: {agent._configuration.streaming_enabled}")
        print(f"   - Tools enabled: {agent._configuration.tools_enabled}")
        print(f"   - Available tools: {agent._configuration.available_tools}")
        
        if not agent._configuration.tools_enabled:
            print("\n❌ PROBLEM: Tools not enabled in config!")
            return
        
        # Test with a query
        if test_tool == "bigquery_vector_search":
            query = "Search the BigQuery database for documents about Python programming"
        else:
            query = "Help me with something that requires using your tools"
        
        print(f"\n📨 Query: {query}")
        print("\n📡 Streaming response:")
        print("-" * 70)
        
        tool_call_detected = False
        tool_executed = False
        chunk_count = 0
        
        async for chunk in agent.stream_chat(query):
            chunk_count += 1
            
            # Print content
            if chunk.success and chunk.content:
                print(chunk.content, end="", flush=True)
            
            # Check for tool calls
            if chunk.message and hasattr(chunk.message, 'tool_calls') and chunk.message.tool_calls:
                tool_call_detected = True
                print(f"\n\n🔧 TOOL CALL DETECTED! (chunk #{chunk_count})")
                for tc in chunk.message.tool_calls:
                    if hasattr(tc, 'function'):
                        print(f"   Function: {tc.function.name}")
            
            # Check for tool execution
            if chunk.metadata.get('tool_executed'):
                tool_executed = True
                print(f"\n\n✅ TOOL EXECUTED: {chunk.metadata['tool_executed']}")
        
        print("\n" + "-" * 70)
        print(f"\n📊 Results:")
        print(f"   - Total chunks: {chunk_count}")
        print(f"   - Tool call detected: {'YES ✅' if tool_call_detected else 'NO ❌'}")
        print(f"   - Tool executed: {'YES ✅' if tool_executed else 'NO ❌'}")
        
        if tool_call_detected and not tool_executed:
            print("\n❌ PROBLEM: Tool call was detected but NOT executed!")
            print("   The fix in stream_chat() is not working correctly")
        elif tool_executed:
            print("\n✅ SUCCESS: Tool calls working in streaming mode!")
        elif not tool_call_detected:
            print("\n⚠️  No tool call was made by the LLM")
            print("   This might mean the query didn't require the tool")
            print("   Or the tool wasn't sent to OpenAI properly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_streaming_tool_calls())

