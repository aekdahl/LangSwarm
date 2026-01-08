from typing import Dict, Any, Optional
from enum import Enum
from langswarm.tools.base import BaseTool
from langswarm.tools.interfaces import ToolType

class ClarificationScope(str, Enum):
    """Scope of the clarification request"""
    LOCAL = "local"
    PARENT_WORKFLOW = "parent_workflow"
    ROOT_USER = "root_user"

class ClarificationTool(BaseTool):
    """
    Tool for agents to request clarification when faced with ambiguity or missing information.
    This acts as a structured signal ("escalation") that can be intercepted by the workflow engine.
    """
    
    def __init__(self):
        super().__init__(
            tool_id="clarify",
            name="clarify",
            description="Request clarification from the user or parent workflow when requirements are ambiguous or critical confirmation is needed.",
            tool_type=ToolType.BUILTIN
        )
        
        # Define the main method schema
        self.add_method(
            name="execute",
            description="Submit a clarification request",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The specific question or clarification needed."
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["local", "parent_workflow", "root_user"],
                        "description": "Who to ask: 'local', 'parent_workflow', or 'root_user'.",
                        "default": "local"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context regarding why clarification is needed."
                    }
                },
                "required": ["prompt"]
            },
            returns={
                "type": "object",
                "description": "Structuring object indicating clarification status"
            }
        )
    
    async def execute(self, prompt: str, scope: str = "local", context: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the clarification request.
        """
        return {
            "status": "clarification_requested",
            "clarification_details": {
                "prompt": prompt,
                "scope": scope,
                "context": context
            },
            "message": f"Clarification requested ({scope}): {prompt}"
        }
