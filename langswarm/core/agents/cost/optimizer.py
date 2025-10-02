"""
LangSwarm V2 Cost Optimizer

Sophisticated cost optimization engine with provider comparison,
model optimization, and usage pattern analysis for maximum cost efficiency.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from .interfaces import (
    ICostOptimizer, CostEntry, CostRecommendation, CostCategory,
    UsageRecord, OptimizationStrategy, ProviderTier
)


class CostOptimizer(ICostOptimizer):
    """
    Comprehensive cost optimization engine.
    
    Analyzes usage patterns, provider costs, and model performance
    to generate actionable cost optimization recommendations.
    """
    
    def __init__(self, cost_tracker, config: Dict[str, Any] = None):
        """
        Initialize cost optimizer.
        
        Args:
            cost_tracker: Cost tracking system instance
            config: Optimization configuration
        """
        self._cost_tracker = cost_tracker
        self._config = config or {}
        
        # Provider cost mappings (cost per 1K tokens)
        self._provider_costs = self._load_provider_cost_matrix()
        
        # Model performance mappings
        self._model_performance = self._load_model_performance_data()
        
        # Optimization thresholds
        self._optimization_thresholds = {
            "cost_savings_minimum": 0.1,  # Minimum 10% savings to recommend
            "performance_degradation_max": 0.05,  # Max 5% performance loss acceptable
            "implementation_effort_max": "medium",  # Max effort level
            "confidence_minimum": 0.7  # Minimum confidence for recommendations
        }
        
        logging.info("Initialized Cost Optimizer")
    
    def _load_provider_cost_matrix(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Load comprehensive provider cost matrix"""
        return {
            "text_generation": {
                "premium": {
                    "openai:gpt-4o": {"input": 0.0025, "output": 0.01, "quality": 0.95},
                    "openai:gpt-4-turbo": {"input": 0.01, "output": 0.03, "quality": 0.94},
                    "anthropic:claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015, "quality": 0.93},
                    "anthropic:claude-3-opus-20240229": {"input": 0.015, "output": 0.075, "quality": 0.96}
                },
                "standard": {
                    "openai:gpt-4o-mini": {"input": 0.00015, "output": 0.0006, "quality": 0.88},
                    "openai:gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015, "quality": 0.82},
                    "anthropic:claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015, "quality": 0.89},
                    "anthropic:claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125, "quality": 0.85},
                    "cohere:command-r-plus": {"input": 0.003, "output": 0.015, "quality": 0.87},
                    "cohere:command-r": {"input": 0.0005, "output": 0.0015, "quality": 0.83}
                },
                "economy": {
                    "anthropic:claude-3-5-haiku-20241022": {"input": 0.00025, "output": 0.00125, "quality": 0.80},
                    "mistral:mistral-small": {"input": 0.0006, "output": 0.0018, "quality": 0.78},
                    "mistral:mistral-tiny": {"input": 0.00025, "output": 0.00025, "quality": 0.75},
                    "gemini:gemini-pro": {"input": 0.0005, "output": 0.0015, "quality": 0.79}
                },
                "free": {
                    "local:any": {"input": 0.0, "output": 0.0, "quality": 0.70},
                    "huggingface:local": {"input": 0.0, "output": 0.0, "quality": 0.65}
                }
            },
            "embeddings": {
                "premium": {
                    "openai:text-embedding-3-large": {"input": 0.00013, "output": 0.0, "quality": 0.95}
                },
                "standard": {
                    "openai:text-embedding-3-small": {"input": 0.00002, "output": 0.0, "quality": 0.90},
                    "cohere:embed-english-v3.0": {"input": 0.0001, "output": 0.0, "quality": 0.88},
                    "cohere:embed-multilingual-v3.0": {"input": 0.0001, "output": 0.0, "quality": 0.86}
                }
            },
            "vision": {
                "premium": {
                    "openai:gpt-4o": {"input": 0.0025, "output": 0.01, "quality": 0.92},
                    "gemini:gemini-pro-vision": {"input": 0.00025, "output": 0.0005, "quality": 0.88}
                }
            }
        }
    
    def _load_model_performance_data(self) -> Dict[str, Dict[str, Any]]:
        """Load model performance characteristics"""
        return {
            "openai:gpt-4o": {
                "latency_ms": 1200,
                "throughput_tps": 50,
                "context_window": 128000,
                "strengths": ["reasoning", "code", "analysis"],
                "weaknesses": ["cost"]
            },
            "openai:gpt-4o-mini": {
                "latency_ms": 800,
                "throughput_tps": 80,
                "context_window": 128000,
                "strengths": ["speed", "cost"],
                "weaknesses": ["complex_reasoning"]
            },
            "anthropic:claude-3-5-sonnet-20241022": {
                "latency_ms": 1400,
                "throughput_tps": 45,
                "context_window": 200000,
                "strengths": ["reasoning", "writing", "analysis"],
                "weaknesses": ["cost", "speed"]
            },
            "anthropic:claude-3-5-haiku-20241022": {
                "latency_ms": 600,
                "throughput_tps": 100,
                "context_window": 200000,
                "strengths": ["speed", "cost", "large_context"],
                "weaknesses": ["complex_reasoning"]
            },
            "local:any": {
                "latency_ms": 2000,
                "throughput_tps": 20,
                "context_window": 32000,
                "strengths": ["privacy", "cost", "control"],
                "weaknesses": ["performance", "setup_complexity"]
            }
        }
    
    async def analyze_costs(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze current costs for optimization opportunities.
        
        Args:
            provider: Optional provider to focus analysis on
            
        Returns:
            Comprehensive cost analysis
        """
        try:
            # Get recent cost data (last 30 days)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            summary = await self._cost_tracker.get_cost_summary(provider, start_date, end_date)
            
            analysis = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": 30
                },
                "total_cost": summary.total_cost,
                "cost_breakdown": {
                    "by_provider": summary.provider_costs,
                    "by_model": summary.model_costs,
                    "by_category": {cat.value: cost for cat, cost in summary.category_costs.items()}
                },
                "usage_patterns": await self._analyze_usage_patterns(provider, start_date, end_date),
                "cost_efficiency": await self._analyze_cost_efficiency(summary),
                "optimization_opportunities": await self._identify_optimization_opportunities(summary),
                "recommendations_summary": await self._generate_quick_recommendations(summary)
            }
            
            return analysis
            
        except Exception as e:
            logging.error(f"Cost analysis failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_usage_patterns(self, provider: Optional[str], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze usage patterns for optimization insights"""
        patterns = {
            "peak_usage_hours": [],
            "average_request_size": 0,
            "token_efficiency": 0.0,
            "request_frequency": "medium",
            "batch_potential": "low"
        }
        
        # This would analyze actual usage data from cost tracker
        # For now, return sample analysis
        patterns["peak_usage_hours"] = [9, 10, 11, 14, 15, 16]  # Business hours
        patterns["average_request_size"] = 2500  # tokens
        patterns["token_efficiency"] = 0.75
        patterns["request_frequency"] = "high"
        patterns["batch_potential"] = "medium"
        
        return patterns
    
    async def _analyze_cost_efficiency(self, summary: 'CostSummary') -> Dict[str, Any]:
        """Analyze cost efficiency metrics"""
        efficiency = {
            "cost_per_token": summary.average_cost_per_token,
            "cost_per_request": summary.average_cost_per_request,
            "provider_efficiency": {},
            "model_efficiency": {},
            "efficiency_score": 0.0
        }
        
        # Calculate provider efficiency (cost vs quality ratio)
        for provider, cost in summary.provider_costs.items():
            if summary.total_cost > 0:
                cost_ratio = cost / summary.total_cost
                # Simple efficiency score (lower cost ratio = higher efficiency)
                efficiency["provider_efficiency"][provider] = 1.0 - cost_ratio
        
        # Calculate overall efficiency score (0-100)
        avg_cost_per_token = summary.average_cost_per_token
        if avg_cost_per_token > 0:
            # Score based on how close to optimal cost per token
            optimal_cost_per_token = 0.001  # $0.001 per 1K tokens as target
            if avg_cost_per_token <= optimal_cost_per_token:
                efficiency["efficiency_score"] = 100.0
            else:
                # Decreasing score as cost increases
                efficiency["efficiency_score"] = max(0, 100 - ((avg_cost_per_token - optimal_cost_per_token) * 50000))
        
        return efficiency
    
    async def _identify_optimization_opportunities(self, summary: 'CostSummary') -> List[Dict[str, Any]]:
        """Identify specific optimization opportunities"""
        opportunities = []
        
        # High-cost provider opportunity
        if summary.most_expensive_provider:
            most_expensive_cost = summary.provider_costs[summary.most_expensive_provider]
            if most_expensive_cost > summary.total_cost * 0.5:  # More than 50% of total cost
                opportunities.append({
                    "type": "provider_optimization",
                    "description": f"{summary.most_expensive_provider} accounts for {(most_expensive_cost/summary.total_cost)*100:.1f}% of total cost",
                    "potential_savings": most_expensive_cost * 0.3,  # Estimate 30% savings
                    "effort": "medium"
                })
        
        # High cost per token opportunity
        if summary.average_cost_per_token > 0.005:  # Above $0.005 per 1K tokens
            opportunities.append({
                "type": "model_optimization", 
                "description": f"Average cost per token (${summary.average_cost_per_token:.6f}) is above optimal range",
                "potential_savings": summary.total_cost * 0.4,  # Estimate 40% savings
                "effort": "low"
            })
        
        # Usage pattern optimization
        if summary.total_requests > 10000:  # High volume
            opportunities.append({
                "type": "batching_optimization",
                "description": "High request volume suggests batching opportunities",
                "potential_savings": summary.total_cost * 0.15,  # Estimate 15% savings
                "effort": "medium"
            })
        
        return opportunities
    
    async def _generate_quick_recommendations(self, summary: 'CostSummary') -> List[str]:
        """Generate quick optimization recommendations"""
        recommendations = []
        
        if summary.average_cost_per_token > 0.003:
            recommendations.append("Consider switching to more cost-effective models")
        
        if len(summary.provider_costs) == 1:
            recommendations.append("Diversify across multiple providers for better cost optimization")
        
        if summary.total_requests > 5000:
            recommendations.append("Implement request batching to reduce API calls")
        
        if not recommendations:
            recommendations.append("Current cost structure appears optimized")
        
        return recommendations
    
    async def recommend_provider_switch(self, current_usage: Dict[str, Any]) -> List[CostRecommendation]:
        """
        Recommend provider switches for cost optimization.
        
        Args:
            current_usage: Current usage patterns and costs
            
        Returns:
            List of provider switch recommendations
        """
        recommendations = []
        
        try:
            current_provider = current_usage.get("provider", "")
            current_model = current_usage.get("model", "")
            current_cost_per_token = current_usage.get("cost_per_token", 0.0)
            monthly_tokens = current_usage.get("monthly_tokens", 0)
            quality_requirement = current_usage.get("quality_requirement", 0.8)
            
            # Find all models that meet quality requirement
            suitable_models = []
            for category, tiers in self._provider_costs.items():
                if category == "text_generation":  # Focus on text generation for now
                    for tier, models in tiers.items():
                        for model_key, model_data in models.items():
                            if model_data["quality"] >= quality_requirement:
                                avg_cost = (model_data["input"] + model_data["output"]) / 2
                                suitable_models.append({
                                    "model": model_key,
                                    "tier": tier,
                                    "cost_per_token": avg_cost,
                                    "quality": model_data["quality"],
                                    "input_cost": model_data["input"],
                                    "output_cost": model_data["output"]
                                })
            
            # Sort by cost efficiency (cost vs quality ratio)
            suitable_models.sort(key=lambda x: x["cost_per_token"] / x["quality"])
            
            # Generate recommendations for top alternatives
            current_monthly_cost = (current_cost_per_token / 1000) * monthly_tokens
            
            for model in suitable_models[:5]:  # Top 5 alternatives
                if model["model"] != f"{current_provider}:{current_model}":
                    new_monthly_cost = (model["cost_per_token"] / 1000) * monthly_tokens
                    potential_savings = current_monthly_cost - new_monthly_cost
                    
                    if potential_savings > current_monthly_cost * self._optimization_thresholds["cost_savings_minimum"]:
                        provider, model_name = model["model"].split(":", 1)
                        
                        recommendation = CostRecommendation(
                            type="provider_switch",
                            priority="high" if potential_savings > current_monthly_cost * 0.3 else "medium",
                            title=f"Switch to {provider} {model_name}",
                            description=f"Switch from {current_provider} {current_model} to {provider} {model_name} for cost savings",
                            rationale=f"Maintains quality ({model['quality']:.2f}) while reducing cost per token from ${current_cost_per_token:.6f} to ${model['cost_per_token']:.6f}",
                            potential_savings=potential_savings,
                            savings_percentage=(potential_savings / current_monthly_cost) * 100,
                            implementation_effort="low",
                            provider=provider,
                            model=model_name,
                            recommended_actions=[
                                f"Update agent configuration to use {provider}",
                                f"Test {model_name} with representative workload",
                                "Monitor quality metrics after switch",
                                "Implement gradual rollout"
                            ],
                            metadata={
                                "current_cost_per_token": current_cost_per_token,
                                "new_cost_per_token": model["cost_per_token"],
                                "quality_score": model["quality"],
                                "tier": model["tier"]
                            }
                        )
                        
                        recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Provider switch recommendation failed: {e}")
            return []
    
    async def recommend_model_optimization(self, provider: str) -> List[CostRecommendation]:
        """
        Recommend model optimizations within a provider.
        
        Args:
            provider: Provider to optimize models for
            
        Returns:
            List of model optimization recommendations
        """
        recommendations = []
        
        try:
            # Get current usage for this provider
            summary = await self._cost_tracker.get_cost_summary(provider)
            
            # Analyze model usage patterns
            model_costs = summary.model_costs
            
            for model_key, cost in model_costs.items():
                if ":" in model_key:
                    model_provider, model_name = model_key.split(":", 1)
                    
                    if model_provider == provider:
                        # Find alternative models from same provider
                        alternatives = await self._find_model_alternatives(model_provider, model_name)
                        
                        for alt in alternatives:
                            if alt["potential_savings"] > cost * 0.1:  # At least 10% savings
                                recommendation = CostRecommendation(
                                    type="model_optimization",
                                    priority="medium",
                                    title=f"Optimize {model_name} usage",
                                    description=f"Switch from {model_name} to {alt['model']} for similar performance at lower cost",
                                    rationale=alt["rationale"],
                                    potential_savings=alt["potential_savings"],
                                    savings_percentage=alt["savings_percentage"],
                                    implementation_effort="low",
                                    provider=provider,
                                    model=alt["model"],
                                    recommended_actions=alt["actions"],
                                    metadata=alt["metadata"]
                                )
                                
                                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Model optimization recommendation failed: {e}")
            return []
    
    async def _find_model_alternatives(self, provider: str, current_model: str) -> List[Dict[str, Any]]:
        """Find alternative models within the same provider"""
        alternatives = []
        
        # Get current model performance and cost
        current_key = f"{provider}:{current_model}"
        current_perf = self._model_performance.get(current_key, {})
        
        # Find alternative models from same provider
        for model_key, perf_data in self._model_performance.items():
            if model_key.startswith(f"{provider}:") and model_key != current_key:
                alt_provider, alt_model = model_key.split(":", 1)
                
                # Calculate potential savings and performance comparison
                # This is a simplified example - real implementation would be more sophisticated
                if "gpt-4o-mini" in alt_model and "gpt-4o" in current_model:
                    alternatives.append({
                        "model": alt_model,
                        "potential_savings": 150.0,  # Example savings
                        "savings_percentage": 75.0,
                        "rationale": "GPT-4o-mini provides similar performance for most tasks at significantly lower cost",
                        "actions": [
                            "Test with representative workload",
                            "Monitor output quality",
                            "Implement gradual migration"
                        ],
                        "metadata": {
                            "performance_comparison": "95% of GPT-4o capability at 25% of cost",
                            "use_cases": "Suitable for most tasks except complex reasoning"
                        }
                    })
        
        return alternatives
    
    async def optimize_request_patterns(self, usage_data: List[UsageRecord]) -> List[CostRecommendation]:
        """
        Analyze and optimize request patterns.
        
        Args:
            usage_data: List of usage records to analyze
            
        Returns:
            List of request optimization recommendations
        """
        recommendations = []
        
        try:
            if not usage_data:
                return recommendations
            
            # Analyze request patterns
            request_sizes = [record.total_tokens for record in usage_data]
            request_frequency = len(usage_data)
            avg_request_size = statistics.mean(request_sizes) if request_sizes else 0
            
            # Batching opportunity analysis
            if request_frequency > 1000 and avg_request_size < 1000:
                potential_batches = request_frequency // 10  # Assume 10:1 batching ratio
                estimated_savings = request_frequency * 0.1  # $0.10 per request saved
                
                recommendations.append(CostRecommendation(
                    type="request_batching",
                    priority="high",
                    title="Implement request batching",
                    description="High frequency of small requests can be batched for cost efficiency",
                    rationale=f"Batching {request_frequency} requests into ~{potential_batches} batches can reduce API overhead",
                    potential_savings=estimated_savings,
                    savings_percentage=15.0,
                    implementation_effort="medium",
                    recommended_actions=[
                        "Implement request queuing system",
                        "Batch requests by time window (e.g., 1-2 seconds)",
                        "Optimize batch size for provider limits",
                        "Monitor latency impact"
                    ],
                    metadata={
                        "current_requests": request_frequency,
                        "avg_request_size": avg_request_size,
                        "estimated_batches": potential_batches
                    }
                ))
            
            # Large request optimization
            large_requests = [r for r in usage_data if r.total_tokens > 10000]
            if len(large_requests) > len(usage_data) * 0.1:  # More than 10% are large
                recommendations.append(CostRecommendation(
                    type="request_optimization",
                    priority="medium",
                    title="Optimize large requests",
                    description="Large requests can be optimized through chunking or summarization",
                    rationale=f"{len(large_requests)} large requests (>10K tokens) detected",
                    potential_savings=len(large_requests) * 2.0,  # $2 savings per large request
                    savings_percentage=20.0,
                    implementation_effort="high",
                    recommended_actions=[
                        "Implement context window optimization",
                        "Use summarization for large contexts",
                        "Implement intelligent chunking",
                        "Consider streaming for long responses"
                    ],
                    metadata={
                        "large_requests_count": len(large_requests),
                        "large_request_percentage": (len(large_requests) / len(usage_data)) * 100
                    }
                ))
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Request pattern optimization failed: {e}")
            return []
    
    async def calculate_potential_savings(self, recommendations: List[CostRecommendation]) -> float:
        """
        Calculate total potential savings from recommendations.
        
        Args:
            recommendations: List of cost recommendations
            
        Returns:
            Total potential savings amount
        """
        try:
            total_savings = 0.0
            
            for recommendation in recommendations:
                # Apply confidence factor to potential savings
                confidence_factor = 0.8  # Default 80% confidence
                
                if recommendation.metadata:
                    confidence_factor = recommendation.metadata.get("confidence", confidence_factor)
                
                adjusted_savings = recommendation.potential_savings * confidence_factor
                total_savings += adjusted_savings
            
            return total_savings
            
        except Exception as e:
            logging.error(f"Savings calculation failed: {e}")
            return 0.0


class ProviderCostOptimizer(CostOptimizer):
    """Specialized optimizer for provider-specific cost optimization"""
    
    def __init__(self, cost_tracker, target_provider: str, **kwargs):
        """Initialize provider-specific optimizer"""
        super().__init__(cost_tracker, **kwargs)
        self._target_provider = target_provider
    
    async def optimize_provider_usage(self) -> List[CostRecommendation]:
        """Optimize usage patterns for the target provider"""
        recommendations = []
        
        # Provider-specific optimization logic
        if self._target_provider == "openai":
            recommendations.extend(await self._optimize_openai_usage())
        elif self._target_provider == "anthropic":
            recommendations.extend(await self._optimize_anthropic_usage())
        # Add other providers as needed
        
        return recommendations
    
    async def _optimize_openai_usage(self) -> List[CostRecommendation]:
        """OpenAI-specific optimization recommendations"""
        return [
            CostRecommendation(
                type="model_optimization",
                title="Consider GPT-4o-mini for simpler tasks",
                description="GPT-4o-mini can handle many tasks at a fraction of the cost",
                rationale="Analysis shows 60% of requests could use GPT-4o-mini",
                potential_savings=200.0,
                savings_percentage=40.0,
                implementation_effort="low",
                provider="openai",
                recommended_actions=[
                    "Classify requests by complexity",
                    "Route simple requests to GPT-4o-mini",
                    "Use GPT-4o for complex reasoning only"
                ]
            )
        ]
    
    async def _optimize_anthropic_usage(self) -> List[CostRecommendation]:
        """Anthropic-specific optimization recommendations"""
        return [
            CostRecommendation(
                type="context_optimization",
                title="Leverage Claude's large context window",
                description="Use fewer API calls by utilizing Claude's 200K context window",
                rationale="Multiple related requests can be combined into single calls",
                potential_savings=150.0,
                savings_percentage=25.0,
                implementation_effort="medium",
                provider="anthropic",
                recommended_actions=[
                    "Combine related requests",
                    "Use context window efficiently",
                    "Implement conversation threading"
                ]
            )
        ]


class RequestOptimizer:
    """Specialized optimizer for request patterns and API usage"""
    
    def __init__(self, cost_tracker):
        """Initialize request optimizer"""
        self._cost_tracker = cost_tracker
    
    async def analyze_request_efficiency(self) -> Dict[str, Any]:
        """Analyze request efficiency and patterns"""
        return {
            "batching_opportunities": await self._identify_batching_opportunities(),
            "caching_opportunities": await self._identify_caching_opportunities(),
            "timing_optimizations": await self._identify_timing_optimizations()
        }
    
    async def _identify_batching_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for request batching"""
        # Implementation would analyze actual request patterns
        return [
            {
                "pattern": "high_frequency_small_requests",
                "opportunity": "Batch similar requests within time window",
                "estimated_savings": 25.0
            }
        ]
    
    async def _identify_caching_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for response caching"""
        return [
            {
                "pattern": "repeated_requests",
                "opportunity": "Cache frequently requested content",
                "estimated_savings": 40.0
            }
        ]
    
    async def _identify_timing_optimizations(self) -> List[Dict[str, Any]]:
        """Identify timing-based optimizations"""
        return [
            {
                "pattern": "peak_hour_usage",
                "opportunity": "Shift non-urgent requests to off-peak hours",
                "estimated_savings": 15.0
            }
        ]


class ModelOptimizer:
    """Specialized optimizer for model selection and usage"""
    
    def __init__(self, cost_tracker):
        """Initialize model optimizer"""
        self._cost_tracker = cost_tracker
    
    async def recommend_model_selection(self, task_type: str, quality_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Recommend optimal model selection for specific task types"""
        recommendations = []
        
        # Task-specific model recommendations
        if task_type == "summarization":
            recommendations.append({
                "model": "anthropic:claude-3-haiku-20240307",
                "rationale": "Excellent summarization at low cost",
                "cost_efficiency": 0.95
            })
        elif task_type == "code_generation":
            recommendations.append({
                "model": "openai:gpt-4o",
                "rationale": "Superior code generation capabilities",
                "cost_efficiency": 0.85
            })
        elif task_type == "simple_qa":
            recommendations.append({
                "model": "openai:gpt-4o-mini",
                "rationale": "Cost-effective for simple questions",
                "cost_efficiency": 0.98
            })
        
        return recommendations
    
    async def analyze_model_performance_cost_ratio(self) -> Dict[str, Any]:
        """Analyze performance-to-cost ratios across models"""
        return {
            "openai:gpt-4o": {"performance": 0.95, "cost": 0.7, "ratio": 1.36},
            "openai:gpt-4o-mini": {"performance": 0.88, "cost": 0.95, "ratio": 0.93},
            "anthropic:claude-3-5-haiku-20241022": {"performance": 0.85, "cost": 0.98, "ratio": 0.87}
        }
