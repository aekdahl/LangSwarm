from langswarm.agent import LangSwarmAgent
from memory.templates.base_workflow import BaseWorkflow
from retrievers import HybridRetriever
from rerankers import SemanticReranker

class ChatbotWorkflow(BaseWorkflow):
    def __init__(self, retriever_config, reranker_config, data_files):
        agent = LangSwarmAgent()
        retriever = HybridRetriever(**retriever_config)
        reranker = SemanticReranker(**reranker_config)
        super().__init__(agent, [retriever], [reranker])

        # Load data
        raw_data = [line.strip() for file in data_files for line in open(file)]
        processed_data = self.process_data(raw_data)
        self.load_data(processed_data)

    def run(self, query):
        documents = self.query_and_rerank(query)
        if not documents:
            return None
        return self.generate_response(query, documents[0]["text"])
