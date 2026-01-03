import asyncio
import sys
import os
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent.parent.parent))

from langswarm.core.agents import AgentBuilder, register_agent
from langswarm.core.workflows import create_simple_workflow, get_workflow_engine

async def main():
    try:
        # Mock keys
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key"
        
        print("Building agents...")
        # Correct usage: AgentBuilder(name)
        reader = await AgentBuilder("reader").litellm().model("gpt-3.5-turbo").system_prompt("Read input.").build()
        analyst = await AgentBuilder("analyst").litellm().model("gpt-3.5-turbo").system_prompt("Analyze.").build()
        advisor = await AgentBuilder("advisor").litellm().model("gpt-3.5-turbo").system_prompt("Advise.").build()

        print("Registering agents...")
        # register_agent is a convenience function that likely calls registry.register_agent
        # check if it's async
        await register_agent(reader)
        await register_agent(analyst)
        await register_agent(advisor)

        print("Creating workflow...")
        workflow = create_simple_workflow(
            workflow_id="finance_flow", 
            name="Financial Analysis", 
            agent_chain=["reader", "analyst", "advisor"]
        )

        engine = get_workflow_engine()
        print("Executing workflow...")
        
        result = await engine.execute_workflow(workflow, {"input": "AAPL"})
        print("Result:", result)

    except Exception as e:
        print(f"Execution Output: {e}")

if __name__ == "__main__":
    asyncio.run(main())
