import sys
import os

# Add the project root to the python path
sys.path.append('/Users/alexanderekdahl/Docker/LangSwarm')

try:
    from langswarm.tools.mcp.daytona_self_hosted.main import DaytonaSelfHostedMCPTool
    print("SUCCESS: DaytonaSelfHostedMCPTool imported successfully")
    
    # Check inheritance
    try:
        from langswarm.tools.base import BaseTool
    except ImportError:
        from langswarm.synapse.tools.base import BaseTool
        
    if issubclass(DaytonaSelfHostedMCPTool, BaseTool):
        print("SUCCESS: DaytonaSelfHostedMCPTool inherits from BaseTool")
    else:
        print("FAILURE: DaytonaSelfHostedMCPTool does not inherit from BaseTool")
        
except ImportError as e:
    print(f"FAILURE: Could not import DaytonaSelfHostedMCPTool: {e}")
except Exception as e:
    print(f"FAILURE: An error occurred: {e}")
