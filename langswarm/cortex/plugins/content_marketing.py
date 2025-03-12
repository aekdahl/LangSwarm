class MarketingContentGenerator(BaseTool):
    def __init__(self, repo_adapter, llm_agent):
        """
        Initialize the Marketing Content Generator Tool.
        Args:
            repo_adapter: Database adapter for repository access.
            llm_agent: LLM instance for content generation.
        """
        super().__init__(
            name="Marketing Content Generator",
            description="Generates marketing and promotional content for the software."
        )
        self.repo_adapter = repo_adapter
        self.llm_agent = llm_agent

    def use(self, content_type="feature_highlights", target_audience="general", tone="professional"):
        """
        Generate marketing content.
        Args:
            content_type (str): The type of content to generate (e.g., feature_highlights, blog_post, release_notes).
            target_audience (str): The target audience for the content (e.g., general, developers, executives).
            tone (str): The tone of the content (e.g., professional, friendly, technical).

        Returns:
            str: The generated content.
        """
        # Step 1: Retrieve the codebase features and documentation
        docs = self.repo_adapter.get_documentation()
        features = self.repo_adapter.get_feature_summaries()

        # Step 2: Generate content based on type
        response = self.llm_agent.run(
            {
                "task": "generate_marketing_content",
                "content_type": content_type,
                "docs": docs,
                "features": features,
                "target_audience": target_audience,
                "tone": tone,
            }
        )
        return response
