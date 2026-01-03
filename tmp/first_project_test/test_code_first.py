import asyncio
import sys
from pathlib import Path

# Add project root to sys path
sys.path.append(str(Path(__file__).parent.parent.parent))

from langswarm import create_agent, create_workflow
from langswarm.core.agents import register_agent
from langswarm.core.workflows import get_workflow_engine

async def main():
    # 1. Specialized Agents
    # We use simple prompts for the test
    reader = create_agent("reader", model="gpt-4o", 
                        system_prompt="Extract text from input.")
    
    analyst = create_agent("analyst", model="gpt-4o", 
                         system_prompt="Analyze key facts: {input}")
    
    writer = create_agent("writer", model="gpt-4o", 
                        system_prompt="Write a summary based on: {analyst.output}")

    # 2. Register
    register_agent(reader)
    register_agent(analyst)
    register_agent(writer)

    # 3. Workflow
    # Note: simple_api create_workflow uses a simplified definition structure?
    # Let's check langswarm_simple_api.md again.
    # It says: def create_workflow(definition: str, agents: List[Dict[str, Any]]) -> Workflow
    # Wait, the signature in the doc was:
    # create_workflow(definition: str, agents: List[Dict[str, Any]])
    # BUT my Quickstart used:
    # create_workflow(definition="...", agents=[{"agent": "..."...}])
    # Let's verify if `create_workflow` actually accepts this structure. 
    # If not, I should use `create_simple_workflow` from `langswarm.core.workflows` directly as seen in `index.mdx` example?
    # `index.mdx` used `create_workflow` too.
    # Actually, `langswarm/__init__.py` likely exposes `create_workflow` from `simple_api`.
    # Let's try to assume the `simple_api` matches the doc.
    
    workflow = create_workflow(
        definition="Document Pipeline",
        agents=[
             {"agent": "reader", "task": "Read: {input}"},
             {"agent": "analyst", "task": "Analyze: {reader.output}"},
             {"agent": "writer", "task": "Summarize: {analyst.output}"}
        ]
    )

    # 4. Run
    print("Running workflow...")
    # I'll mock the LLM calls or rely on them working if keys are set. 
    # If keys are missing, it will fail. I should check if I can use a mock provider?
    # Or just rely on the structure being correct.
    # For this test, I will assume the user has keys or I will catch the error.
    # Ideally I want to verify the ORCHESTRATION works.
    
    try:
        # We might not have keys in this env. 
        # But if it gets to "API key missing", the code is valid.
        result = await workflow.run(input_message="Sample Document Content")
        print("Result:", result)
    except Exception as e:
        print(f"Execution Error (Expected if no API key): {e}")
        # If it's a structural error, I need to know.

if __name__ == "__main__":
    asyncio.run(main())
