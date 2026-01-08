
import unittest
from langswarm.core.observability.cost_estimator import CostEstimator

class TestCostEstimator(unittest.TestCase):
    def test_known_models(self):
        # GPT-4o (Input $2.50/1M, Output $10.00/1M) -> ($0.0025/1k, $0.01/1k)
        cost = CostEstimator.estimate_cost("gpt-4o", 1000, 1000)
        self.assertAlmostEqual(cost, 0.0125)
        
        # GPT-4o Mini (Input $0.15/1M, Output $0.60/1M) -> ($0.00015/1k, $0.0006/1k)
        cost = CostEstimator.estimate_cost("gpt-4o-mini", 1000, 1000)
        self.assertAlmostEqual(cost, 0.00075)
        
        # Claude 3.5 Sonnet (Input $3/1M, Output $15/1M) -> ($0.003/1k, $0.015/1k)
        cost = CostEstimator.estimate_cost("claude-3-5-sonnet-20240620", 1000, 1000)
        self.assertAlmostEqual(cost, 0.018)

    def test_fallback_logic(self):
        # Versioned model not explicitly in map but prefix matches
        # Assuming gpt-4o-future-version falls back to gpt-4o price if implemented that way
        # Currently the code has a fallback loop:
        # for key in cls._RATES: if model.startswith(key): ...
        
        # Test accurate fallback
        cost = CostEstimator.estimate_cost("gpt-4o-custom-finetune", 1000, 1000)
        # Should match gpt-4o
        self.assertAlmostEqual(cost, 0.0125)

    def test_unknown_model(self):
        cost = CostEstimator.estimate_cost("unknown-model-123", 1000, 1000)
        self.assertEqual(cost, 0.0)

    def test_zero_tokens(self):
        cost = CostEstimator.estimate_cost("gpt-4o", 0, 0)
        self.assertEqual(cost, 0.0)

if __name__ == '__main__':
    unittest.main()
