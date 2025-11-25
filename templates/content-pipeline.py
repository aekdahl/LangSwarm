#!/usr/bin/env python3
"""
Content Creation Pipeline Template
Three-stage workflow: Research → Write → Edit
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
from langswarm import create_agent
from langswarm.core.agents import register_agent
from langswarm.core.workflows import create_simple_workflow, get_workflow_engine

async def main():
    # Create specialized agents for each stage
    researcher = create_agent(
        name="researcher",
        model="gpt-4",
        system_prompt="You are a thorough researcher. Gather comprehensive information on topics."
    )
    
    writer = create_agent(
        name="writer",
        model="gpt-4",
        system_prompt="You are a skilled writer. Create engaging, well-structured content."
    )
    
    editor = create_agent(
        name="editor",
        model="gpt-4",
        system_prompt="You are a meticulous editor. Polish content for clarity and impact."
    )
    
    # Register agents for workflow orchestration
    register_agent(researcher)
    register_agent(writer)
    register_agent(editor)
    
    # Create workflow: researcher → writer → editor
    workflow = create_simple_workflow(
        workflow_id="content_pipeline",
        name="Content Creation Pipeline",
        agent_chain=["researcher", "writer", "editor"]
    )
    
    # Execute the pipeline
    engine = get_workflow_engine()
    result = await engine.execute_workflow(
        workflow=workflow,
        input_data={"input": "Write an article about AI in healthcare"}
    )
    
    print("Final Content:")
    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())

