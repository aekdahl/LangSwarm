import pytest
from unittest.mock import patch
from langswarm.core.registry.agents import AgentRegistry


class DummyAgent:
    def __init__(self, name="dummy", agent_type="base"):
        self.name = name
        self.agent_type = agent_type


@pytest.fixture(autouse=True)
def reset_registry():
    AgentRegistry._registry.clear()
    AgentRegistry._helper_registry.clear()
    AgentRegistry.agent_costs.clear()
    AgentRegistry.agent_budget_limits.clear()
    AgentRegistry.total_cost = 0
    AgentRegistry.total_budget_limit = None
    AgentRegistry.total_credits = None
    AgentRegistry.daily_cost_history.clear()
    AgentRegistry._last_reset = None
    yield


def test_register_and_get_agent():
    agent = DummyAgent()
    AgentRegistry.register(agent)
    assert AgentRegistry.get(agent.name)["agent"] == agent


def test_register_helper_agent():
    agent = DummyAgent(name="ls_json_parser")
    AgentRegistry.register_helper_agent(agent)
    assert AgentRegistry.get(agent.name)["agent"] == agent


def test_register_fails_on_predefined_helper():
    agent = DummyAgent(name="ls_json_parser")
    with pytest.raises(ValueError):
        AgentRegistry.register(agent)


def test_register_helper_fails_on_unknown_helper():
    agent = DummyAgent(name="unknown_helper")
    with pytest.raises(ValueError):
        AgentRegistry.register_helper_agent(agent)


def test_report_usage_and_cost_tracking():
    agent = DummyAgent()
    AgentRegistry.register(agent)
    AgentRegistry.report_usage(agent.name, 10)
    assert AgentRegistry.agent_costs[agent.name] == 10
    assert AgentRegistry.total_cost == 10


def test_total_budget_limit_enforced():
    agent = DummyAgent()
    AgentRegistry.register(agent)
    AgentRegistry.set_total_budget(5)
    with pytest.raises(RuntimeError):
        AgentRegistry.report_usage(agent.name, 10)


def test_agent_budget_limit_enforced():
    agent = DummyAgent()
    AgentRegistry.register(agent, budget_limit=5)
    with pytest.raises(RuntimeError):
        AgentRegistry.report_usage(agent.name, 10)


def test_credit_limit_enforced():
    agent = DummyAgent()
    AgentRegistry.register(agent)
    AgentRegistry.set_total_credits(5)
    with pytest.raises(RuntimeError):
        AgentRegistry.report_usage(agent.name, 10)


def test_cost_report_structure():
    agent = DummyAgent()
    AgentRegistry.register(agent)
    AgentRegistry.report_usage(agent.name, 2)
    report = AgentRegistry.get_cost_report()
    assert "total_spent" in report
    assert agent.name in report["agent_costs"]


def test_credit_report_reflects_credit_value():
    AgentRegistry.set_total_credits(42)
    report = AgentRegistry.get_credit_report()
    assert report["total_credits"] == 42


def test_reset_costs_and_credits():
    agent = DummyAgent()
    AgentRegistry.register(agent)
    AgentRegistry.report_usage(agent.name, 10)
    AgentRegistry.reset_costs()
    assert AgentRegistry.total_cost == 0
    assert AgentRegistry.agent_costs[agent.name] == 0

    AgentRegistry.reset_credits()
    assert AgentRegistry.total_credits is None


@patch("langswarm.core.registry.agents.GlobalLogger")
def test_generate_daily_report_logs_and_returns_summary(mock_logger):
    agent = DummyAgent()
    
    AgentRegistry.register(agent)
    AgentRegistry.report_usage(agent.name, 1)
    
    report = AgentRegistry.generate_daily_report()
    
    assert "date" in report
    assert "total_spent" in report
    
    # ✅ Check it was called twice
    assert mock_logger.log.call_count == 2

    # ✅ Extract messages and assert our expected log is present
    log_messages = [call.args[0] for call in mock_logger.log.call_args_list]
    
    assert any("DAILY COST REPORT" in msg for msg in log_messages)
