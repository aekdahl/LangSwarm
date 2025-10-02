#!/usr/bin/env python3
"""
Simple test for LangSwarm V2 Cost Management System

This script tests the cost management system using the correct interface definitions.
"""

import sys
from datetime import datetime
from decimal import Decimal

# Add current directory to path
sys.path.insert(0, '.')

try:
    # Import cost components directly
    from langswarm.v2.core.agents.cost.interfaces import (
        CostEntry, CostSummary, CostBudget, CostCategory, BillingPeriod, CostAlertType
    )
    from langswarm.v2.core.agents.cost.tracker import CostTracker
    from langswarm.v2.core.agents.cost.manager import CostManagementSystem
    
    print("✅ Successfully imported cost management components!")
    
    # Test CostEntry creation with correct fields
    cost_entry = CostEntry(
        provider="openai",
        model="gpt-4o",
        category=CostCategory.API_CALLS,
        amount=0.05,  # Using float instead of Decimal for now
        input_tokens=800,  # Using correct field name
        output_tokens=200,  # Using correct field name
        total_tokens=1000,
        user_id="user123",
        department="engineering"
    )
    print(f"✅ CostEntry created: {cost_entry.provider}, ${cost_entry.amount}")
    print(f"  Tokens: {cost_entry.input_tokens} in + {cost_entry.output_tokens} out = {cost_entry.total_tokens} total")
    print(f"  Cost per token: ${cost_entry.cost_per_token:.6f}")
    
    # Test CostBudget creation
    budget = CostBudget(
        id="budget123",
        name="Monthly Engineering Budget",
        amount=1000.0,
        period=BillingPeriod.MONTHLY,
        department="engineering"
    )
    print(f"✅ CostBudget created: {budget.name}, ${budget.amount}")
    
    # Test CostTracker
    tracker = CostTracker()
    tracker.record_cost(cost_entry)
    
    # Create another cost entry
    cost_entry2 = CostEntry(
        provider="anthropic",
        model="claude-3-opus",
        category=CostCategory.API_CALLS,
        amount=0.08,
        input_tokens=900,
        output_tokens=300,
        total_tokens=1200,
        user_id="user456",
        department="product"
    )
    tracker.record_cost(cost_entry2)
    
    # Get summary
    summary = tracker.get_summary()
    print(f"✅ Cost summary: ${summary.total_cost}, {summary.total_entries} entries")
    print(f"  Providers: {list(summary.provider_costs.keys())}")
    print(f"  Total tokens: {summary.total_tokens}")
    
    # Test department costs
    dept_costs = tracker.get_costs_by_department()
    print(f"✅ Department costs: {dict(dept_costs)}")
    
    # Test enum values
    print(f"✅ Cost categories: {[cat.value for cat in CostCategory][:5]}...")
    print(f"✅ Billing periods: {[period.value for period in BillingPeriod]}")
    print(f"✅ Alert types: {[alert.value for alert in CostAlertType][:3]}...")
    
    # Test CostManagementSystem
    config = {
        'tracker': {'type': 'standard'},
        'budget_manager': {'default_thresholds': {'warning': 0.8, 'critical': 0.9}},
    }
    
    cost_mgmt = CostManagementSystem(config)
    print(f"✅ Cost management system created: {type(cost_mgmt).__name__}")
    
    # Record cost through integrated system
    cost_mgmt.cost_tracker.record_cost(cost_entry)
    dashboard_data = cost_mgmt.get_dashboard_data()
    print(f"✅ Dashboard data retrieved")
    print(f"  Current costs: ${dashboard_data['current_costs']['total_cost']}")
    print(f"  Total entries: {dashboard_data['current_costs']['total_entries']}")
    
    print("\n🎉 Cost Management System Basic Test - PASSED!")
    print("🚀 Core functionality is working correctly!")
    
except Exception as e:
    print(f"❌ Cost management test failed: {str(e)}")
    import traceback
    traceback.print_exc()
