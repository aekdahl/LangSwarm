from langswarm.agent import LangSwarmAgent
from memory.templates.base_workflow import BaseWorkflow
from retrievers import HybridRetriever
from rerankers import DomainSpecificReranker

class ResearchAssistantWorkflow(BaseWorkflow):
    def __init__(self, retriever_config, reranker_config, research_data):
        agent = LangSwarmAgent()
        retriever = HybridRetriever(**retriever_config)
        reranker = DomainSpecificReranker(**reranker_config)
        super().__init__(agent, [retriever], [reranker])

        # Load data
        processed_data = self.process_data(research_data, metadata={"source": "research"})
        self.load_data(processed_data)

    def run(self, query):
        documents = self.query_and_rerank(query)
        if not documents:
            return None
        return self.generate_response(query, documents[0]["text"])
