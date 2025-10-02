"""
Tests for Navigation Configuration Schema

This module tests the configuration schema system including:
- Schema validation
- Configuration building
- Loading and parsing
- Utility functions
"""

import pytest
import json
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any

from ..schema import (
    NavigationConfig, NavigationConfigBuilder, NavigationConfigLoader,
    NavigationSchemaValidator, NavigationMode, ConditionOperator,
    NavigationCondition, NavigationRule, NavigationStep,
    create_navigation_config, validate_navigation_config, 
    load_navigation_config, get_navigation_schema
)
from ..config_utils import (
    create_basic_support_routing, create_ecommerce_routing,
    validate_config_file, generate_config_template,
    get_config_summary, optimize_config_for_performance
)


class TestNavigationSchema:
    """Test the core schema components"""
    
    def test_navigation_condition_creation(self):
        """Test NavigationCondition creation and serialization"""
        condition = NavigationCondition(
            field="output.category",
            operator=ConditionOperator.EQUALS,
            value="technical",
            description="Technical issue condition"
        )
        
        assert condition.field == "output.category"
        assert condition.operator == ConditionOperator.EQUALS
        assert condition.value == "technical"
        assert condition.description == "Technical issue condition"
        
        # Test serialization
        condition_dict = condition.to_dict()
        assert condition_dict["field"] == "output.category"
        assert condition_dict["operator"] == "eq"
        assert condition_dict["value"] == "technical"
    
    def test_navigation_step_creation(self):
        """Test NavigationStep creation and serialization"""
        condition = NavigationCondition("output.category", ConditionOperator.EQUALS, "technical")
        
        step = NavigationStep(
            id="technical_support",
            name="Technical Support",
            description="Handle technical issues",
            conditions=[condition],
            weight=1.5,
            metadata={"department": "tech"}
        )
        
        assert step.id == "technical_support"
        assert step.name == "Technical Support"
        assert len(step.conditions) == 1
        assert step.weight == 1.5
        assert step.metadata["department"] == "tech"
        
        # Test serialization
        step_dict = step.to_dict()
        assert step_dict["id"] == "technical_support"
        assert len(step_dict["conditions"]) == 1
        assert step_dict["weight"] == 1.5
    
    def test_navigation_rule_creation(self):
        """Test NavigationRule creation and serialization"""
        condition = NavigationCondition("output.priority", ConditionOperator.EQUALS, "critical")
        
        rule = NavigationRule(
            conditions=[condition],
            target_step="escalate",
            priority=10,
            description="Escalate critical issues"
        )
        
        assert len(rule.conditions) == 1
        assert rule.target_step == "escalate"
        assert rule.priority == 10
        
        # Test serialization
        rule_dict = rule.to_dict()
        assert rule_dict["target_step"] == "escalate"
        assert rule_dict["priority"] == 10
        assert len(rule_dict["conditions"]) == 1


class TestNavigationSchemaValidator:
    """Test schema validation functionality"""
    
    def setup_method(self):
        """Set up test validator"""
        self.validator = NavigationSchemaValidator()
    
    def test_valid_basic_config(self):
        """Test validation of a basic valid configuration"""
        config = {
            "mode": "manual",
            "available_steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step"
                }
            ]
        }
        
        # Should not raise an exception
        self.validator.validate(config)
    
    def test_missing_required_field(self):
        """Test validation fails for missing required fields"""
        config = {
            "mode": "manual"
            # Missing available_steps
        }
        
        with pytest.raises(ValueError, match="available_steps.*required"):
            self.validator.validate(config)
    
    def test_invalid_mode(self):
        """Test validation fails for invalid mode"""
        config = {
            "mode": "invalid_mode",
            "available_steps": [
                {"id": "step1", "name": "Step 1", "description": "Test step"}
            ]
        }
        
        with pytest.raises(ValueError):
            self.validator.validate(config)
    
    def test_invalid_step_id(self):
        """Test validation fails for invalid step ID format"""
        config = {
            "mode": "manual",
            "available_steps": [
                {
                    "id": "123invalid",  # Can't start with number
                    "name": "Invalid Step",
                    "description": "Step with invalid ID"
                }
            ]
        }
        
        with pytest.raises(ValueError):
            self.validator.validate(config)
    
    def test_invalid_operator(self):
        """Test validation fails for invalid condition operator"""
        config = {
            "mode": "manual",
            "available_steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Test step",
                    "conditions": [
                        {
                            "field": "output.test",
                            "operator": "invalid_operator",
                            "value": "test"
                        }
                    ]
                }
            ]
        }
        
        with pytest.raises(ValueError):
            self.validator.validate(config)
    
    def test_valid_complex_config(self):
        """Test validation of a complex configuration"""
        config = {
            "mode": "hybrid",
            "available_steps": [
                {
                    "id": "technical_support",
                    "name": "Technical Support",
                    "description": "Handle technical issues",
                    "conditions": [
                        {
                            "field": "output.category",
                            "operator": "eq",
                            "value": "technical"
                        }
                    ],
                    "weight": 1.5,
                    "metadata": {"department": "tech"}
                },
                {
                    "id": "general_support",
                    "name": "General Support",
                    "description": "Handle general issues"
                }
            ],
            "rules": [
                {
                    "conditions": [
                        {
                            "field": "output.priority",
                            "operator": "eq",
                            "value": "critical"
                        }
                    ],
                    "target_step": "technical_support",
                    "priority": 10
                }
            ],
            "fallback_step": "general_support",
            "timeout_seconds": 45,
            "tracking_enabled": True
        }
        
        # Should not raise an exception
        self.validator.validate(config)


class TestNavigationConfigBuilder:
    """Test the configuration builder"""
    
    def test_basic_config_building(self):
        """Test building a basic configuration"""
        config = (create_navigation_config()
                  .set_mode(NavigationMode.MANUAL)
                  .add_step("step1", "Step 1", "First step")
                  .add_step("step2", "Step 2", "Second step")
                  .set_fallback("step1")
                  .build())
        
        assert config.mode == NavigationMode.MANUAL
        assert len(config.available_steps) == 2
        assert config.fallback_step == "step1"
    
    def test_conditional_step_building(self):
        """Test building steps with conditions"""
        config = (create_navigation_config()
                  .add_condition_step(
                      "tech_step", "Tech Step", "Technical step",
                      "output.category", "eq", "technical"
                  )
                  .build())
        
        assert len(config.available_steps) == 1
        step = config.available_steps[0]
        assert step.id == "tech_step"
        assert len(step.conditions) == 1
        assert step.conditions[0].field == "output.category"
    
    def test_rule_building(self):
        """Test adding rules to configuration"""
        condition = NavigationCondition("output.priority", ConditionOperator.EQUALS, "high")
        
        config = (create_navigation_config()
                  .add_step("step1", "Step 1", "First step")
                  .add_rule("step1", [condition], priority=5, description="High priority rule")
                  .build())
        
        assert len(config.rules) == 1
        rule = config.rules[0]
        assert rule.target_step == "step1"
        assert rule.priority == 5
    
    def test_yaml_export(self):
        """Test exporting configuration as YAML"""
        builder = (create_navigation_config()
                   .add_step("step1", "Step 1", "First step")
                   .set_fallback("step1"))
        
        yaml_output = builder.to_yaml()
        assert "mode: manual" in yaml_output
        assert "step1" in yaml_output
        
        # Verify it's valid YAML
        parsed = yaml.safe_load(yaml_output)
        assert parsed["mode"] == "manual"
    
    def test_json_export(self):
        """Test exporting configuration as JSON"""
        builder = (create_navigation_config()
                   .add_step("step1", "Step 1", "First step"))
        
        json_output = builder.to_json()
        
        # Verify it's valid JSON
        parsed = json.loads(json_output)
        assert parsed["mode"] == "manual"
        assert len(parsed["available_steps"]) == 1


class TestNavigationConfigLoader:
    """Test configuration loading and parsing"""
    
    def setup_method(self):
        """Set up test loader"""
        self.loader = NavigationConfigLoader()
    
    def test_load_from_dict(self):
        """Test loading configuration from dictionary"""
        config_dict = {
            "mode": "manual",
            "available_steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "conditions": [
                        {
                            "field": "output.test",
                            "operator": "eq",
                            "value": "value"
                        }
                    ]
                }
            ],
            "fallback_step": "step1"
        }
        
        config = self.loader.load_from_dict(config_dict)
        
        assert config.mode == NavigationMode.MANUAL
        assert len(config.available_steps) == 1
        assert config.fallback_step == "step1"
        
        step = config.available_steps[0]
        assert step.id == "step1"
        assert len(step.conditions) == 1
    
    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file"""
        config_dict = {
            "mode": "hybrid",
            "available_steps": [
                {"id": "step1", "name": "Step 1", "description": "Test step"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            config = self.loader.load_from_yaml(temp_path)
            assert config.mode == NavigationMode.HYBRID
            assert len(config.available_steps) == 1
        finally:
            Path(temp_path).unlink()
    
    def test_load_from_json_file(self):
        """Test loading configuration from JSON file"""
        config_dict = {
            "mode": "conditional",
            "available_steps": [
                {"id": "step1", "name": "Step 1", "description": "Test step"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f)
            temp_path = f.name
        
        try:
            config = self.loader.load_from_json(temp_path)
            assert config.mode == NavigationMode.CONDITIONAL
            assert len(config.available_steps) == 1
        finally:
            Path(temp_path).unlink()


class TestConfigUtilities:
    """Test configuration utility functions"""
    
    def test_create_basic_support_routing(self):
        """Test creating basic support routing configuration"""
        config_dict = create_basic_support_routing()
        
        assert config_dict["mode"] == "hybrid"
        assert len(config_dict["available_steps"]) >= 3
        assert config_dict["fallback_step"] is not None
        
        # Validate the generated configuration
        validate_navigation_config(config_dict)
    
    def test_create_ecommerce_routing(self):
        """Test creating e-commerce routing configuration"""
        config_dict = create_ecommerce_routing()
        
        assert config_dict["mode"] == "hybrid"
        assert len(config_dict["available_steps"]) >= 3
        assert len(config_dict["rules"]) >= 1
        
        # Validate the generated configuration
        validate_navigation_config(config_dict)
    
    def test_generate_config_template(self):
        """Test generating configuration templates"""
        # Test basic template
        basic_yaml = generate_config_template("basic")
        basic_config = yaml.safe_load(basic_yaml)
        validate_navigation_config(basic_config)
        
        # Test ecommerce template
        ecommerce_yaml = generate_config_template("ecommerce")
        ecommerce_config = yaml.safe_load(ecommerce_yaml)
        validate_navigation_config(ecommerce_config)
        
        # Test invalid template
        with pytest.raises(ValueError):
            generate_config_template("invalid_template")
    
    def test_validate_config_file(self):
        """Test configuration file validation"""
        # Create a valid config file
        config_dict = {
            "mode": "manual",
            "available_steps": [
                {"id": "step1", "name": "Step 1", "description": "Test step"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            result = validate_config_file(temp_path)
            assert result["valid"] is True
            assert len(result["errors"]) == 0
        finally:
            Path(temp_path).unlink()
    
    def test_get_config_summary(self):
        """Test getting configuration summary"""
        config_dict = {
            "mode": "hybrid",
            "available_steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Test step",
                    "conditions": [
                        {"field": "output.test", "operator": "eq", "value": "test"}
                    ]
                },
                {
                    "id": "step2",
                    "name": "Step 2",
                    "description": "Another step",
                    "weight": 2.0
                }
            ],
            "rules": [
                {
                    "conditions": [
                        {"field": "output.priority", "operator": "eq", "value": "high"}
                    ],
                    "target_step": "step1"
                }
            ],
            "fallback_step": "step2"
        }
        
        summary = get_config_summary(config_dict)
        
        assert summary["mode"] == "hybrid"
        assert summary["total_steps"] == 2
        assert summary["conditional_steps"] == 1
        assert summary["weighted_steps"] == 1
        assert summary["rules_count"] == 1
        assert summary["has_fallback"] is True
        assert summary["complexity"] in ["simple", "moderate", "complex"]
    
    def test_optimize_config_for_performance(self):
        """Test configuration optimization"""
        config_dict = {
            "mode": "manual",
            "available_steps": [
                {"id": "step1", "name": "Step 1", "description": "Test step"}
            ],
            "timeout_seconds": 60
        }
        
        optimized = optimize_config_for_performance(config_dict)
        
        # Should reduce timeout for simple configs
        assert optimized["timeout_seconds"] < config_dict["timeout_seconds"]
        assert optimized["tracking_enabled"] is True
        assert optimized["metadata"]["performance_optimized"] is True


class TestSchemaIntegration:
    """Integration tests for the complete schema system"""
    
    def test_end_to_end_config_creation(self):
        """Test complete configuration creation workflow"""
        # Build configuration
        config = (create_navigation_config()
                  .set_mode("hybrid")
                  .add_condition_step(
                      "tech_support", "Technical Support", 
                      "Handle technical issues",
                      "output.category", "eq", "technical"
                  )
                  .add_step("general_support", "General Support", "Handle general issues")
                  .set_fallback("general_support")
                  .set_timeout(30)
                  .build())
        
        # Convert to dictionary
        config_dict = config.to_dict()
        
        # Validate
        validate_navigation_config(config_dict)
        
        # Export and re-import
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f, default_flow_style=False)
            temp_path = f.name
        
        try:
            # Load back from file
            loaded_config = load_navigation_config(temp_path)
            
            # Verify it matches original
            assert loaded_config.mode == config.mode
            assert len(loaded_config.available_steps) == len(config.available_steps)
            assert loaded_config.fallback_step == config.fallback_step
            
        finally:
            Path(temp_path).unlink()
    
    def test_schema_export_and_validation(self):
        """Test schema export and external validation"""
        schema = get_navigation_schema()
        
        # Schema should be valid JSON Schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert "properties" in schema
        assert "definitions" in schema
        
        # Test validation with external jsonschema library
        import jsonschema
        
        valid_config = {
            "mode": "manual",
            "available_steps": [
                {"id": "step1", "name": "Step 1", "description": "Test step"}
            ]
        }
        
        # Should not raise an exception
        jsonschema.validate(valid_config, schema)


if __name__ == "__main__":
    pytest.main([__file__]) 