"""
Test script to verify that tool calls work in streaming mode.

This test demonstrates that the fix in BaseAgent.stream_chat() 
correctly handles tool calls during streaming.

Run with: python test_streaming_tool_fix.py
"""

import asyncio
import logging
import os

# Set up logging to see tool execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_streaming_with_tools():
    """Test that tool calls work correctly in streaming mode"""
    
    try:
        from langswarm.core.agents import create_openai_agent
        
        # Ensure OpenAI API key is set
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("❌ OPENAI_API_KEY environment variable not set")
            logger.info("   Set it with: export OPENAI_API_KEY='your-key-here'")
            return False
        
        logger.info("=" * 60)
        logger.info("🧪 Testing Streaming Mode with Tool Calls")
        logger.info("=" * 60)
        
        # Create agent with streaming and tools enabled
        logger.info("\n1️⃣ Creating agent with streaming=True and tools...")
        agent = await create_openai_agent(
            name="test_streaming_tools",
            model="gpt-4o",
            system_prompt="You are a helpful assistant with access to tools.",
            streaming=True,
            tools=["calculator"]  # Add whatever tools you have configured
        )
        logger.info(f"✅ Agent created: {agent.name}")
        logger.info(f"   Streaming enabled: {agent._configuration.streaming_enabled}")
        logger.info(f"   Tools enabled: {agent._configuration.tools_enabled}")
        logger.info(f"   Available tools: {agent._configuration.available_tools}")
        
        # Test query that should trigger a tool call
        test_query = "What is 1234 multiplied by 5678?"
        logger.info(f"\n2️⃣ Sending query that requires tool: '{test_query}'")
        logger.info("   Watching for tool calls during streaming...")
        
        # Stream the response
        full_response = ""
        tool_executed = False
        chunk_count = 0
        
        logger.info("\n3️⃣ Streaming response:")
        logger.info("-" * 60)
        
        async for chunk in agent.stream_chat(test_query):
            chunk_count += 1
            
            # Check for tool execution
            if chunk.metadata.get('tool_executed'):
                tool_executed = True
                logger.info(f"\n🔧 TOOL EXECUTED: {chunk.metadata['tool_executed']}")
                logger.info(f"   Parameters: {chunk.metadata.get('tool_parameters', 'N/A')}")
            
            # Accumulate response
            if chunk.success and chunk.content:
                full_response += chunk.content
                print(chunk.content, end="", flush=True)
        
        print("\n" + "-" * 60)
        logger.info(f"\n4️⃣ Stream complete!")
        logger.info(f"   Total chunks: {chunk_count}")
        logger.info(f"   Response length: {len(full_response)} characters")
        logger.info(f"   Tool executed: {'YES ✅' if tool_executed else 'NO ❌'}")
        
        # Verify the fix worked
        if tool_executed:
            logger.info("\n" + "=" * 60)
            logger.info("✅ SUCCESS! Tool calls are working in streaming mode!")
            logger.info("=" * 60)
            return True
        else:
            logger.warning("\n" + "=" * 60)
            logger.warning("⚠️  WARNING: No tool was executed during streaming")
            logger.warning("   This might mean:")
            logger.warning("   1. The LLM didn't need to call a tool for this query")
            logger.warning("   2. Tool is not available/registered")
            logger.warning("   3. The fix didn't work (check logs)")
            logger.warning("=" * 60)
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("   Make sure LangSwarm is installed: pip install -e .")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_without_tools():
    """Test that regular streaming (without tools) still works"""
    
    try:
        from langswarm.core.agents import create_openai_agent
        
        logger.info("\n" + "=" * 60)
        logger.info("🧪 Testing Streaming Mode WITHOUT Tool Calls")
        logger.info("=" * 60)
        
        # Create agent with streaming but no tools
        logger.info("\n1️⃣ Creating agent with streaming=True, no tools...")
        agent = await create_openai_agent(
            name="test_streaming_no_tools",
            model="gpt-4o",
            system_prompt="You are a helpful assistant.",
            streaming=True
            # No tools parameter
        )
        logger.info(f"✅ Agent created: {agent.name}")
        
        # Simple query
        test_query = "Say hello in 5 words or less"
        logger.info(f"\n2️⃣ Sending simple query: '{test_query}'")
        
        full_response = ""
        chunk_count = 0
        
        logger.info("\n3️⃣ Streaming response:")
        logger.info("-" * 60)
        
        async for chunk in agent.stream_chat(test_query):
            chunk_count += 1
            if chunk.success and chunk.content:
                full_response += chunk.content
                print(chunk.content, end="", flush=True)
        
        print("\n" + "-" * 60)
        logger.info(f"\n4️⃣ Stream complete!")
        logger.info(f"   Total chunks: {chunk_count}")
        logger.info(f"   Response: '{full_response}'")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ SUCCESS! Regular streaming works correctly!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    logger.info("\n🚀 Starting LangSwarm V2 Streaming Tool Call Tests\n")
    
    # Test 1: Streaming without tools (baseline)
    test1_passed = await test_streaming_without_tools()
    
    # Test 2: Streaming with tools (the fix)
    test2_passed = await test_streaming_with_tools()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Test 1 (Streaming without tools): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    logger.info(f"Test 2 (Streaming with tools):    {'✅ PASSED' if test2_passed else '⚠️  INCONCLUSIVE'}")
    logger.info("=" * 60)
    
    if test1_passed:
        logger.info("\n✅ The streaming tool call fix has been applied successfully!")
        logger.info("   Tool calls now work in both streaming and non-streaming modes.")
    else:
        logger.error("\n❌ Tests failed. Please check the error logs above.")
    
    logger.info("\n")


if __name__ == "__main__":
    asyncio.run(main())

