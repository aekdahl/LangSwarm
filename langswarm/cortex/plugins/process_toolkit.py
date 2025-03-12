from .base import BasePlugin

class ProcessToolkit(BasePlugin):
    """
    A plugin enabling an AI agent to use select processes.
    """
    def __init__(self, identifier):
        self.identifier = identifier
        self.brief = (
            f"Use any of a set of structured reasoning methods—such as Chain-of-Thought, "
            f"ReAct, Plan-and-Reflect, and multi-step approaches—when tackling different tasks."
        )
        
        super().__init__(
            name="ProcessToolkit",
            description="""Use any of a set of structured reasoning methods—such as Chain-of-Thought, ReAct, Plan-and-Reflect, and multi-step approaches—when tackling different tasks. This toolkit helps you decide whether to reason silently, call tools for actions, or break tasks into subtasks. By switching templates or methods, you can solve complex problems more effectively.""",
            instruction="""
- **Actions and Parameters**:
    - `run_process`: Get information about a step in the plugin process.
      - Parameters:
        - `process_name` (str): See the list of process names below.
        - `user_prompt` (str | optional): The original user prompt that holds the task to complete.

- **List of Process Names**:
    - `chain_of_thought`: Uses a hidden chain-of-thought approach—agent reasons internally step-by-step before providing a concise final answer.

    - `react`: Emphasizes Reason + Act. The agent can call tools or retrievers in a stepwise manner, observing results and continuing reasoning until it finalizes a response.

    - `multi_step`: Encourages the agent to break the user request into multiple subtasks and handle them systematically (with or without tool calls).

    - `plan_and_reflect`: The agent first forms a plan, reflects on it, and revises if needed, then produces a final solution.

    - `tree_of_thought`: Encourages branching multiple possible solutions and pruning unpromising ones, ultimately selecting the best.

    - `plan_execute_review`: The agent forms a plan, executes (calling tools if needed), then reviews or tests the outcome, iterating if necessary.

- **Agent query format**:
  ```
  use plugin:name|action|{"param1": "value1", "param2": "value2"}
  ```
  Replace `name`, `action` and parameters as needed.

Example:
- Report completion of a step:
  ```
  use plugin:process_toolkit|run_process|{"process_name": "react", "user_prompt": "Add docstrings to all methods"}
  ```
        """
        )

    def run(self, payload = {}, action="run_process"):
        """
        Execute the plugin's actions.
        :param payload: str or dict - The input query or plugin details.
        :param action: str - The action to perform.
        :return: str or List[str] - The result of the action.
        """
        if action == "run_process":
            return self.run_process(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )

    def run_process(self, **kwargs):
        """
        Expects arguments in the format:
        {
            "process_name": "<name of the process>",
            "user_prompt": "<the user’s question or request>",
            ... 
        }
        
        Example:
          use:process_toolkit|run_process|{"process_name": "react", "user_prompt": "Add docstrings to all methods"}
        """
        process_name = kwargs.get("process_name")
        user_prompt = kwargs.get("user_prompt", "No prompt provided.")

        # Step 1: Select the right template
        if process_name == "chain_of_thought":
            template = self._chain_of_thought_template()
        elif process_name == "react":
            template = self._react()
        elif process_name == "multi_step":
            template = self._multi_step()
        elif process_name == "plan_and_reflect":
            template = self._plan_and_reflect()
        elif process_name == "tree_of_thought":
            template = self._tree_of_thought()
        elif process_name == "plan_execute_review":
            template = self._plan_execute_review()
        else:
            return "Error: Unknown process name. Available processes are: chain_of_thought, react, multi_step, plan_and_reflect, tree_of_thought, plan_execute_review."

        # Step 2: Merge the user prompt into the template
        final_prompt = template.format(user_prompt=user_prompt)

        # Step 3: Here you'd call your LLM or internal reasoning function
        return final_prompt

    def _chain_of_thought_template(self):
        return """
You are to use a chain-of-thought approach to reason through the user request internally before providing the final answer.
Be explicit in your thinking (internally), but do NOT reveal your entire thought process to the user directly.

**Instructions:**
1. Think step by step about the problem. (Internally, not shown to user.)
2. Once you have reasoned out the solution, provide the final answer in a concise, user-friendly format.
3. Do NOT expose your hidden reasoning steps in the final output.

User Request:
{user_prompt}

-----
Respond with the final short or detailed answer after you've completed your chain-of-thought (silently).
"""

    def _react(self):
        return """
You are to use the ReAct (Reason + Act) framework. This means:
- You can reason step by step.
- If you need more data, you can call a tool or retriever by producing a command in the form:
  use:tool_name|action|{"param":"value"}
- Then observe the tool's response, integrate it into your reasoning, and continue.

**Instructions:**
1. Provide short internal reasoning steps to decide what tool or data you need.
2. Call the tool or retriever in the specified format whenever needed.
3. Once you have enough information, finalize your answer to the user.

User Prompt:
{user_prompt}

-----
Remember to keep your chain-of-thought private and only share the final answer with the user. 
If no tools are needed, simply answer.
"""

    def _multi_step(self): 
        return """
You are to plan a multi-step approach to solve the user's request. 
At each step, decide if you must gather more info via a tool or retriever, or if you can proceed to produce the final answer.

**Instructions:**
1. Break down the user request into sub-steps or sub-goals.
2. For each sub-step, decide if you need to call a tool or retriever in the form:
   use:tool_name|action|{"param":"value"}
3. If the sub-step can be done internally, reason silently and proceed.
4. Continue until all sub-steps are complete, then produce a final answer.

User Prompt:
{user_prompt}

-----
Provide the final consolidated answer after all sub-steps are resolved.
"""

    def _plan_and_reflect(self):
        return """
You will Plan and Reflect. 
- First, produce a high-level plan of how you'll handle the user's request.
- Then reflect on each part of the plan. If you see any issues or missing information, refine or ask for it.
- Finally, execute your final solution.

**Instructions:**
1. Create a quick plan of the tasks needed to solve this request.
2. Reflect on each task: do we have enough data or do we need to call a tool or do we need more from the user?
3. If everything is sufficient, produce the final answer or solution.

User Prompt:
{user_prompt}

-----
Return your plan + reflection as internal reasoning. Only the final conclusion should be shared directly with the user.
"""

    def _tree_of_thought():
        return """
You will use a Tree-of-Thought approach:
- Generate multiple solution branches or ideas in parallel if needed.
- Evaluate each branch, prune bad ideas.
- Converge on the best solution.

**Instructions:**
1. Create possible solution 'branches' or outlines.
2. Evaluate each branch for correctness, feasibility, or synergy with the user's goals.
3. Discard branches that are not viable.
4. Produce the final answer from the winning branch.

User Prompt:
{user_prompt}

-----
Only present the final single best solution to the user, after your internal branching and pruning.
"""

    def _plan_execute_review():
        return """
You will perform a plan-execute-review cycle:
- Plan: Outline steps or tasks for the user's request.
- Execute: If needed, call tools or retrievers. Then produce partial results.
- Review: Check if the partial results satisfy the plan or if you need to revise your approach.
- Finalize: Provide the final solution or answer.

**Instructions:**
1. Provide a clear plan.
2. Attempt execution using: use:tool_name|action|{"param": "value"} as needed.
3. Review results. If incomplete or incorrect, refine or plan again.
4. Conclude with a final, cohesive answer.

User Prompt:
{user_prompt}

-----
Summarize your final answer after ensuring the plan-execute-review loop is complete.
"""