class CodeUnderstandingAgent:
    def __init__(self, tools):
        """
        Initialize the Code Understanding Agent with a set of tools.
        Args:
            tools (list): A list of instantiated tools available to the agent.
        """
        self.tools = {tool.name: tool for tool in tools}

    def execute_task(self, task_name, *args, **kwargs):
        """
        Execute a task by selecting the appropriate tool.
        Args:
            task_name (str): The name of the task to execute.
            *args, **kwargs: Additional arguments for the task.

        Returns:
            The result of the tool execution.
        """
        if task_name not in self.tools:
            raise ValueError(f"No tool found for task: {task_name}")
        return self.tools[task_name].use(*args, **kwargs)

    def workflow(self, tasks):
        """
        Execute a workflow consisting of multiple tasks.
        Args:
            tasks (list): A list of task dictionaries with 'name' and 'params'.

        Returns:
            dict: Results of all tasks in the workflow.
        """
        results = {}
        for task in tasks:
            task_name = task["name"]
            task_params = task.get("params", {})
            results[task_name] = self.execute_task(task_name, **task_params)
        return results

class ReasonAboutCode(BaseCapability):
    """
    Capability for reasoning about the agent's own source code.
    """
    def __init__(self, code_search_tool):
        super().__init__(name="ReasonAboutCode", description="Analyze and reason about source code.")
        self.code_search_tool = code_search_tool

    def run(self, query):
        """
        Use the code search tool to analyze code relevant to the query.
        """
        code_snippets = self.code_search_tool.search(query)
        reasoning_prompt = f"Analyze the following code for '{query}':\n\n{code_snippets}"
        return reasoning_prompt
