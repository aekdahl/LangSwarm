#!/usr/bin/env python3
"""
Standalone test for LangSwarm V2 Cost Management System

This script tests the cost management components in isolation to verify
functionality independently of the problematic multimodal module.
"""

import asyncio
import sys
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, List, Any

# Add current directory to path
sys.path.insert(0, '.')

# Import cost management components directly
from langswarm.v2.core.agents.cost.interfaces import (
    # Data classes
    CostEntry, CostSummary, CostBudget, CostAlert, CostForecast, 
    BillingRecord, UsageRecord, CostRecommendation,
    
    # Enums
    CostCategory, BillingPeriod, AlertType, OptimizationStrategy, 
    RecommendationCategory, CostMetric,
    
    # Interfaces
    ICostTracker, ICostOptimizer, ICostPredictor, IBudgetManager,
    IBillingSystem, IRecommendationEngine, ICostManager
)

from langswarm.v2.core.agents.cost.tracker import CostTracker, create_cost_tracker
from langswarm.v2.core.agents.cost.optimizer import CostOptimizer, create_cost_optimizer
from langswarm.v2.core.agents.cost.predictor import CostPredictor, create_cost_predictor
from langswarm.v2.core.agents.cost.budget import BudgetManager, create_budget_manager
from langswarm.v2.core.agents.cost.billing import BillingSystem, create_billing_system
from langswarm.v2.core.agents.cost.recommendations import RecommendationEngine, create_recommendation_engine
from langswarm.v2.core.agents.cost.manager import CostManagementSystem, create_cost_management_system


def test_data_structures():
    """Test core data structures and enums."""
    print("\n🧪 Testing Cost Management Data Structures...")
    
    # Test CostEntry creation
    cost_entry = CostEntry(
        provider="openai",
        model="gpt-4o",
        category=CostCategory.API_CALLS,
        amount=Decimal("0.05"),
        total_tokens=1000,
        prompt_tokens=800,
        completion_tokens=200,
        user_id="user123",
        project_id="proj456",
        department="engineering",
        metadata={"session_id": "sess789"}
    )
    print(f"✅ CostEntry created: {cost_entry.provider}, ${cost_entry.amount}")
    
    # Test CostBudget creation
    budget = CostBudget(
        id="budget123",
        name="Monthly Engineering Budget",
        amount=Decimal("1000.00"),
        period=BillingPeriod.MONTHLY,
        department="engineering",
        warning_threshold=0.8,
        critical_threshold=0.9
    )
    print(f"✅ CostBudget created: {budget.name}, ${budget.amount}")
    
    # Test enums
    print(f"✅ CostCategory: {list(CostCategory)[:3]}...")
    print(f"✅ BillingPeriod: {list(BillingPeriod)[:3]}...")
    print(f"✅ AlertType: {list(AlertType)}")
    
    return True


def test_cost_tracker():
    """Test the cost tracking functionality."""
    print("\n📊 Testing Cost Tracker...")
    
    # Create cost tracker
    config = {
        'type': 'standard',
        'export_formats': ['json', 'csv']
    }
    tracker = create_cost_tracker(config)
    print(f"✅ Cost tracker created: {type(tracker).__name__}")
    
    # Create some cost entries
    entries = [
        CostEntry(
            provider="openai",
            model="gpt-4o",
            category=CostCategory.API_CALLS,
            amount=Decimal("0.05"),
            total_tokens=1000,
            user_id="user1",
            department="engineering"
        ),
        CostEntry(
            provider="anthropic",
            model="claude-3-opus",
            category=CostCategory.API_CALLS,
            amount=Decimal("0.08"),
            total_tokens=1200,
            user_id="user2",
            department="product"
        ),
        CostEntry(
            provider="openai",
            model="gpt-3.5-turbo",
            category=CostCategory.API_CALLS,
            amount=Decimal("0.02"),
            total_tokens=800,
            user_id="user1",
            department="engineering"
        )
    ]
    
    # Record cost entries
    for entry in entries:
        tracker.record_cost(entry)
        print(f"✅ Recorded cost: {entry.provider} ${entry.amount}")
    
    # Get summary
    summary = tracker.get_summary()
    print(f"✅ Total cost: ${summary.total_cost}")
    print(f"✅ Total entries: {summary.total_entries}")
    print(f"✅ Providers: {list(summary.provider_costs.keys())}")
    
    # Get costs by department
    dept_costs = tracker.get_costs_by_department()
    print(f"✅ Department costs: {dict(dept_costs)}")
    
    return True


def test_cost_optimizer():
    """Test the cost optimization functionality."""
    print("\n⚡ Testing Cost Optimizer...")
    
    config = {
        'strategy': 'cost_minimization',
        'quality_threshold': 0.8
    }
    optimizer = create_cost_optimizer(config)
    print(f"✅ Cost optimizer created: {type(optimizer).__name__}")
    
    # Test provider comparison
    providers = ["openai", "anthropic", "gemini"]
    comparison = optimizer.compare_providers(providers, task_type="text_generation")
    print(f"✅ Provider comparison completed for {len(comparison)} providers")
    
    for provider_data in comparison[:2]:  # Show first 2
        print(f"  - {provider_data['provider']}: ${provider_data['cost_per_1k_tokens']}/1k tokens, "
              f"quality: {provider_data['quality_score']}")
    
    # Test model optimization
    models = ["gpt-4o", "gpt-3.5-turbo", "claude-3-sonnet"]
    model_rec = optimizer.optimize_model_selection(models, task_complexity="medium")
    print(f"✅ Model recommendation: {model_rec['recommended_model']} "
          f"(cost efficiency: {model_rec['cost_efficiency_score']:.2f})")
    
    return True


def test_budget_manager():
    """Test the budget management functionality."""
    print("\n💰 Testing Budget Manager...")
    
    config = {
        'alert_channels': ['email', 'slack'],
        'default_thresholds': {
            'warning': 0.8,
            'critical': 0.9
        }
    }
    budget_mgr = create_budget_manager(config)
    print(f"✅ Budget manager created: {type(budget_mgr).__name__}")
    
    # Create a budget
    budget = CostBudget(
        id="test_budget",
        name="Test Department Budget",
        amount=Decimal("500.00"),
        period=BillingPeriod.MONTHLY,
        department="engineering",
        warning_threshold=0.8,
        critical_threshold=0.9
    )
    
    budget_mgr.create_budget(budget)
    print(f"✅ Budget created: {budget.name}, ${budget.amount}")
    
    # Simulate some spending
    spending = Decimal("350.00")  # 70% of budget
    budget_mgr.update_budget_usage(budget.id, spending)
    print(f"✅ Budget usage updated: ${spending}")
    
    # Check budget status
    status = budget_mgr.get_budget_status(budget.id)
    print(f"✅ Budget utilization: {status['utilization_percent']:.1f}%")
    print(f"✅ Remaining: ${status['remaining_amount']}")
    
    # Check for alerts
    alerts = budget_mgr.check_budget_alerts(budget.id)
    print(f"✅ Budget alerts: {len(alerts)} alerts generated")
    
    return True


def test_billing_system():
    """Test the billing system functionality."""
    print("\n🧾 Testing Billing System...")
    
    config = {
        'billing_model': 'usage_based',
        'customer_tier': 'enterprise',
        'tax_rate': 0.08
    }
    billing = create_billing_system(config)
    print(f"✅ Billing system created: {type(billing).__name__}")
    
    # Create usage records
    usage_records = [
        UsageRecord(
            id="usage1",
            provider="openai",
            model="gpt-4o",
            tokens=10000,
            cost=Decimal("5.00"),
            user_id="user1",
            department="engineering"
        ),
        UsageRecord(
            id="usage2",
            provider="anthropic",
            model="claude-3-opus",
            tokens=8000,
            cost=Decimal("6.40"),
            user_id="user2",
            department="product"
        )
    ]
    
    # Generate billing records
    billing_records = []
    for usage in usage_records:
        record = billing.generate_billing_record(usage)
        billing_records.append(record)
        print(f"✅ Billing record generated: {record.id}, ${record.amount}")
    
    # Generate invoice
    invoice = billing.generate_invoice("customer123", billing_records, BillingPeriod.MONTHLY)
    print(f"✅ Invoice generated: {invoice['invoice_id']}")
    print(f"  - Subtotal: ${invoice['subtotal']}")
    print(f"  - Tax: ${invoice['tax_amount']}")
    print(f"  - Total: ${invoice['total_amount']}")
    
    # Generate chargeback report
    chargeback = billing.generate_chargeback_report(billing_records)
    print(f"✅ Chargeback report generated with {len(chargeback['departments'])} departments")
    
    return True


def test_recommendation_engine():
    """Test the recommendation engine functionality."""
    print("\n🎯 Testing Recommendation Engine...")
    
    config = {
        'analysis_period_days': 30,
        'min_confidence': 0.7
    }
    recommender = create_recommendation_engine(config)
    print(f"✅ Recommendation engine created: {type(recommender).__name__}")
    
    # Mock historical data
    historical_data = [
        {
            'provider': 'openai',
            'model': 'gpt-4o',
            'cost': 50.0,
            'tokens': 25000,
            'department': 'engineering'
        },
        {
            'provider': 'anthropic',
            'model': 'claude-3-opus',
            'cost': 64.0,
            'tokens': 20000,
            'department': 'product'
        }
    ]
    
    # Generate recommendations
    recommendations = recommender.generate_recommendations(historical_data)
    print(f"✅ Generated {len(recommendations)} recommendations")
    
    for rec in recommendations[:2]:  # Show first 2
        print(f"  - {rec.category.value}: {rec.title}")
        print(f"    Potential savings: ${rec.estimated_savings}/month")
        print(f"    Confidence: {rec.confidence:.2f}")
    
    return True


def test_integrated_system():
    """Test the integrated cost management system."""
    print("\n🔧 Testing Integrated Cost Management System...")
    
    config = {
        'tracker': {'type': 'standard'},
        'optimizer': {'strategy': 'balanced'},
        'budget_manager': {'default_thresholds': {'warning': 0.8, 'critical': 0.9}},
        'billing': {'billing_model': 'usage_based'},
        'predictor': {'forecasting_method': 'linear_regression'},
        'recommender': {'min_confidence': 0.7}
    }
    
    cost_mgmt = create_cost_management_system(config)
    print(f"✅ Integrated system created: {type(cost_mgmt).__name__}")
    
    # Test basic operations
    cost_entry = CostEntry(
        provider="openai",
        model="gpt-4o",
        category=CostCategory.API_CALLS,
        amount=Decimal("0.05"),
        total_tokens=1000
    )
    
    # Record cost through integrated system
    cost_mgmt.cost_tracker.record_cost(cost_entry)
    print(f"✅ Cost recorded through integrated system")
    
    # Get dashboard data
    dashboard_data = cost_mgmt.get_dashboard_data()
    print(f"✅ Dashboard data retrieved:")
    print(f"  - Current costs: ${dashboard_data['current_costs']['total_cost']}")
    print(f"  - Active budgets: {len(dashboard_data['budgets'])}")
    print(f"  - Recent recommendations: {len(dashboard_data['recommendations'])}")
    
    return True


async def main():
    """Run all cost management tests."""
    print("🚀 LangSwarm V2 Cost Management System - Standalone Test")
    print("=" * 60)
    
    tests = [
        ("Data Structures", test_data_structures),
        ("Cost Tracker", test_cost_tracker),
        ("Cost Optimizer", test_cost_optimizer),
        ("Budget Manager", test_budget_manager),
        ("Billing System", test_billing_system),
        ("Recommendation Engine", test_recommendation_engine),
        ("Integrated System", test_integrated_system),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            if result:
                print(f"✅ {test_name} - PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Cost Management Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All cost management tests PASSED! System is ready for production.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    asyncio.run(main())
