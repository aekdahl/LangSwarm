# tests/test_util_mixin.py

import unittest
from langswarm.core.wrappers.util_mixin import UtilMixin

class TestUtilMixin(unittest.TestCase):

    def setUp(self):
        self.mixin = UtilMixin()

    def test_model_registry_contains_known_model(self):
        self.assertIn("gpt-4", self.mixin.MODEL_REGISTRY)
        self.assertIsInstance(self.mixin.MODEL_REGISTRY["gpt-4"], dict)

    def test_get_model_details_known_model(self):
        details = self.mixin._get_model_details("gpt-4")
        self.assertEqual(details["name"], "gpt-4")
        self.assertEqual(details["limit"], 8192)
        self.assertEqual(details["ppm"], 0)

    def test_get_model_details_unknown_model(self):
        details = self.mixin._get_model_details("unknown-model", context_limit=12345, ppm=3)
        self.assertEqual(details["name"], "unknown-model")
        self.assertEqual(details["limit"], 12345)
        self.assertEqual(details["ppm"], 3)
        self.assertEqual(details["ppm_out"], 3)

if __name__ == "__main__":
    unittest.main()
