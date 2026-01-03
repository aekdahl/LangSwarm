import asyncio
import sys
import os
from pathlib import Path
# Add project root to sys path to ensure imports work
sys.path.append(str(Path(__file__).parent.parent.parent))

from langswarm.core.config import load_config
from langswarm.core.workflows import get_workflow_engine

async def main():
    try:
        # Create dummy file
        with open("sample.txt", "w") as f:
            f.write("This is a sample business report. Revenue: $1M. Growth: 20%.")
            
        print("Loading config...")
        config = load_config("langswarm.yaml")
        print(f"Loaded {len(config.agents)} agents")
        
        engine = get_workflow_engine()
        print("Running workflow...")
        
        # The example implies input data passing
        result = await engine.execute_workflow(
            workflow_id="document_analysis",
            input_data={
                "document_path": "sample.txt", # The read_step needs this context
                "user_request": "Analyze sample.txt" 
            }
        )
        print("Result:", result.output)
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
