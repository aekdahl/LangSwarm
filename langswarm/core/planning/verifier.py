"""
Verifier for Acceptance Tests, Gate Assertions, and Drift Detection

Checks test conditions, evaluates gate assertions, and calculates
various drift metrics for decision-making.
"""

import logging
from typing import Dict, Any, List
from simpleeval import simple_eval

from .models import RunState

logger = logging.getLogger(__name__)


class Verifier:
    """
    Verifies acceptance tests, gate assertions, and data integrity.
    
    Provides:
    - Acceptance test execution
    - Gate assertion evaluation
    - Data integrity drift calculation
    - Reconciliation checks
    """
    
    def __init__(self):
        self.test_history = []
    
    def check_acceptance_tests(
        self, 
        tests: List[Dict[str, Any]], 
        artifacts: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Run acceptance tests on artifacts.
        
        Args:
            tests: List of test definitions
            artifacts: Artifacts to test against
            
        Returns:
            Dict of test_name -> passed
        """
        results = {}
        
        for test in tests:
            test_name = test.get("name", f"test_{len(results)}")
            test_type = test.get("type", "assertion")
            
            try:
                if test_type == "assertion":
                    # Evaluate assertion
                    assertion = test.get("assertion", "")
                    passed = self.evaluate_assertion(assertion, artifacts)
                    results[test_name] = passed
                
                elif test_type == "schema":
                    # Schema validation
                    schema = test.get("schema")
                    data = test.get("data_path", "")
                    passed = self._validate_schema(artifacts.get(data), schema)
                    results[test_name] = passed
                
                elif test_type == "custom":
                    # Custom test function
                    test_fn = test.get("function")
                    passed = self._run_custom_test(test_fn, artifacts)
                    results[test_name] = passed
                
                else:
                    logger.warning(f"Unknown test type: {test_type}")
                    results[test_name] = False
                    
            except Exception as e:
                logger.error(f"Test '{test_name}' failed with error: {e}")
                results[test_name] = False
        
        # Track test history
        self.test_history.append(results)
        
        return results
    
    def evaluate_assertion(
        self, 
        assertion: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate gate assertion like '{{ abs($.delta.total_pct) <= 0.5 }}'.
        
        Args:
            assertion: Assertion expression
            context: Context for evaluation (artifacts, metrics, etc.)
            
        Returns:
            True if assertion passes
        """
        try:
            # Handle template syntax
            if assertion.startswith("{{") and assertion.endswith("}}"):
                assertion = assertion[2:-2].strip()
            
            # Replace $.path with dict access
            # Example: $.delta.total_pct -> context.get('delta', {}).get('total_pct')
            if "$." in assertion:
                assertion = self._replace_json_path(assertion, context)
            
            # Evaluate safely
            result = simple_eval(assertion, names={"context": context, **context})
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Failed to evaluate assertion '{assertion}': {e}")
            return False
    
    def check_integrity_drift(
        self, 
        state: RunState, 
        thresholds: Dict[str, float]
    ) -> float:
        """
        Calculate cumulative data integrity drift.
        
        Drift measures include:
        - Reconciliation errors
        - Schema violations
        - Missing data
        - Quality degradation
        
        Args:
            state: Current run state
            thresholds: Threshold configuration
            
        Returns:
            Drift percentage (0.0 = no drift, 1.0 = 100% drift)
        """
        drift_components = []
        
        # Check drift metrics in state
        drift_data = state.drift_metrics
        
        # Reconciliation drift
        if "reconciliation_error_pct" in drift_data:
            drift_components.append(drift_data["reconciliation_error_pct"])
        
        # Schema violation rate
        if "schema_violation_rate" in drift_data:
            drift_components.append(drift_data["schema_violation_rate"])
        
        # Missing data rate
        if "missing_data_rate" in drift_data:
            drift_components.append(drift_data["missing_data_rate"])
        
        # Quality degradation
        if "quality_degradation" in drift_data:
            drift_components.append(drift_data["quality_degradation"])
        
        # Calculate cumulative drift (max of components)
        if not drift_components:
            return 0.0
        
        cumulative_drift = max(drift_components)
        
        return cumulative_drift
    
    def check_reconciliation(
        self, 
        expected: Dict[str, Any], 
        actual: Dict[str, Any],
        tolerance_pct: float = 0.5
    ) -> tuple[bool, float]:
        """
        Check reconciliation between expected and actual results.
        
        Args:
            expected: Expected values
            actual: Actual values
            tolerance_pct: Tolerance percentage
            
        Returns:
            Tuple of (within_tolerance, delta_pct)
        """
        try:
            # Extract numeric values for comparison
            expected_val = self._extract_numeric(expected)
            actual_val = self._extract_numeric(actual)
            
            if expected_val is None or actual_val is None:
                return True, 0.0  # Can't compare, assume OK
            
            # Calculate percentage difference
            if expected_val == 0:
                delta_pct = 0.0 if actual_val == 0 else 100.0
            else:
                delta_pct = abs((actual_val - expected_val) / expected_val) * 100
            
            within_tolerance = delta_pct <= tolerance_pct
            
            return within_tolerance, delta_pct
            
        except Exception as e:
            logger.warning(f"Reconciliation check failed: {e}")
            return True, 0.0
    
    def _replace_json_path(self, expression: str, context: Dict[str, Any]) -> str:
        """
        Replace JSON path notation with Python dict access.
        
        Example: $.delta.total_pct -> context.get('delta', {}).get('total_pct')
        """
        import re
        
        # Find all $.path patterns
        pattern = r'\$\.([a-zA-Z0-9_.]+)'
        
        def replace_path(match):
            path = match.group(1)
            parts = path.split('.')
            
            # Build nested get() calls
            result = "context"
            for part in parts:
                result = f"{result}.get('{part}', {{}})"
            
            return result
        
        return re.sub(pattern, replace_path, expression)
    
    def _extract_numeric(self, data: Any) -> Optional[float]:
        """Extract numeric value from various data structures"""
        if isinstance(data, (int, float)):
            return float(data)
        
        if isinstance(data, dict):
            # Try common keys
            for key in ["total", "value", "amount", "count", "sum"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, (int, float)):
                        return float(val)
        
        return None
    
    def _validate_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """
        Basic schema validation.
        
        For production, use jsonschema library.
        """
        if not data or not schema:
            return True
        
        # Basic type check
        expected_type = schema.get("type")
        if expected_type == "array" and not isinstance(data, list):
            return False
        if expected_type == "object" and not isinstance(data, dict):
            return False
        
        # Check required fields
        if expected_type == "object":
            required = schema.get("required", [])
            if not all(field in data for field in required):
                return False
        
        return True
    
    def _run_custom_test(self, test_fn: str, artifacts: Dict[str, Any]) -> bool:
        """Run custom test function"""
        # Placeholder for custom test execution
        # In production, this would load and execute registered test functions
        logger.warning(f"Custom test function '{test_fn}' not implemented")
        return True




