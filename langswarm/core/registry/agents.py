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
        """Retrieve an agent from either registry."""
        return cls._registry.get(name) or cls._helper_registry.get(name)

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