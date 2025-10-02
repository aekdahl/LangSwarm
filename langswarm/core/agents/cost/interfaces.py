"""
LangSwarm V2 Cost Management Interfaces

Core interfaces and data structures for sophisticated cost management and optimization.
Provides abstractions for cost tracking, budgeting, billing, and optimization.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid


class CostCategory(Enum):
    """Cost category enumeration"""
    API_CALLS = "api_calls"
    COMPUTE = "compute"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    EMBEDDING = "embedding"
    FUNCTION_CALLING = "function_calling"
    FINE_TUNING = "fine_tuning"
    VISION = "vision"
    AUDIO = "audio"
    OTHER = "other"


class BillingPeriod(Enum):
    """Billing period enumeration"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class CostAlertType(Enum):
    """Cost alert type enumeration"""
    BUDGET_THRESHOLD = "budget_threshold"
    UNUSUAL_SPENDING = "unusual_spending"
    COST_SPIKE = "cost_spike"
    INEFFICIENT_USAGE = "inefficient_usage"
    PROVIDER_RECOMMENDATION = "provider_recommendation"
    BUDGET_EXCEEDED = "budget_exceeded"


class OptimizationStrategy(Enum):
    """Cost optimization strategy enumeration"""
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_PERFORMANCE = "maximize_performance"
    BALANCE_COST_PERFORMANCE = "balance_cost_performance"
    OPTIMIZE_LATENCY = "optimize_latency"
    OPTIMIZE_QUALITY = "optimize_quality"
    CUSTOM = "custom"


class ProviderTier(Enum):
    """Provider tier for cost optimization"""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"
    FREE = "free"


class CostMetric(Enum):
    """Cost metric types"""
    TOTAL_COST = "total_cost"
    COST_PER_REQUEST = "cost_per_request"
    COST_PER_TOKEN = "cost_per_token"
    COST_PER_MINUTE = "cost_per_minute"
    COST_PER_USER = "cost_per_user"
    COST_PER_SESSION = "cost_per_session"


@dataclass
class CostEntry:
    """Individual cost entry record"""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    provider: str = ""
    model: str = ""
    category: CostCategory = CostCategory.API_CALLS
    amount: float = 0.0
    currency: str = "USD"
    
    # Usage details
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    requests: int = 1
    
    # Context information
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    department: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token"""
        if self.total_tokens > 0:
            return self.amount / self.total_tokens
        return 0.0
    
    @property
    def cost_per_request(self) -> float:
        """Calculate cost per request"""
        if self.requests > 0:
            return self.amount / self.requests
        return 0.0


@dataclass
class CostSummary:
    """Cost summary for a specific period"""
    period_start: datetime
    period_end: datetime
    total_cost: float = 0.0
    currency: str = "USD"
    
    # Breakdown by provider
    provider_costs: Dict[str, float] = field(default_factory=dict)
    
    # Breakdown by model
    model_costs: Dict[str, float] = field(default_factory=dict)
    
    # Breakdown by category
    category_costs: Dict[CostCategory, float] = field(default_factory=dict)
    
    # Usage statistics
    total_requests: int = 0
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    
    # Performance metrics
    average_cost_per_request: float = 0.0
    average_cost_per_token: float = 0.0
    most_expensive_provider: Optional[str] = None
    most_expensive_model: Optional[str] = None
    
    # Trends
    cost_trend: str = "stable"  # "increasing", "decreasing", "stable"
    usage_trend: str = "stable"
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.total_requests > 0:
            self.average_cost_per_request = self.total_cost / self.total_requests
        
        if self.total_tokens > 0:
            self.average_cost_per_token = self.total_cost / self.total_tokens
        
        if self.provider_costs:
            self.most_expensive_provider = max(self.provider_costs, key=self.provider_costs.get)
        
        if self.model_costs:
            self.most_expensive_model = max(self.model_costs, key=self.model_costs.get)


@dataclass
class CostBudget:
    """Cost budget configuration"""
    budget_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Budget limits
    amount: float = 0.0
    currency: str = "USD"
    period: BillingPeriod = BillingPeriod.MONTHLY
    
    # Scope
    providers: List[str] = field(default_factory=list)  # Empty = all providers
    models: List[str] = field(default_factory=list)     # Empty = all models
    categories: List[CostCategory] = field(default_factory=list)  # Empty = all categories
    
    # Filters
    user_ids: List[str] = field(default_factory=list)
    project_ids: List[str] = field(default_factory=list)
    departments: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Alert thresholds (percentages)
    warning_threshold: float = 80.0
    critical_threshold: float = 95.0
    
    # Status
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Current period tracking
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    current_period_spend: float = 0.0
    
    @property
    def remaining_budget(self) -> float:
        """Calculate remaining budget for current period"""
        return max(0.0, self.amount - self.current_period_spend)
    
    @property
    def budget_utilization(self) -> float:
        """Calculate budget utilization percentage"""
        if self.amount > 0:
            return (self.current_period_spend / self.amount) * 100
        return 0.0
    
    @property
    def is_over_budget(self) -> bool:
        """Check if budget is exceeded"""
        return self.current_period_spend > self.amount


@dataclass
class CostAlert:
    """Cost alert notification"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: CostAlertType = CostAlertType.BUDGET_THRESHOLD
    severity: str = "medium"  # "low", "medium", "high", "critical"
    title: str = ""
    message: str = ""
    
    # Context
    provider: Optional[str] = None
    model: Optional[str] = None
    budget_id: Optional[str] = None
    
    # Alert details
    current_cost: float = 0.0
    threshold_cost: float = 0.0
    projected_cost: float = 0.0
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostForecast:
    """Cost forecast for future periods"""
    forecast_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider: Optional[str] = None
    model: Optional[str] = None
    
    # Forecast period
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    
    # Forecast data
    predicted_cost: float = 0.0
    confidence_level: float = 0.8  # 0.0 to 1.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    
    # Assumptions
    assumptions: List[str] = field(default_factory=list)
    
    # Historical data used
    historical_periods: int = 0
    data_quality: str = "good"  # "poor", "fair", "good", "excellent"
    
    # Trends
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"
    seasonality_detected: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    methodology: str = "linear_regression"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BillingRecord:
    """Billing record for chargeback and invoicing"""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Billing details
    customer_id: str = ""
    department: Optional[str] = None
    project_id: Optional[str] = None
    
    # Period
    billing_period: BillingPeriod = BillingPeriod.MONTHLY
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    
    # Costs
    total_amount: float = 0.0
    currency: str = "USD"
    
    # Line items
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    
    # Status
    status: str = "draft"  # "draft", "approved", "invoiced", "paid"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Invoice details
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageRecord:
    """Usage record for billing calculation"""
    usage_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # User context
    user_id: str = ""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    department: Optional[str] = None
    
    # Provider details
    provider: str = ""
    model: str = ""
    
    # Usage metrics
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    requests: int = 1
    duration_ms: int = 0
    
    # Cost
    cost: float = 0.0
    currency: str = "USD"
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostRecommendation:
    """Cost optimization recommendation"""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # "provider_switch", "model_optimization", "usage_pattern", etc.
    priority: str = "medium"  # "low", "medium", "high", "critical"
    
    # Description
    title: str = ""
    description: str = ""
    rationale: str = ""
    
    # Impact
    potential_savings: float = 0.0
    savings_percentage: float = 0.0
    implementation_effort: str = "medium"  # "low", "medium", "high"
    
    # Context
    provider: Optional[str] = None
    model: Optional[str] = None
    category: Optional[CostCategory] = None
    
    # Actions
    recommended_actions: List[str] = field(default_factory=list)
    
    # Status
    status: str = "pending"  # "pending", "accepted", "rejected", "implemented"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ICostTracker(ABC):
    """Interface for cost tracking"""
    
    @abstractmethod
    async def track_cost(self, entry: CostEntry) -> None:
        """Track a cost entry"""
        pass
    
    @abstractmethod
    async def get_cost_summary(self, provider: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> CostSummary:
        """Get cost summary for a period"""
        pass
    
    @abstractmethod
    async def get_costs_by_provider(self, start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, float]:
        """Get costs grouped by provider"""
        pass
    
    @abstractmethod
    async def get_costs_by_model(self, provider: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, float]:
        """Get costs grouped by model"""
        pass
    
    @abstractmethod
    async def export_cost_data(self, format: str = "csv",
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> str:
        """Export cost data in specified format"""
        pass


class ICostOptimizer(ABC):
    """Interface for cost optimization"""
    
    @abstractmethod
    async def analyze_costs(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Analyze current costs for optimization opportunities"""
        pass
    
    @abstractmethod
    async def recommend_provider_switch(self, current_usage: Dict[str, Any]) -> List[CostRecommendation]:
        """Recommend provider switches for cost optimization"""
        pass
    
    @abstractmethod
    async def recommend_model_optimization(self, provider: str) -> List[CostRecommendation]:
        """Recommend model optimizations"""
        pass
    
    @abstractmethod
    async def optimize_request_patterns(self, usage_data: List[UsageRecord]) -> List[CostRecommendation]:
        """Analyze and optimize request patterns"""
        pass
    
    @abstractmethod
    async def calculate_potential_savings(self, recommendations: List[CostRecommendation]) -> float:
        """Calculate total potential savings from recommendations"""
        pass


class ICostPredictor(ABC):
    """Interface for cost prediction and forecasting"""
    
    @abstractmethod
    async def predict_costs(self, provider: str, 
                          forecast_days: int = 30,
                          confidence_level: float = 0.8) -> CostForecast:
        """Predict future costs based on historical data"""
        pass
    
    @abstractmethod
    async def forecast_budget_burn(self, budget: CostBudget) -> Dict[str, Any]:
        """Forecast when budget will be exhausted"""
        pass
    
    @abstractmethod
    async def predict_usage_trends(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Predict usage trends and patterns"""
        pass
    
    @abstractmethod
    async def capacity_planning(self, target_growth: float) -> Dict[str, Any]:
        """Perform capacity planning for cost budgeting"""
        pass


class ICostBudgetManager(ABC):
    """Interface for budget management"""
    
    @abstractmethod
    async def create_budget(self, budget: CostBudget) -> str:
        """Create a new budget"""
        pass
    
    @abstractmethod
    async def update_budget(self, budget_id: str, updates: Dict[str, Any]) -> None:
        """Update an existing budget"""
        pass
    
    @abstractmethod
    async def check_budget_status(self, budget_id: Optional[str] = None) -> Dict[str, Any]:
        """Check current budget status"""
        pass
    
    @abstractmethod
    async def generate_budget_alerts(self) -> List[CostAlert]:
        """Generate budget-based alerts"""
        pass
    
    @abstractmethod
    async def get_budget_utilization(self, budget_id: str) -> float:
        """Get budget utilization percentage"""
        pass


class ICostBillingSystem(ABC):
    """Interface for billing and chargeback systems"""
    
    @abstractmethod
    async def generate_bill(self, customer_id: str, 
                          period: BillingPeriod,
                          start_date: datetime,
                          end_date: datetime) -> BillingRecord:
        """Generate a bill for a customer"""
        pass
    
    @abstractmethod
    async def calculate_chargeback(self, department: str,
                                 period: BillingPeriod) -> Dict[str, Any]:
        """Calculate chargeback costs for a department"""
        pass
    
    @abstractmethod
    async def generate_invoice(self, billing_record_id: str) -> Dict[str, Any]:
        """Generate an invoice from a billing record"""
        pass
    
    @abstractmethod
    async def track_usage(self, usage: UsageRecord) -> None:
        """Track usage for billing purposes"""
        pass


class ICostRecommendationEngine(ABC):
    """Interface for cost recommendation engine"""
    
    @abstractmethod
    async def generate_recommendations(self, provider: Optional[str] = None) -> List[CostRecommendation]:
        """Generate cost optimization recommendations"""
        pass
    
    @abstractmethod
    async def analyze_spending_patterns(self, timeframe_days: int = 30) -> Dict[str, Any]:
        """Analyze spending patterns for recommendations"""
        pass
    
    @abstractmethod
    async def recommend_budget_adjustments(self) -> List[CostRecommendation]:
        """Recommend budget adjustments based on spending patterns"""
        pass
    
    @abstractmethod
    async def evaluate_recommendation_impact(self, recommendation: CostRecommendation) -> Dict[str, Any]:
        """Evaluate the potential impact of implementing a recommendation"""
        pass


# Exception classes for cost management
class CostManagementError(Exception):
    """Base exception for cost management errors"""
    pass


class BudgetExceededError(CostManagementError):
    """Raised when budget is exceeded"""
    pass


class InvalidBudgetError(CostManagementError):
    """Raised when budget configuration is invalid"""
    pass


class CostTrackingError(CostManagementError):
    """Raised when cost tracking fails"""
    pass


class BillingError(CostManagementError):
    """Raised when billing operations fail"""
    pass


class ForecastingError(CostManagementError):
    """Raised when cost forecasting fails"""
    pass
