import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append('/Users/alexanderekdahl/Docker/LangSwarm')

# Set dummy API key for initialization check
os.environ["MCP_DAYTONA_API_KEY"] = "dummy_key"
os.environ["MCP_DAYTONA_SERVER_URL"] = "http://localhost:3000"
os.environ["MCP_DAYTONA_TARGET"] = "local"

async def verify():
    print("Verifying Daytona Interpreter Integration...")
    
    try:
        from langswarm.tools.mcp.daytona_interpreter.main import DaytonaInterpreterMCPTool
        print("SUCCESS: DaytonaInterpreterMCPTool imported")
        
        tool = DaytonaInterpreterMCPTool("daytona_interpreter")
        print("SUCCESS: Tool instance created")
        
        # We can't fully initialize without a real API key and running server, 
        # but we can check if dependencies are loaded.
        
        if tool.interpreter is None:
            print("INFO: Interpreter not initialized yet (expected)")
            
        # Try to initialize with dummy config
        success = await tool.initialize({})
        if success:
            print("SUCCESS: Tool initialized (mocked)")
        else:
            print("INFO: Tool initialization failed (likely due to connection check)")
            
    except ImportError as e:
        print(f"FAILURE: ImportError: {e}")
    except Exception as e:
        print(f"FAILURE: Exception: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
