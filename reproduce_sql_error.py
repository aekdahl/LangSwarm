
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append('/Users/alexanderekdahl/Docker/LangSwarm')

try:
    from langswarm.tools.mcp.sql_database.main import SQLDatabaseMCPTool
    print("Successfully imported SQLDatabaseMCPTool")
    
    try:
        print("Attempting to instantiate SQLDatabaseMCPTool...")
        tool = SQLDatabaseMCPTool(identifier="test_sql_db")
        print("Successfully instantiated SQLDatabaseMCPTool")
    except Exception as e:
        print(f"Failed to instantiate SQLDatabaseMCPTool: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"Failed to import SQLDatabaseMCPTool: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()
