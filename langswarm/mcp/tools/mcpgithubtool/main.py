from langswarm.synapse.tools.base import BaseTool


class MCPGitHubTool(BaseTool):
    """
    A LangSwarm-compatible tool that wraps a remote MCP tool.
    """

    def __init__(
        self,
        identifier: str,
        name: str,
        description: str,
        instruction: str,
        brief: str = "",
        **kwargs
    ):
        """
        :param name: Tool name
        :param description: Full description
        :param instruction: Instruction string (shown to agent)
        :param identifier: Unique identifier
        :param brief: Short description
        """
        super().__init__(
            name=name,
            description=description,
            instruction=instruction,
            identifier=identifier,
            brief=brief,
            **kwargs
        )
        self.id = identifier
        self.type = name
        self.identifier = identifier
        for key, value in kwargs.items():
            if not hasattr(self, key) and not key.startswith("_"):
                setattr(self, key, value)
