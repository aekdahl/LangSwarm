import asyncio
import json
from unittest.mock import MagicMock, AsyncMock
import logging
from langswarm.core.agents.providers.openai import OpenAIProvider
from langswarm.core.agents.base import AgentConfiguration
from langswarm.core.agents.interfaces import ProviderType

# Configure logging
logging.basicConfig(level=logging.INFO)

# Mock Tool Registry
class MockToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def get_tool(self, name):
        return self.tools.get(name)

# Mock Tool with methods
class MockToolWithMethods:
    def __init__(self):
        self.metadata = MagicMock()
        self.metadata.name = "complex_tool"
        self.metadata.description = "A complex tool"
        
        # Define methods
        method_schema = MagicMock()
        method_schema.description = "Method 1"
        method_schema.parameters = {}
        method_schema.required = []
        
        self.metadata.methods = {
            "method1": method_schema,
            "method2": method_schema
        }

async def run_reproduction():
    print("🚀 Starting tool duplication reproduction script...")
    
    # Mock dependencies
    import sys
    sys.modules['openai'] = MagicMock()
    sys.modules['langswarm.tools.registry'] = MagicMock()
    
    # Setup registry mock
    mock_registry = MockToolRegistry()
    mock_tool = MockToolWithMethods()
    mock_registry.tools["complex_tool"] = mock_tool
    
    # Setup registry mock module
    mock_registry_module = MagicMock()
    mock_registry_module.ToolRegistry.return_value = mock_registry
    sys.modules['langswarm.tools.registry'] = mock_registry_module
    
    # No need to patch, just run
    provider = OpenAIProvider()
    
    # Build definitions
    print("Building tool definitions...")
    definitions = provider._build_tool_definitions(["complex_tool"])
        
    print(f"Generated {len(definitions)} definitions:")
    found_base_tool = False
    found_flattened_tools = 0
    
    for tool_def in definitions:
        name = tool_def["function"]["name"]
        print(f"  - {name}")
        
        if name == "complex_tool":
            found_base_tool = True
        elif name.startswith("complex_tool__"):
            found_flattened_tools += 1
    
    # Verification
    if found_base_tool and found_flattened_tools > 0:
        print("\n❌ BUG REPRODUCED: Found both base tool AND flattened methods!")
        print("The LLM will be confused by the duplicate base tool definition.")
    elif found_flattened_tools > 0 and not found_base_tool:
        print("\n✅ Verification PASSED: Only flattened methods found (correct behavior).")
    else:
        print("\n⚠️ Unexpected result.")

if __name__ == "__main__":
    import unittest
    asyncio.run(run_reproduction())
