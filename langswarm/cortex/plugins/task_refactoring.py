from .base import BaseCapability


class RefactoringAdvisor(BaseCapability):
    def __init__(self, repo_adapter, llm_agent, branch_prefix="refactor"):
        """
        Initializes the Refactoring Advisor tool.
        Args:
            repo_adapter: Database adapter for repository access.
            llm_agent: LLM instance for code analysis and suggestions.
            branch_prefix (str): Prefix for new branches.
        """
        super().__init__(
            name="Refactoring Advisor",
            description=(
                "Improves code and creates a new branch with a pull request. "
                "Inline Commenter", "Adds comments to complex or critical parts of the code. "
                "Creates detailed docstrings for all functions and classes."
            ),
            instruction=""
        )
        
    def run(self, payload, action="analyze_and_refactor"):
        """
        Execute the capability's actions.
        :param payload: str or dict - The input query or tool details.
        :param action: str - The action to perform: 'fetch_and_store' or 'query_code'.
        :return: str or List[str] - The result of the action.
        """
        if action == "analyze_and_refactor":
            return self.analyze_and_refactor(**payload)
        elif action == "inline_comment":
            return self.inline_comment(**payload)
        elif action == "create_pull_request":
            return self.create_pull_request(**payload)
        elif action == "read_file":
            return self.read_file(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )

    def analyze_and_refactor(self, file):
        """
        Analyzes and refactors the given files.
        Args:
            files (list): List of file paths to analyze.

        Returns:
            dict: Dictionary of file paths and their refactored content.
        """
        refactored_files = {}
        # Use LLM for analysis and suggestions
        
            
        return refactored_files

    def inline_comment(self, file_path, file_content):
        """
        Add inline comments to the file content.
        Args:
            file_content (str): The content of the file.

        Returns:
            str: Modified file content with comments.
        """
        prompt = (
            "Analyze the following code and add inline comments to complex or critical parts. "
            "Explain logic, dependencies, and key decisions. Then create a new branch in GitHub "
            "and update the corresponding file with your changes, finally create a pull request:\n\n"
            f"{file_path}\n\n"
            f"{file_content}"
        )
        return self.llm_agent.run(prompt)

    def generate_docstring(self, file_path, file_content):
        """
        Add docstrings to all functions and classes in the file content.
        Args:
            file_content (str): The content of the file.

        Returns:
            str: Modified file content with docstrings.
        """
        prompt = (
            "Analyze the following code and add detailed docstrings to all functions and classes. "
            "Describe their purpose, input parameters, outputs, and potential exceptions:\n\n"
            f"{file_content}"
        )
        return self.llm_agent.run(prompt)