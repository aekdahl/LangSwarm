
import unittest
import asyncio
from unittest.mock import MagicMock

from langswarm.core.middleware.interceptors.token_tracking import TokenTrackingInterceptor
from langswarm.core.middleware.interfaces import IResponseContext

class TestInterceptorCostFallback(unittest.TestCase):
    def setUp(self):
        self.interceptor = TokenTrackingInterceptor(
            enable_budget_enforcement=False,
            enable_context_monitoring=False
        )

    def test_cost_calculation_fallback(self):
        async def run_test():
            # Mock response with usage but NO cost
            response = MagicMock(spec=IResponseContext)
            response.metadata = {
                "token_usage": {
                    "input_tokens": 1000,
                    "output_tokens": 1000,
                    "total_tokens": 2000,
                    "cost_estimate": 0.0 # Explicitly zero
                }
            }
            # Also cover result attribute absence
            response.result = None

            # Call extraction with model name
            usage_info = await self.interceptor._extract_token_usage_from_response(
                response,
                model="gpt-4o"
            )

            # Check if cost was calculated
            # GPT-4o: 1k input ($0.0025) + 1k output ($0.01) = $0.0125
            self.assertIsNotNone(usage_info)
            self.assertEqual(usage_info["input_tokens"], 1000)
            self.assertEqual(usage_info["output_tokens"], 1000)
            self.assertAlmostEqual(usage_info["cost_estimate"], 0.0125)
            
            # Test without model -> Should remain 0.0
            usage_info_no_model = await self.interceptor._extract_token_usage_from_response(
                response,
                model=None
            )
            self.assertEqual(usage_info_no_model["cost_estimate"], 0.0)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
