"""
Navigation Configuration Utilities

This module provides utility functions for creating, validating, and managing
navigation configurations programmatically.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .schema import (
    NavigationConfigBuilder, NavigationConfigLoader, NavigationSchemaValidator,
    NavigationMode, ConditionOperator, NavigationCondition,
    create_navigation_config, validate_navigation_config, load_navigation_config
)


def create_basic_support_routing() -> Dict[str, Any]:
    """Create a basic customer support routing configuration"""
    config = (create_navigation_config()
              .set_mode(NavigationMode.HYBRID)
              .add_condition_step(
                  "technical_support", 
                  "Technical Support",
                  "Route technical issues to specialized support team",
                  "output.category", "eq", "technical"
              )
              .add_condition_step(
                  "billing_support",
                  "Billing Support", 
                  "Route billing and payment issues to billing team",
                  "output.category", "eq", "billing"
              )
              .add_step(
                  "general_support",
                  "General Support",
                  "Handle general inquiries and miscellaneous issues"
              )
              .set_fallback("general_support")
              .set_timeout(30)
              .set_tracking(True))
    
    # Add escalation rule for critical issues
    critical_condition = NavigationCondition(
        field="output.priority",
        operator=ConditionOperator.EQUALS,
        value="critical",
        description="Critical priority issues require immediate escalation"
    )
    
    config.add_rule("technical_support", [critical_condition], priority=10, 
                   description="Auto-escalate critical issues")
    
    return config.build().to_dict()


def create_ecommerce_routing() -> Dict[str, Any]:
    """Create an e-commerce navigation configuration"""
    config = (create_navigation_config()
              .set_mode(NavigationMode.HYBRID)
              .add_condition_step(
                  "order_management",
                  "Order Management",
                  "Handle order status, shipping, and delivery issues",
                  "output.intent", "contains", "order"
              )
              .add_condition_step(
                  "product_support",
                  "Product Support", 
                  "Handle product questions, returns, and exchanges",
                  "output.intent", "contains", "product"
              )
              .add_condition_step(
                  "payment_issues",
                  "Payment Issues",
                  "Handle payment problems and refund requests",
                  "output.category", "eq", "payment"
              )
              .add_step(
                  "sales_inquiry",
                  "Sales Inquiry", 
                  "Handle pre-purchase questions and product recommendations",
                  weight=1.5  # Higher weight for sales opportunities
              )
              .set_fallback("sales_inquiry")
              .set_timeout(25))
    
    # Add VIP customer rule
    vip_condition = NavigationCondition(
        field="output.customer_tier",
        operator=ConditionOperator.EQUALS,
        value="vip",
        description="VIP customers get priority routing"
    )
    
    config.add_rule("order_management", [vip_condition], priority=9,
                   description="VIP customers routed to premium support")
    
    return config.build().to_dict()


def create_it_helpdesk_routing() -> Dict[str, Any]:
    """Create an IT helpdesk navigation configuration"""
    config = (create_navigation_config()
              .set_mode(NavigationMode.CONDITIONAL)
              .add_condition_step(
                  "password_reset",
                  "Password Reset",
                  "Automated password reset and account recovery",
                  "output.issue_type", "eq", "password"
              )
              .add_condition_step(
                  "software_support",
                  "Software Support",
                  "Application issues and software troubleshooting", 
                  "output.category", "eq", "software"
              )
              .add_condition_step(
                  "hardware_support",
                  "Hardware Support",
                  "Hardware problems and equipment requests",
                  "output.category", "eq", "hardware"
              )
              .add_condition_step(
                  "network_issues",
                  "Network Issues",
                  "Connectivity and network-related problems",
                  "output.category", "eq", "network"
              )
              .add_step(
                  "general_it_support",
                  "General IT Support",
                  "Miscellaneous IT issues and general help"
              )
              .set_fallback("general_it_support")
              .set_timeout(20))
    
    # Add urgent escalation rule
    urgent_condition = NavigationCondition(
        field="output.urgency",
        operator=ConditionOperator.IN,
        value=["urgent", "critical"],
        description="Urgent issues need immediate attention"
    )
    
    config.add_rule("general_it_support", [urgent_condition], priority=10,
                   description="Escalate urgent issues immediately")
    
    return config.build().to_dict()


def validate_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Validate a navigation configuration file"""
    try:
        config = load_navigation_config(file_path)
        return {
            "valid": True,
            "config": config.to_dict(),
            "errors": [],
            "warnings": []
        }
    except Exception as e:
        return {
            "valid": False,
            "config": None,
            "errors": [str(e)],
            "warnings": []
        }


def generate_config_template(template_type: str = "basic") -> str:
    """Generate a configuration template"""
    templates = {
        "basic": create_basic_support_routing,
        "ecommerce": create_ecommerce_routing,
        "it_helpdesk": create_it_helpdesk_routing
    }
    
    if template_type not in templates:
        available = ", ".join(templates.keys())
        raise ValueError(f"Unknown template type: {template_type}. Available: {available}")
    
    config_dict = templates[template_type]()
    return yaml.dump(config_dict, default_flow_style=False, sort_keys=False)


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two navigation configurations, with override taking precedence"""
    merged = base_config.copy()
    
    # Simple merge for top-level fields
    for key, value in override_config.items():
        if key == "available_steps":
            # Merge steps by ID
            base_steps = {step["id"]: step for step in merged.get("available_steps", [])}
            override_steps = {step["id"]: step for step in value}
            base_steps.update(override_steps)
            merged["available_steps"] = list(base_steps.values())
        elif key == "rules":
            # Append rules (they have priorities to handle conflicts)
            merged["rules"] = merged.get("rules", []) + value
        elif key == "metadata":
            # Merge metadata dictionaries
            merged_metadata = merged.get("metadata", {})
            merged_metadata.update(value)
            merged["metadata"] = merged_metadata
        else:
            # Direct override for other fields
            merged[key] = value
    
    return merged


def convert_config_format(input_file: Union[str, Path], output_file: Union[str, Path]) -> None:
    """Convert configuration between YAML and JSON formats"""
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    # Load configuration
    config = load_navigation_config(input_path)
    config_dict = config.to_dict()
    
    # Save in target format
    if output_path.suffix.lower() in ['.yml', '.yaml']:
        with open(output_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    elif output_path.suffix.lower() == '.json':
        with open(output_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    else:
        raise ValueError(f"Unsupported output format: {output_path.suffix}")


def list_template_files() -> List[Dict[str, Any]]:
    """List available navigation configuration templates"""
    templates_dir = Path(__file__).parent / "templates"
    templates = []
    
    if templates_dir.exists():
        for template_file in templates_dir.glob("*.yaml"):
            try:
                config = load_navigation_config(template_file)
                templates.append({
                    "name": template_file.stem,
                    "file": str(template_file),
                    "mode": config.mode.value,
                    "steps_count": len(config.available_steps),
                    "rules_count": len(config.rules),
                    "description": config.metadata.get("description", "No description")
                })
            except Exception as e:
                templates.append({
                    "name": template_file.stem,
                    "file": str(template_file),
                    "error": str(e)
                })
    
    return templates


def optimize_config_for_performance(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize configuration for better performance"""
    optimized = config_dict.copy()
    
    # Reduce timeout for simple configurations
    step_count = len(optimized.get("available_steps", []))
    if step_count <= 3:
        optimized["timeout_seconds"] = min(optimized.get("timeout_seconds", 30), 15)
    
    # Enable tracking for configurations without it
    if "tracking_enabled" not in optimized:
        optimized["tracking_enabled"] = True
    
    # Add performance metadata
    if "metadata" not in optimized:
        optimized["metadata"] = {}
    
    optimized["metadata"]["performance_optimized"] = True
    optimized["metadata"]["optimization_timestamp"] = "auto-generated"
    
    return optimized


def get_config_summary(config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
    """Get a summary of a navigation configuration"""
    if isinstance(config, (str, Path)):
        config_obj = load_navigation_config(config)
        config_dict = config_obj.to_dict()
    else:
        config_dict = config
        config_obj = load_navigation_config(config_dict)
    
    # Count different types of steps
    steps = config_dict.get("available_steps", [])
    conditional_steps = len([s for s in steps if s.get("conditions")])
    weighted_steps = len([s for s in steps if s.get("weight", 1.0) != 1.0])
    
    return {
        "mode": config_dict.get("mode", "manual"),
        "total_steps": len(steps),
        "conditional_steps": conditional_steps,
        "weighted_steps": weighted_steps,
        "rules_count": len(config_dict.get("rules", [])),
        "has_fallback": config_dict.get("fallback_step") is not None,
        "timeout_seconds": config_dict.get("timeout_seconds", 30),
        "tracking_enabled": config_dict.get("tracking_enabled", True),
        "analytics_enabled": config_dict.get("analytics_enabled", True),
        "complexity": _assess_complexity(config_dict),
        "use_case": config_dict.get("metadata", {}).get("use_case", "unknown")
    }


def _assess_complexity(config_dict: Dict[str, Any]) -> str:
    """Assess the complexity level of a configuration"""
    score = 0
    
    # Base complexity from mode
    mode_scores = {"manual": 1, "conditional": 2, "hybrid": 3, "weighted": 2}
    score += mode_scores.get(config_dict.get("mode", "manual"), 1)
    
    # Add complexity from features
    if config_dict.get("rules"):
        score += len(config_dict["rules"])
    
    steps = config_dict.get("available_steps", [])
    conditional_steps = len([s for s in steps if s.get("conditions")])
    score += conditional_steps
    
    if config_dict.get("prompt_template"):
        score += 1
    
    # Categorize complexity
    if score <= 3:
        return "simple"
    elif score <= 8:
        return "moderate"
    else:
        return "complex"


# CLI-style functions for easy usage
def create_template(template_type: str, output_file: Optional[str] = None) -> str:
    """Create a configuration template"""
    template_yaml = generate_config_template(template_type)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(template_yaml)
        return f"Template saved to {output_file}"
    else:
        return template_yaml


def validate_file(file_path: str) -> str:
    """Validate a configuration file and return results"""
    result = validate_config_file(file_path)
    
    if result["valid"]:
        summary = get_config_summary(result["config"])
        return f"✅ Configuration is valid\nComplexity: {summary['complexity']}\nSteps: {summary['total_steps']}\nMode: {summary['mode']}"
    else:
        errors = "\n".join(f"  - {error}" for error in result["errors"])
        return f"❌ Configuration is invalid:\n{errors}"


def list_templates() -> str:
    """List available templates"""
    templates = list_template_files()
    
    if not templates:
        return "No templates found in templates directory"
    
    result = "Available navigation configuration templates:\n\n"
    for template in templates:
        if "error" in template:
            result += f"❌ {template['name']}: {template['error']}\n"
        else:
            result += f"✅ {template['name']}: {template['description']}\n"
            result += f"   Mode: {template['mode']}, Steps: {template['steps_count']}, Rules: {template['rules_count']}\n\n"
    
    return result 