import time
import json
import datetime

from ..base.log import GlobalLogger  # Import the existing logging system


class AgentRegistry:
    """
    Manages registered agents, cost tracking, budget enforcement, and optional prepaid credits.
    
    Enforce Singleton pattern while maintaining a global registry.
    """
    _instance = None  # Store the singleton instance
    _registry = {}
    _helper_registry = {}
    
    total_budget_limit = None  # Optional global cost cap
    total_cost = 0  # Track total spent
    agent_costs = {}  # Track individual agent spending
    agent_budget_limits = {}  # Optional per-agent limits
    daily_cost_history = {}  # Stores past daily costs (date -> cost)
    
    # Optional credit system (globally shared across all agents)
    total_credits = None  # Total prepaid credits (if set)

    # Time Tracking for Budget Reset
    _last_reset = None  # Stores last reset timestamp

    PREDEFINED_HELPER_AGENTS = {
        "ls_json_parser": "Parses and corrects malformed JSON. Enables LangSwarm functions to use GenAI to correct JSON.",
    }

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def _check_and_reset_budget(cls):
        """Automatically resets total cost if a new day has started and stores previous day's data."""
        current_date = datetime.date.today()
        if cls._last_reset is None or cls._last_reset < current_date:
            # Store the previous day's total cost before resetting
            if cls._last_reset:
                cls.daily_cost_history[cls._last_reset] = cls.total_cost

            cls.total_cost = 0  # Reset total daily cost
            cls.agent_costs = {name: 0 for name in cls.agent_costs}  # Reset per-agent costs
            cls._last_reset = current_date  # Update last reset time

    @classmethod
    def register(cls, agent, name=None, agent_type=None, metadata=None, budget_limit=None):
        """Register an agent, preventing overwrites of predefined helper agents."""
        name = name or agent.name
        agent_type = agent_type or agent.agent_type
        
        if name in cls.PREDEFINED_HELPER_AGENTS:
            raise ValueError(
                f"'{name}' is a predefined helper agent. Use `register_helper_agent()` instead.\n"
                f"{name}: {cls.PREDEFINED_HELPER_AGENTS[name]}"
            )
        cls._registry[name] = {"agent": agent, "name": name, "type": agent_type, "metadata": metadata or {}}
        
        if budget_limit:
            cls.agent_budget_limits[name] = budget_limit
        cls.agent_costs[name] = 0  # Initialize agent's cost tracking

    @classmethod
    def register_helper_agent(cls, agent, name=None, agent_type=None, metadata=None, budget_limit=None):
        """Explicitly register a helper agent."""
        name = name or agent.name
        agent_type = agent_type or agent.agent_type
        
        if name not in cls.PREDEFINED_HELPER_AGENTS:
            raise ValueError(
                f"'{name}' is not a predefined helper agent. Available: {', '.join(cls.PREDEFINED_HELPER_AGENTS.keys())}"
            )
        cls._helper_registry[name] = {"name": name, "agent": agent, "type": agent_type, "metadata": metadata or {}}
        
        if budget_limit:
            cls.agent_budget_limits[name] = budget_limit
        cls.agent_costs[name] = 0  # Initialize agent's cost tracking

    @classmethod
    def get(cls, name):
        """Retrieve an agent from either registry, auto-creating predefined helpers if needed."""
        # Check if agent exists in registries
        agent_dict = cls._registry.get(name) or cls._helper_registry.get(name)
        
        if agent_dict:
            # Return the actual agent object, not the dict
            return agent_dict.get("agent")
        
        # Auto-create predefined helper agents on first access
        if name in cls.PREDEFINED_HELPER_AGENTS:
            try:
                # Auto-create the predefined helper agent
                agent_instance = cls._create_predefined_helper_agent(name)
                if agent_instance:
                    cls.register_helper_agent(agent_instance, name=name)
                    # Return the actual agent object, not the dict
                    helper_dict = cls._helper_registry.get(name)
                    return helper_dict.get("agent") if helper_dict else None
            except Exception as e:
                # If auto-creation fails, log and continue
                print(f"Warning: Failed to auto-create predefined helper agent '{name}': {e}")
        
        return None
    
    @classmethod
    def _create_predefined_helper_agent(cls, name):
        """Create a predefined helper agent instance."""
        if name == "ls_json_parser":
            try:
                from langswarm.v1.core.factory.agents import AgentFactory
                
                # Check if we have an API key - if not, return None
                import os
                if not os.getenv('OPENAI_API_KEY'):
                    print(f"Warning: OPENAI_API_KEY not set - cannot create ls_json_parser agent")
                    return None
                
                # Define the system prompt
                ls_json_parser_prompt = """You are a specialized JSON parser and validator assistant.

CRITICAL TASK:
Extract and return ONLY valid JSON from any text input you receive.

PROCESSING GUIDELINES:
- If input is already valid JSON → return it exactly as-is
- If input contains JSON within text/markdown → extract just the JSON part
- Remove markdown code fences, explanations, or surrounding text
- Fix minor JSON formatting issues when possible
- If no valid JSON found → return empty object: {}

RESPONSE FORMAT:
- Return ONLY the JSON object/array
- NO explanations, markdown, or additional text
- NO code fences or formatting
- NO wrapper structures

**Examples:**

Input: {"query": "test", "limit": 10}
Output: {"query": "test", "limit": 10}

Input: Here are the search parameters: {"query": "company policies", "limit": 5}
Output: {"query": "company policies", "limit": 5}

Input: ```json\n{"method": "search", "params": {"q": "example"}}\n```
Output: {"method": "search", "params": {"q": "example"}}

Input: I want to search for information about "my company products" with a limit of 10 results
Output: {"query": "my company products", "limit": 10}

Be precise, efficient, and always return valid JSON without any wrapper or explanation."""

                # Create the agent using AgentFactory (without auto-registration)
                agent = AgentFactory._create_base_agent(
                    agent_type="langchain-openai",
                    documents=None,
                    model="gpt-4o",
                    system_prompt=ls_json_parser_prompt
                )
                
                # Wrap with AgentWrapper - pass system_prompt explicitly
                from langswarm.v1.core.wrappers.generic import AgentWrapper
                wrapped_agent = AgentWrapper(
                    name="ls_json_parser",
                    agent=agent,
                    model="gpt-4o",
                    agent_type="langchain-openai",
                    system_prompt=ls_json_parser_prompt,
                    allow_middleware=False  # CRITICAL: Disable tool calling for JSON parser
                )
                
                return wrapped_agent
            except Exception as e:
                print(f"Failed to create ls_json_parser agent: {e}")
                return None
        
        return None

    @classmethod
    def list(cls):
        """List all registered agents."""
        return cls._registry

    @classmethod
    def list_helpers(cls):
        """List all registered helper agents."""
        return cls._helper_registry
    
    @classmethod
    def report_usage(cls, name, cost):
        """
        Report API usage cost and deduct from global credits (if enabled).
        """
        cls._check_and_reset_budget()  # Ensure daily budget enforcement
        
        if name not in cls._registry and name not in cls._helper_registry:
            raise ValueError(f"Agent '{name}' not found.")

        # Prepaid credits check (if enabled)
        if cls.total_credits is not None and cls.total_credits < cost:
            raise RuntimeError("Insufficient credits.")

        # Check total budget limit
        if cls.total_budget_limit is not None and (cls.total_cost + cost) > cls.total_budget_limit:
            raise RuntimeError("Total budget exceeded. Execution blocked.")

        # Check agent-specific budget
        agent_limit = cls.agent_budget_limits.get(name)
        if agent_limit is not None and (cls.agent_costs[name] + cost) > agent_limit:
            raise RuntimeError(f"Budget limit exceeded for agent '{name}'.")

        # Update credits
        if cls.total_credits is not None:
            cls.total_credits -= cost  # Deduct from global credits
            
        # Update costs
        cls.total_cost += cost
        cls.agent_costs[name] += cost
        
        GlobalLogger.log(
            f"Agent '{name}' used {cost:.2f} tokens. Total Cost: {cls.total_cost:.2f}",
            level="info"
        )
        
    @classmethod
    def get_cost_report(cls):
        """
        Return a summary of total and per-agent costs.
        """
        return {
            "total_spent": cls.total_cost,
            "agent_costs": cls.agent_costs,
            "total_budget_limit": cls.total_budget_limit,
            "agent_budget_limits": cls.agent_budget_limits,
        }

    @classmethod
    def get_credit_report(cls):
        """
        Return the remaining global credits.
        """
        cls._check_and_reset_budget()  # Ensure up-to-date values
        return {"total_credits": cls.total_credits}

    @classmethod
    def get_daily_cost_history(cls, days=7):
        """
        Retrieve past cost data for reporting (default: last 7 days).
        """
        return dict(sorted(cls.daily_cost_history.items(), reverse=True)[:days])

    @classmethod
    def set_total_budget(cls, budget):
        """
        Set a total budget limit for all agents combined.
        """
        cls.total_budget_limit = None if budget == 0 else budget

    @classmethod
    def set_total_credits(cls, credits):
        """
        Set a global prepaid credit balance (shared by all agents).
        """
        cls.total_credits = None if credits == 0 else credits

    @classmethod
    def reset_costs(cls):
        """
        Reset all cost tracking.
        """
        cls._check_and_reset_budget()
        cls.total_cost = 0
        cls.agent_costs = {name: 0 for name in cls.agent_costs}

    @classmethod
    def reset_credits(cls):
        """
        Reset the global credit balance (set to None).
        """
        cls.total_credits = None

    @classmethod
    def generate_daily_report(cls):
        """
        Generates a summary report of today's cost usage.
        """
        cls._check_and_reset_budget()  # Ensure data is up-to-date

        report = {
            "date": str(cls._last_reset),
            "total_spent": cls.total_cost,
            "agent_costs": cls.agent_costs,
            "remaining_credits": cls.total_credits,
            "total_budget": cls.total_budget_limit,
            "budget_remaining": cls.total_budget_limit - cls.total_cost if cls.total_budget_limit else "N/A",
        }

        # Log report summary with GlobalLogger
        GlobalLogger.log(f"DAILY COST REPORT: {json.dumps(report, indent=4)}", level="info")

        return report