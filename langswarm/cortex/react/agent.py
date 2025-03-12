import time
import json
import re

from langswarm.core.wrappers.generic import AgentWrapper
from .base import BaseReAct

class ReActAgent(AgentWrapper, BaseReAct):
    """
    A specialized agent for workflows combining reasoning and acting (ReAct). This agent supports tools and plugins
    for enhanced functionality and flexibility. It parses input for actionable instructions (e.g., tools or plugins),
    routes actions to the appropriate handlers, and returns structured responses.
    """

    def __init__(
        self, 
        name, 
        agent, 
        model, 
        memory=None, 
        agent_type=None,
        tool_registry=None, 
        plugin_registry=None, 
        plugin_instruction=None, 
        **kwargs
    ):
        # Validate that the provided agent is not already wrapped
        if isinstance(agent, AgentWrapper):
            raise ValueError(
                "ReActAgent cannot wrap an already wrapped AgentWrapper. "
                "Please provide a raw agent (e.g., LLM or LangChain agent) instead."
            )
        
        # Continue with normal initialization
        super().__init__(
            name, 
            agent,
            model, 
            memory=memory, 
            agent_type=agent_type,
            tool_registry=tool_registry, 
            plugin_registry=plugin_registry, 
            plugin_instruction=plugin_instruction,
            **kwargs
        )

    def chat(self, query: str, max_iterations=10) -> str:
        """
        Handle both standard and ReAct-specific queries.

        :param query: str - The input query.
        :param max_iterations: int - Maximum iterations before returning a summary.
        :return: str - The final response.
        """

        history = []  # Store responses for final summarization

        for iteration in range(max_iterations):
            asked_to_continue = None
            agent_reply = super().chat(query)

            # ToDo: Update to current call format
            #request_call_error = self.utils._is_valid_request_calls_in_text(agent_reply)
            #if request_call_error:
            #    self._log_event(f"The agent formatted the request call incorrect.", "info")
            #    agent_reply = super().chat(request_call_error)
            #else:
            #    use_call_error = self.utils._is_valid_use_calls_in_text(agent_reply)
            #    if use_call_error:
            #        self._log_event(f"The agent formatted the use call incorrect.", "info")
            #        agent_reply = super().chat(use_call_error)

            status, result = self._react(agent_reply)

            # Store the intermediate response for summarization later
            history.append(f"-- Iteration {iteration + 1} --\nAgent response: {agent_reply}\nAction result: {result}")

            asked_to_continue = re.search(self.ask_to_continue_regex, agent_reply, re.IGNORECASE)
            
            # ToDo: The regex is not working properly
            #if not asked_to_continue:
            #    asked_to_continue = re.search(self.check_for_continuation, agent_reply, re.IGNORECASE)

            if status != 201 and asked_to_continue:
                self._log_event(f"Agent requested an internal step", "info")
                query = "Please continue."
                continue

            if status == 201:  # Successful action execution
                self._log_event(f"Action Result: {result}", "info")

                if result:
                    query = result  # Use the retrieved action result
                else:
                    self._log_event(f"No result from action: {result}", "info")
                    return f"{agent_reply} + No result from action: {result}."

            elif status == 200:  # No action detected
                self._log_event(f"No action detected: {result}", "info")
                return agent_reply

            else:  # Action not found or other error
                self._log_event(f"Action Error: {result}", "error")
                return agent_reply

        # If we reached max iterations, format a summarized response
        self._log_event(f"Exhausted max iterations: {max_iterations}", "info")
        formatted_summary = self._format_final_response(history)
        return formatted_summary
    
    def _react(self, reasoning: str) -> tuple:
        """
        Execute the reasoning and acting workflow: parse the input for tools or plugins, route the action,
        and return a structured response.
        :param reasoning: str - The input reasoning.
        :return: Tuple[int, str] - (status_code, response).
        """
        
        # ToDo: Handle multiple reasoning iterations. Maybe move the iteration from the chat() interface.
        
        actions = self._parse_action(reasoning)
        if actions:
            #status, result = self._route_action(*action_details)
            #return status, self._respond_to_user([reasoning, result])
        
            # Process each action and collect responses
            results = [self._route_action(*action) for action in actions]

            # Extract statuses and responses
            statuses, responses = zip(*results)  # Unzipping the tuple list

            # Determine final status:
            # - If any status is NOT 200 or 201 → return that status.
            # - Else if any status is 201 → return 201.
            # - Otherwise, return 200.
            if any(status not in {200, 201} for status in statuses):
                final_status = next(status for status in statuses if status not in {200, 201})
            elif 201 in statuses:
                final_status = 201
            else:
                final_status = 200

            # Concatenate responses into one string
            final_response = "\n\n".join(map(str, responses))

            return final_status, final_response
        else:
            self._log_event(f"No actions returned.", "info")

        return 200, reasoning
            
    def suggest_plugins(self, query: str, top_k: int = 5):
        """
        Suggest plugins relevant to a query using the plugin registry.

        :param query: A string describing the task or need.
        :param top_k: Number of top suggestions to return.
        :return: A list of suggested plugins with descriptions and similarity scores.
        """
        return self.plugin_registry.search_plugins(query, top_k=top_k)
