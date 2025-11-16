"""
LangSwarm V1 Safety Limits Configuration

This module provides easy-to-use functions for setting safety limits to prevent
runaway costs from endless loops or excessive API usage.

Usage:
    from langswarm.v1.safety_limits import set_budget_limits, set_workflow_limits
    
    # Set global budget protection
    set_budget_limits(total_budget=10.00, agent_limits={'my_agent': 5.00})
    
    # Set workflow execution limits
    limits = set_workflow_limits(
        max_execution_time_sec=60,
        max_api_calls=20,
        max_consecutive_errors=5
    )
    
    # Use limits when running workflows
    executor.run_workflow('main_workflow', user_input, **limits)
"""

from typing import Dict, Optional


def set_budget_limits(
    total_budget: Optional[float] = None,
    prepaid_credits: Optional[float] = None,
    agent_limits: Optional[Dict[str, float]] = None
):
    """
    Set budget and credit limits to prevent runaway costs.
    
    Args:
        total_budget: Maximum total spending allowed (in USD)
        prepaid_credits: Total prepaid credits available (in USD)
        agent_limits: Dictionary of per-agent spending limits
        
    Example:
        >>> set_budget_limits(
        ...     total_budget=10.00,           # $10 total limit
        ...     prepaid_credits=20.00,        # $20 prepaid credits
        ...     agent_limits={'gpt4': 5.00}   # $5 limit for 'gpt4' agent
        ... )
        
    Raises:
        RuntimeError: When budget or credits are exceeded during execution
    """
    try:
        from langswarm.v1.core.registry import AgentRegistry
    except ImportError:
        from langswarm.core.registry import AgentRegistry
    
    if total_budget is not None:
        AgentRegistry.total_budget_limit = total_budget
        print(f"✅ Global budget limit set: ${total_budget:.2f}")
    
    if prepaid_credits is not None:
        AgentRegistry.total_credits = prepaid_credits
        print(f"✅ Prepaid credits set: ${prepaid_credits:.2f}")
    
    if agent_limits:
        for agent_name, limit in agent_limits.items():
            AgentRegistry.agent_budget_limits[agent_name] = limit
            print(f"✅ Agent '{agent_name}' budget limit set: ${limit:.2f}")
    
    print("\n🛡️  Budget protection enabled:")
    print(f"   - Workflows will auto-abort when limits are exceeded")
    print(f"   - This prevents runaway loops from consuming excessive credits")
    
    return {
        'total_budget_limit': AgentRegistry.total_budget_limit,
        'total_credits': AgentRegistry.total_credits,
        'agent_budget_limits': AgentRegistry.agent_budget_limits
    }


def set_workflow_limits(
    max_execution_time_sec: int = 300,
    max_api_calls: int = 100,
    max_consecutive_errors: int = 10
) -> Dict:
    """
    Set workflow execution limits to prevent runaway loops.
    
    These limits are applied per workflow execution and reset for each run.
    
    Args:
        max_execution_time_sec: Maximum workflow execution time (default: 300 = 5 minutes)
        max_api_calls: Maximum API calls per workflow (default: 100)
        max_consecutive_errors: Circuit breaker threshold (default: 10)
        
    Returns:
        Dictionary of limits to pass to run_workflow(**limits)
        
    Example:
        >>> limits = set_workflow_limits(
        ...     max_execution_time_sec=60,   # 1 minute timeout
        ...     max_api_calls=20,            # Max 20 API calls
        ...     max_consecutive_errors=5     # Stop after 5 consecutive errors
        ... )
        >>> executor.run_workflow('my_workflow', user_input, **limits)
        
    Raises:
        TimeoutError: When execution time exceeds max_execution_time_sec
        RuntimeError: When API calls or consecutive errors exceed limits
        KeyboardInterrupt: When Ctrl+C is pressed (graceful shutdown)
    """
    limits = {
        'max_execution_time_sec': max_execution_time_sec,
        'max_api_calls': max_api_calls,
        'max_consecutive_errors': max_consecutive_errors
    }
    
    print("🛡️  Workflow execution limits configured:")
    print(f"   - Maximum execution time: {max_execution_time_sec}s")
    print(f"   - Maximum API calls: {max_api_calls}")
    print(f"   - Maximum consecutive errors: {max_consecutive_errors}")
    print(f"\n   Pass these limits to run_workflow: executor.run_workflow('id', input, **limits)")
    
    return limits


def set_conservative_limits():
    """
    Set conservative safety limits suitable for development/testing.
    
    Limits:
        - $5 total budget
        - 60 second timeout
        - 20 API calls max
        - 3 consecutive errors max
        
    Returns:
        Dictionary of workflow limits to pass to run_workflow()
        
    Example:
        >>> limits = set_conservative_limits()
        >>> executor.run_workflow('test_workflow', input, **limits)
    """
    print("🔒 Setting CONSERVATIVE safety limits (recommended for dev/test)")
    print()
    
    set_budget_limits(total_budget=5.00)
    
    return set_workflow_limits(
        max_execution_time_sec=60,
        max_api_calls=20,
        max_consecutive_errors=3
    )


def set_production_limits():
    """
    Set reasonable production safety limits.
    
    Limits:
        - $50 total budget
        - 5 minute timeout
        - 200 API calls max
        - 10 consecutive errors max
        
    Returns:
        Dictionary of workflow limits to pass to run_workflow()
        
    Example:
        >>> limits = set_production_limits()
        >>> executor.run_workflow('prod_workflow', input, **limits)
    """
    print("🚀 Setting PRODUCTION safety limits")
    print()
    
    set_budget_limits(total_budget=50.00)
    
    return set_workflow_limits(
        max_execution_time_sec=300,
        max_api_calls=200,
        max_consecutive_errors=10
    )


def get_current_limits():
    """
    Get the currently configured safety limits.
    
    Returns:
        Dictionary with current budget and workflow limits
    """
    try:
        from langswarm.v1.core.registry import AgentRegistry
    except ImportError:
        from langswarm.core.registry import AgentRegistry
    
    return {
        'budget': {
            'total_budget_limit': AgentRegistry.total_budget_limit,
            'total_spent': AgentRegistry.total_cost,
            'total_credits': AgentRegistry.total_credits,
            'agent_costs': AgentRegistry.agent_costs,
            'agent_budget_limits': AgentRegistry.agent_budget_limits
        }
    }


def print_cost_report():
    """Print a detailed cost report."""
    try:
        from langswarm.v1.core.registry import AgentRegistry
    except ImportError:
        from langswarm.core.registry import AgentRegistry
    
    print("\n📊 Cost Report")
    print("=" * 50)
    print(f"Total Spent: ${AgentRegistry.total_cost:.4f}")
    
    if AgentRegistry.total_budget_limit:
        remaining = AgentRegistry.total_budget_limit - AgentRegistry.total_cost
        print(f"Budget Limit: ${AgentRegistry.total_budget_limit:.2f}")
        print(f"Remaining: ${remaining:.4f} ({remaining/AgentRegistry.total_budget_limit*100:.1f}%)")
    
    if AgentRegistry.total_credits is not None:
        print(f"Credits Remaining: ${AgentRegistry.total_credits:.4f}")
    
    if AgentRegistry.agent_costs:
        print("\nPer-Agent Costs:")
        for agent, cost in AgentRegistry.agent_costs.items():
            limit = AgentRegistry.agent_budget_limits.get(agent)
            limit_str = f" / ${limit:.2f}" if limit else ""
            print(f"  - {agent}: ${cost:.4f}{limit_str}")
    
    print("=" * 50)


# Quick setup function for immediate protection
def quick_protect(budget: float = 5.00):
    """
    Quick protection setup with one function call.
    
    Sets conservative limits suitable for dev/test:
    - Budget limit
    - 60 second timeout
    - 20 API calls max
    - 3 consecutive errors max
    
    Args:
        budget: Total budget limit in USD (default: $5)
        
    Returns:
        Dictionary of limits to pass to run_workflow()
        
    Example:
        >>> limits = quick_protect(budget=10.00)
        >>> executor.run_workflow('workflow_id', input, **limits)
    """
    print(f"⚡ Quick Protection Setup (${budget:.2f} budget)")
    print()
    
    set_budget_limits(total_budget=budget)
    
    return set_workflow_limits(
        max_execution_time_sec=60,
        max_api_calls=20,
        max_consecutive_errors=3
    )


if __name__ == "__main__":
    # Example usage
    print("LangSwarm V1 Safety Limits - Example Usage\n")
    
    # Quick protection
    limits = quick_protect(budget=5.00)
    
    print("\n" + "="*60)
    print("To use these limits:")
    print("="*60)
    print("""
from langswarm.v1.safety_limits import quick_protect
from langswarm.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

# Set up protection
limits = quick_protect(budget=5.00)

# Load and run workflow with limits
loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# Run with protection - will auto-abort on budget/time/error limits
result = executor.run_workflow('main_workflow', user_input, **limits)
    """)

