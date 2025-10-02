"""
LangSwarm V2 Cost Management & Optimization

Sophisticated cost management and optimization system for V2 agents with:
- Real-time cost tracking and budgeting
- Provider cost comparison and optimization
- Usage-based billing and chargeback systems
- Cost prediction and capacity planning
- Automated cost optimization recommendations
"""

from typing import Optional, Dict, Any, List

from .interfaces import (
    # Core interfaces
    ICostTracker, ICostOptimizer, ICostPredictor, ICostBudgetManager,
    ICostBillingSystem, ICostRecommendationEngine,
    
    # Data structures
    CostEntry, CostSummary, CostBudget, CostAlert, CostForecast,
    BillingRecord, UsageRecord, CostRecommendation,
    
    # Enums
    CostCategory, BillingPeriod, CostAlertType, OptimizationStrategy,
    ProviderTier, CostMetric
)

from .tracker import (
    CostTracker, RealTimeCostTracker, create_cost_tracker
)

from .optimizer import (
    CostOptimizer, ProviderCostOptimizer, RequestOptimizer,
    ModelOptimizer
)

from .predictor import (
    CostPredictor, UsageForecaster, BudgetPlanner,
    CapacityPlanner
)

from .budget import (
    BudgetManager, CostBudgetManager, AlertManager,
    SpendingController
)

from .billing import (
    BillingSystem, UsageBillingSystem, ChargebackSystem,
    InvoiceGenerator
)

from .recommendations import (
    RecommendationEngine, CostOptimizationEngine,
    ProviderRecommendationEngine
)

from .manager import (
    CostManagementSystem, GlobalCostManager,
    create_cost_management_system
)

# Version info
__version__ = "2.0.0"

# Public API
__all__ = [
    # Core interfaces
    'ICostTracker',
    'ICostOptimizer', 
    'ICostPredictor',
    'ICostBudgetManager',
    'ICostBillingSystem',
    'ICostRecommendationEngine',
    
    # Data structures
    'CostEntry',
    'CostSummary',
    'CostBudget',
    'CostAlert',
    'CostForecast',
    'BillingRecord',
    'UsageRecord',
    'CostRecommendation',
    
    # Enums
    'CostCategory',
    'BillingPeriod',
    'CostAlertType',
    'OptimizationStrategy',
    'ProviderTier',
    'CostMetric',
    
    # Core implementations
    'CostTracker',
    'RealTimeCostTracker',
    'create_cost_tracker',
    
    # Optimization
    'CostOptimizer',
    'ProviderCostOptimizer',
    'RequestOptimizer',
    'ModelOptimizer',
    
    # Prediction and planning
    'CostPredictor',
    'UsageForecaster',
    'BudgetPlanner',
    'CapacityPlanner',
    
    # Budget management
    'BudgetManager',
    'CostBudgetManager',
    'AlertManager',
    'SpendingController',
    
    # Billing systems
    'BillingSystem',
    'UsageBillingSystem',
    'ChargebackSystem',
    'InvoiceGenerator',
    
    # Recommendations
    'RecommendationEngine',
    'CostOptimizationEngine',
    'ProviderRecommendationEngine',
    
    # Management system
    'CostManagementSystem',
    'GlobalCostManager',
    'create_cost_management_system'
]

# Global cost management system
_global_cost_manager: Optional['GlobalCostManager'] = None


def get_global_cost_manager() -> Optional['GlobalCostManager']:
    """Get the global cost management system"""
    return _global_cost_manager


def set_global_cost_manager(manager: 'GlobalCostManager'):
    """Set the global cost management system"""
    global _global_cost_manager
    _global_cost_manager = manager


def initialize_cost_management(config: Optional[Dict[str, Any]] = None):
    """Initialize global cost management system"""
    if not get_global_cost_manager():
        manager = create_cost_management_system(config or {})
        set_global_cost_manager(manager)


# Convenience functions for quick access
async def track_cost(provider: str, model: str, usage: Dict[str, Any], cost: float, **kwargs):
    """Track a cost entry"""
    manager = get_global_cost_manager()
    if manager:
        await manager.track_cost(provider, model, usage, cost, **kwargs)
    else:
        raise RuntimeError("Cost management system not initialized")


async def get_cost_summary(provider: str = None, period: str = "day") -> Dict[str, Any]:
    """Get cost summary"""
    manager = get_global_cost_manager()
    if manager:
        return await manager.get_cost_summary(provider, period)
    else:
        return {}


async def get_cost_recommendations(provider: str = None) -> List[Dict[str, Any]]:
    """Get cost optimization recommendations"""
    manager = get_global_cost_manager()
    if manager:
        return await manager.get_recommendations(provider)
    else:
        return []


async def check_budget_status() -> Dict[str, Any]:
    """Check current budget status"""
    manager = get_global_cost_manager()
    if manager:
        return await manager.check_budget_status()
    else:
        return {"status": "not_initialized"}


async def optimize_costs(provider: str = None) -> Dict[str, Any]:
    """Run cost optimization analysis"""
    manager = get_global_cost_manager()
    if manager:
        return await manager.optimize_costs(provider)
    else:
        return {"error": "Cost management system not initialized"}
