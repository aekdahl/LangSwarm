class DocumentationGenerator(BaseTool):
    def __init__(self, repo_adapter, llm_agent):
        """
        Initialize the Documentation Generator Tool.
        Args:
            repo_adapter: Database adapter for repository access.
            llm_agent: LLM instance for documentation generation.
        """
        super().__init__(
            name="Documentation Generator",
            description="Updates or generates documentation based on the codebase."
        )
        self.repo_adapter = repo_adapter
        self.llm_agent = llm_agent

    def use(self, target_files=None):
        """
        Main method to run the Documentation Generator Tool.
        Args:
            target_files (list): List of files to generate documentation for. If None, targets the entire codebase.

        Returns:
            str: Pull request link or status.
        """
        # Step 1: Fetch target files or the entire codebase
        if not target_files:
            target_files = self.repo_adapter.get_all_files()

        # Step 2: Generate documentation
        new_docs = {}
        for file_path in target_files:
            code_content = self.repo_adapter.get_file_content(file_path)
            doc_update = self.llm_agent.run(
                {
                    "task": "generate_documentation",
                    "file_path": file_path,
                    "code": code_content,
                }
            )
            new_docs[file_path] = doc_update

        # Step 3: Create a branch and write updated docs
        branch_name = f"docs-update/{int(time.time())}"
        self.repo_adapter.create_branch(branch_name)
        for file_path, doc_content in new_docs.items():
            self.repo_adapter.write_file(file_path, doc_content, branch_name)

        # Step 4: Create a pull request
        return self.repo_adapter.create_pull_request(
            branch_name,
            title="Updated Documentation",
            description="Automated documentation updates for the codebase."
        )
