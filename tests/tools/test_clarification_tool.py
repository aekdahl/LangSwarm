
import pytest
from langswarm.tools.core.clarification import ClarificationTool, ClarificationScope

@pytest.mark.asyncio
async def test_clarification_tool_metadata():
    tool = ClarificationTool()
    assert tool.metadata.name == "clarify"
    assert "clarification" in tool.metadata.description.lower()

@pytest.mark.asyncio
async def test_clarification_tool_output():
    tool = ClarificationTool()
    
    # Run the tool
    result = await tool.execute(
        prompt="Which file?",
        scope="parent_workflow",
        context="Found 2 files"
    )
    
    # Verify output structure
    assert result["status"] == "clarification_requested"
    assert result["clarification_details"]["prompt"] == "Which file?"
    assert result["clarification_details"]["scope"] == "parent_workflow"
    assert result["clarification_details"]["context"] == "Found 2 files"

@pytest.mark.asyncio
async def test_clarification_tool_defaults():
    tool = ClarificationTool()
    
    # Run with minimal args
    result = await tool.execute(prompt="Help me")
    
    # Verify defaults
    assert result["clarification_details"]["scope"] == "local"
    assert result["clarification_details"]["context"] is None
