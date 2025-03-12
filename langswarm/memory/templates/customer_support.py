from langswarm.agent import LangSwarmAgent
from memory.templates.base_workflow import BaseWorkflow
from retrievers import FAQRetriever, TicketRetriever
from rerankers import CombinedReranker

class CustomerSupportWorkflow(BaseWorkflow):
    def __init__(self, faq_config, ticket_config, reranker_config, faq_data, ticket_data):
        agent = LangSwarmAgent()
        retrievers = [FAQRetriever(**faq_config), TicketRetriever(**ticket_config)]
        reranker = CombinedReranker(**reranker_config)
        super().__init__(agent, retrievers, [reranker])

        # Load data
        processed_faq = self.process_data(faq_data)
        processed_ticket = self.process_data(ticket_data)
        self.load_data(processed_faq + processed_ticket)

    def run(self, query):
        documents = self.query_and_rerank(query)
        if not documents:
            return None
        return self.generate_response(query, documents[0]["text"])
