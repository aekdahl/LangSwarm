
import inspect
import sys
import os
from unittest.mock import MagicMock

# Mock daytona module before import
sys.modules["daytona"] = MagicMock()

from langswarm.tools.mcp.daytona_environment.main import DaytonaEnvironmentMCPTool, DaytonaEnvironmentManager

def test_daytona_tool_fixes():
    print("🧪 Testing DaytonaEnvironmentMCPTool fixes...")
    
    # Instantiate tool
    tool = DaytonaEnvironmentMCPTool(identifier="daytona_env", local_mode=True)
    
    # 1. Verify method registration
    print("\n1. Verifying method registration...")
    methods = tool.metadata.methods
    print(f"   Registered methods: {list(methods.keys())}")
    
    expected_methods = [
        "create_sandbox", "execute_code", "execute_shell", 
        "file_operation", "git_operation", "list_sandboxes", 
        "delete_sandbox", "get_sandbox_info"
    ]
    
    missing = [m for m in expected_methods if m not in methods]
    
    if not missing:
        print("✅ All expected methods are registered.")
    else:
        print(f"❌ Missing methods: {missing}")
        
    # 2. Verify create_sandbox signature
    print("\n2. Verifying create_sandbox signature...")
    sig = inspect.signature(tool.create_sandbox)
    print(f"   Signature: {sig}")
    
    name_param = sig.parameters.get("name")
    if name_param:
        if name_param.default is None:
            print("✅ 'name' parameter is optional (default=None).")
        else:
            print(f"❌ 'name' parameter is NOT optional (default={name_param.default}).")
    else:
        print("❌ 'name' parameter not found.")

def test_sandbox_lookup():
    print("\n🧪 Testing _get_sandbox lookup logic...")
    
    # Mock DaytonaEnvironmentManager
    manager = DaytonaEnvironmentManager(api_key="mock_key")
    manager._client = MagicMock()
    
    # Mock sandboxes
    sandbox1 = MagicMock()
    sandbox1.id = "uuid-123"
    sandbox1.name = "sandbox-1"
    
    sandbox2 = MagicMock()
    sandbox2.id = "uuid-456"
    sandbox2.name = "my-custom-sandbox"
    
    manager._client.list.return_value = [sandbox1, sandbox2]
    
    # Test lookup by ID
    print("   Looking up by ID 'uuid-123'...")
    result1 = manager._get_sandbox("uuid-123")
    if result1 == sandbox1:
        print("✅ Found sandbox by ID.")
    else:
        print(f"❌ Failed to find sandbox by ID. Got: {result1}")
        
    # Test lookup by Name
    print("   Looking up by Name 'my-custom-sandbox'...")
    result2 = manager._get_sandbox("my-custom-sandbox")
    if result2 == sandbox2:
        print("✅ Found sandbox by Name.")
    else:
        print(f"❌ Failed to find sandbox by Name. Got: {result2}")
        
    # Test missing
    print("   Looking up missing sandbox 'missing'...")
    try:
        manager._get_sandbox("missing")
        print("❌ Should have raised ValueError for missing sandbox.")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"⚠️ Raised unexpected exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    try:
        test_daytona_tool_fixes()
        test_sandbox_lookup()
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
