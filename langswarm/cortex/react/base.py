from typing import Any, Optional

class BaseReAct:
    """
    A base class for ReAct workflows, encapsulating reasoning and acting logic.
    """

    def reason(self, query: str) -> str:
        """
        Generate reasoning steps using the agent.
        """
        context = " ".join([message["content"] for message in self.in_memory]) if hasattr(self, "in_memory") else ""
        prompt = f"Context: {context}\n\nQuery: {query}\n\nThoughts:"
        return self.agent.invoke(prompt) if callable(self.agent) else self.agent.run(prompt)

    def act(self, action: tuple) -> Any:
        """
        Perform an action based on reasoning.
        """
        tool_name, args = action
        for tool in self.tools:
            if tool.name == tool_name:
                if hasattr(tool, "run"):  # LangChain tools
                    return tool.run(*args)
                elif hasattr(tool, "use"):  # Custom tools
                    return tool.use(*args)
        raise ValueError(f"Tool '{tool_name}' not found.")

    def react(self, query):
        raise NotImplementedError("This method should be implemented in a subclass.")
