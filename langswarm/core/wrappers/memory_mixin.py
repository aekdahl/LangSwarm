from typing import Any, Optional, List

class MemoryMixin:
    """
    Mixin for memory management.
    """

    def _initialize_memory(self, agent: Any, memory: Optional[Any], in_memory: list) -> Optional[Any]:
        """
        Initialize or validate memory for the agent.

        If the agent already have memory initialized, we used that.
        If the memory is a LangChain memory instance, we use that.
        If non of these are available we return None. No external memory in use.

        :ToDo - Initialize LangChain memory (or other external memory) upon request.
        """
        if hasattr(agent, "memory") and agent.memory:
            return agent.memory

        if memory:
            if hasattr(memory, "load_memory_variables") and hasattr(memory, "save_context"):
                return memory
            raise ValueError(f"Invalid memory instance provided. Memory: {str(memory)}")

        return None

    def add_user_message(self, message: str):
        """
        Custom logic for handling user messages before delegating to LangChain's memory.

        ToDo: Add custom logic for handling in-memory.
        """
        print(f"Custom handling of user message: {message}")
        if hasattr(self.memory, "chat_memory") and hasattr(self.memory.chat_memory, "add_user_message"):
            self.memory.chat_memory.add_user_message(message)
        else:
            raise ValueError("Memory instance does not support user message addition.")

    def add_ai_message(self, message: str):
        """
        Custom logic for handling AI messages before delegating to LangChain's memory.

        ToDo: Add custom logic for handling in-memory.
        """
        print(f"Custom handling of AI message: {message}")
        if hasattr(self.memory, "chat_memory") and hasattr(self.memory.chat_memory, "add_ai_message"):
            self.memory.chat_memory.add_ai_message(message)
        else:
            raise ValueError("Memory instance does not support AI message addition.")

    def _update_memory_summary(self, memory_adapter: Any, memory_summary_adapter: Any) -> Optional[Any]:

        if memory_adapter is None or memory_summary_adapter is None:
            return
        
        # Retrieve the stored summary and last processed timestamp from ChromaDB
        summary_record = memory_summary_adapter.query("", filters={"key": {"$eq": self.agent.identifier}}, n=None) 
        summary_record = summary_record or {}
        
        # Store last processed timestamp (this should be persistent)
        last_processed_timestamp = summary_record.get("last_processed_timestamp")

        # Query to get all conversations up to the last processed timestamp
        if last_processed_timestamp:
            all_conversations = memory_adapter.query("", filters={"timestamp": {"$gt": last_processed_timestamp}}, n=None)
        else:
            all_conversations = memory_adapter.query("", n=None)

        if all_conversations:
            # Generate summary from current summary and all past conversations using the LLM
            conversation_texts = [f"{conv['user_input']} -> {conv['agent_response']}" for conv in all_conversations]
            combined_text = "\n".join(conversation_texts)
            
            prompt = f'''You have been tasked with summarizing conversation records in a bullet-point format. Your goal is to create a clear, concise summary of the interactions that highlights the most important information.

1. Summarize the conversations using bullet points, focusing on the most recent interactions.
2. Ensure that the important information and key themes from the discussions are included in the summary.
3. Reference older conversations briefly, indicating that they can be retrieved for more details.

Your summary should be easy to read and provide a clear overview of the interactions in a concise manner.

Example output:
- Recently discussed memory retrieval errors and how to access stored history.
- Emphasized the importance of summarizing past interactions.
- Suggested using an LLM for improved context.
- Older discussions are available for reference if needed.

Please generate the summary based on the retrieved conversation records and the current summary below:

Current summary: 
---
{summary_record["summary"]}
---

Retrieved conversation records:
---
{combined_text}
---

Output only the generated summary. Nothing else.
'''

            # Use the LLM to generate a summary
            summary = self.chat(prompt)

            # Update the last processed timestamp to the latest one in the new conversations
            last_processed_timestamp = max(conv["timestamp"] for conv in all_conversations)

            # Save the merged summary to ChromaDB
            summary_record = {
                "summary": summary,
                "last_processed_timestamp": last_processed_timestamp
            }
            
            # Store the summary record in ChromaDB
            memory_summary_adapter.add_document({
                "key": self.agent.identifier, 
                "text":summary, 
                "metadata": {
                    "last_processed_timestamp": last_processed_timestamp,
                    "key": self.agent.identifier
                }
            })
            
            # Set the memory for the agent
            self.agent.set_memory([summary])
        
        elif summary_record.get("summary"):
            # Set the memory for the agent
            self.agent.set_memory([summary_record.get("summary")])
            