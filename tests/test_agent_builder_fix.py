
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock
from langswarm.core.agents.builder import AgentBuilder
from langswarm.tools.registry import IToolRegistry, ToolRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_agent_builder_custom_registry():
    print("🧪 Testing AgentBuilder with custom registry...")
    
    # Mock registry and tool
    mock_registry = MagicMock(spec=IToolRegistry)
    mock_tool = MagicMock()
    mock_tool.name = "mock_tool"
    mock_registry.get_tool.return_value = mock_tool
    
    # Mock agent
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    mock_agent.register_tool = AsyncMock() # Simulate async register_tool
    
    # Create builder with custom registry
    builder = AgentBuilder(name="test_agent", registry=mock_registry)
    
    # Manually trigger _auto_inject_tools (since we can't easily mock the full build process without providers)
    print("   Injecting tools...")
    await builder._auto_inject_tools(mock_agent, ["mock_tool"])
    
    # Verify
    mock_registry.get_tool.assert_called_with("mock_tool")
    mock_agent.register_tool.assert_called_with(mock_tool)
    print("✅ Custom registry used and tool injected via register_tool")

async def test_missing_tool_warning():
    print("\n🧪 Testing missing tool warning (no crash)...")
    
    mock_registry = MagicMock(spec=IToolRegistry)
    mock_registry.get_tool.return_value = None # Tool not found
    
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    
    builder = AgentBuilder(name="test_agent", registry=mock_registry)
    
    try:
        await builder._auto_inject_tools(mock_agent, ["missing_tool"])
        print("✅ No exception raised for missing tool")
    except Exception as e:
        print(f"❌ Exception raised: {e}")

async def main():
    await test_agent_builder_custom_registry()
    await test_missing_tool_warning()

if __name__ == "__main__":
    asyncio.run(main())
