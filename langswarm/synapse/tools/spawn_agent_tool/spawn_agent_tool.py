import uuid
import threading
from typing import Callable, Dict, Any

# Global registries for background (async) tasks
AGENT_THREADS = {}   # agent_id -> threading.Thread
AGENT_RESULTS = {}   # agent_id -> final or intermediate result


def agent_worker(agent_class: Callable, agent_args: Dict, agent_id: str, task_data: Any):
    """
    Worker function for asynchronous tasks. Creates and runs the agent in a separate thread, 
    storing the result in AGENT_RESULTS.
    """
    try:
        # 1) Instantiate the agent class
        agent_instance = agent_class(**agent_args)
        # 2) Execute its run_task method
        result = agent_instance.run_task(task_data)
        # 3) Store the result so we can retrieve it later
        AGENT_RESULTS[agent_id] = result
    except Exception as e:
        AGENT_RESULTS[agent_id] = f"Error: {str(e)}"


class SpawnAgentTool:
    """
    A unified tool for:
        - create_agent: Create an agent instance in memory (not running).
        - run_async: Run an already-created agent in a background thread.
        - create_and_run_async: Create & run agent in one step, returning agent_id.
        - create_and_run_sync: Create & run agent in one step, synchronously in the main thread.

    Usage examples (for an LLM's ReAct style calls):
    use:spawn_agent|create_agent|{"agent_class": "MySubAgent", "agent_args": {"foo": "bar"}}
    use:spawn_agent|run_async|{"agent_id": "<some_id>", "task_data": {"some_key": "some_value"}}
    use:spawn_agent|create_and_run_async|{"agent_class": "...", "agent_args": {...}, "task_data": {...}}
    use:spawn_agent|create_and_run_sync|{"agent_class": "...", "agent_args": {...}, "task_data": {...}}
    """

    def __init__(self):
        # Store references to agent instances that were created but not yet run
        self.agents_created = {}  # agent_id -> agent_instance

    def create_agent(self, agent_class: Callable, agent_args: Dict) -> str:
        """
        Create an agent (not running). Returns an agent_id.
        The user/agent can run it later or do other tasks with it.
        """
        agent_id = str(uuid.uuid4())
        agent_instance = agent_class(**agent_args)
        self.agents_created[agent_id] = agent_instance
        return agent_id

    def run_async(self, agent_id: str, task_data: Any) -> str:
        """
        Run an *already created* agent in a separate thread.
        Returns the agent_id. The result is stored in AGENT_RESULTS[agent_id].
        """
        agent_instance = self.agents_created.get(agent_id)
        if not agent_instance:
            return f"Error: No agent found with ID '{agent_id}'"

        def worker_wrapper():
            try:
                result = agent_instance.run_task(task_data)
                AGENT_RESULTS[agent_id] = result
            except Exception as e:
                AGENT_RESULTS[agent_id] = f"Error: {str(e)}"

        thread = threading.Thread(target=worker_wrapper, daemon=True)
        AGENT_THREADS[agent_id] = thread
        thread.start()

        return agent_id

    def create_and_run_async(self, agent_class: Callable, agent_args: Dict, task_data: Any) -> str:
        """
        Create a new agent and immediately run it in a separate thread,
        returning the agent_id. The final result is stored in AGENT_RESULTS[agent_id].
        """
        agent_id = str(uuid.uuid4())
        thread = threading.Thread(
            target=agent_worker,
            args=(agent_class, agent_args, agent_id, task_data),
            daemon=True
        )
        AGENT_THREADS[agent_id] = thread
        thread.start()
        return agent_id

    def create_and_run_sync(self, agent_class: Callable, agent_args: Dict, task_data: Any) -> Any:
        """
        Create a new agent and run it synchronously in the current thread, 
        returning the final result directly.
        """
        try:
            agent_instance = agent_class(**agent_args)
            result = agent_instance.run_task(task_data)
            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def check_agent_status(self, agent_id: str) -> str:
        """
        Check whether the thread is still alive or finished.
        If finished, return the final result from AGENT_RESULTS.
        """
        thread = AGENT_THREADS.get(agent_id)
        if not thread:
            return f"Agent with ID '{agent_id}' not found."

        if thread.is_alive():
            return f"Agent {agent_id} is still running asynchronously."
        else:
            result = AGENT_RESULTS.get(agent_id, "No result recorded.")
            return f"Agent {agent_id} completed with result:\n{result}"
