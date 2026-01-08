
import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from langswarm.core.observability.token_tracking import (
    TokenBudgetManager, 
    TokenUsageAggregator, 
    TokenBudgetConfig, 
    TokenUsageEvent, 
    TokenEventType
)
from langswarm.core.observability.interfaces import IMetrics

class TestTokenBudgeting(unittest.TestCase):
    def setUp(self):
        self.metrics_mock = MagicMock(spec=IMetrics)
        self.aggregator = TokenUsageAggregator(metrics=self.metrics_mock)
        self.budget_manager = TokenBudgetManager(aggregator=self.aggregator)
        
        # Common test data
        self.user_id = "test_user"
        self.session_id = "test_session"

    def test_daily_token_limit_enforcement(self):
        async def run_test():
            # Set budget: 1000 tokens per day
            budget = TokenBudgetConfig(daily_token_limit=1000, enforce_limits=True)
            await self.budget_manager.set_budget(self.user_id, budget)
            
            # Record initial usage: 800 tokens
            event1 = TokenUsageEvent(
                user_id=self.user_id,
                session_id=self.session_id,
                total_tokens=800,
                cost_estimate=0.01,
                timestamp=datetime.utcnow()
            )
            await self.aggregator.record_usage(event1)
            
            # Check if 100 more tokens allowed (Total: 900 <= 1000) -> Should pass
            allowed_1 = await self.budget_manager.enforce_token_limit(
                self.user_id, 
                self.session_id, 
                projected_tokens=100
            )
            self.assertTrue(allowed_1, "Should allow 900/1000 tokens")
            
            # Check if 300 more tokens allowed (Total: 800 + 300 = 1100 > 1000) -> Should fail
            allowed_2 = await self.budget_manager.enforce_token_limit(
                self.user_id, 
                self.session_id, 
                projected_tokens=300
            )
            self.assertFalse(allowed_2, "Should block 1100/1000 tokens")
            
            # Verify details
            result = await self.budget_manager.check_budget_limit(
                self.user_id,
                self.session_id,
                projected_tokens=300
            )
            self.assertFalse(result.within_limit)
            self.assertIn("Daily token limit exceeded", result.reason)

        asyncio.run(run_test())

    def test_cost_limit_enforcement(self):
        async def run_test():
            # Set budget: $1.00 limit
            budget = TokenBudgetConfig(cost_limit_usd=1.00, enforce_limits=True)
            await self.budget_manager.set_budget(self.user_id, budget)
            
            # Record usage: $0.80
            event1 = TokenUsageEvent(
                user_id=self.user_id,
                session_id=self.session_id,
                total_tokens=1000,
                cost_estimate=0.80,
                timestamp=datetime.utcnow()
            )
            await self.aggregator.record_usage(event1)
            
            # Check if $0.15 allowed (Total: $0.95 <= $1.00) -> Should pass
            allowed_1 = await self.budget_manager.enforce_token_limit(
                self.user_id, 
                self.session_id, 
                projected_cost=0.15
            )
            self.assertTrue(allowed_1, "Should allow $0.95/$1.00")
            
            # Check if $0.50 allowed (Total: $1.30 > $1.00) -> Should fail
            allowed_2 = await self.budget_manager.enforce_token_limit(
                self.user_id, 
                self.session_id, 
                projected_cost=0.50
            )
            self.assertFalse(allowed_2, "Should block $1.30/$1.00")

        asyncio.run(run_test())
        
    def test_session_limit_enforcement(self):
        async def run_test():
            # Set budget: 500 tokens per session
            budget = TokenBudgetConfig(session_token_limit=500, enforce_limits=True)
            await self.budget_manager.set_budget(self.user_id, budget)
            
            # Record usage in Session A: 300 tokens
            event_a = TokenUsageEvent(
                user_id=self.user_id, 
                session_id="session_A",
                total_tokens=300
            )
            await self.aggregator.record_usage(event_a)
            
            # Record usage in Session B: 100 tokens
            event_b = TokenUsageEvent(
                user_id=self.user_id, 
                session_id="session_B",
                total_tokens=100
            )
            await self.aggregator.record_usage(event_b)
            
            # Check Session A + 250 (Total 550 > 500) -> Block
            allowed_a = await self.budget_manager.enforce_token_limit(
                self.user_id, 
                "session_A", 
                projected_tokens=250
            )
            self.assertFalse(allowed_a, "Should block session A limit violation")
            
            # Check Session B + 250 (Total 350 < 500) -> Allow, even though user total is high
            allowed_b = await self.budget_manager.enforce_token_limit(
                self.user_id, 
                "session_B", 
                projected_tokens=250
            )
            self.assertTrue(allowed_b, "Should allow session B (within session limit)")

        asyncio.run(run_test())

    def test_alert_recommendations(self):
        async def run_test():
            budget = TokenBudgetConfig(
                daily_token_limit=1000, 
                token_alert_threshold=0.8
            )
            await self.budget_manager.set_budget(self.user_id, budget)
            
            # Use 850 tokens (85%)
            event = TokenUsageEvent(
                user_id=self.user_id,
                total_tokens=850,
                timestamp=datetime.utcnow()
            )
            await self.aggregator.record_usage(event)
            
            # Check budget
            result = await self.budget_manager.check_budget_limit(self.user_id)
            
            found_alert = False
            for rec in result.recommendations:
                if "85.0% of limit" in rec:
                    found_alert = True
            
            self.assertTrue(found_alert, "Should provide alert recommendation when threshold crossed")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
