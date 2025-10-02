"""
LangSwarm V2 Cost Recommendation Engine

Intelligent cost optimization recommendation system with automated analysis,
pattern recognition, and actionable cost reduction strategies.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from .interfaces import (
    ICostRecommendationEngine, CostRecommendation, CostCategory,
    OptimizationStrategy, ProviderTier
)


class RecommendationEngine(ICostRecommendationEngine):
    """
    Intelligent cost optimization recommendation engine.
    
    Analyzes spending patterns, usage trends, and provider performance
    to generate actionable cost optimization recommendations.
    """
    
    def __init__(self, cost_tracker, cost_optimizer=None, config: Dict[str, Any] = None):
        """
        Initialize recommendation engine.
        
        Args:
            cost_tracker: Cost tracking system instance
            cost_optimizer: Optional cost optimizer instance
            config: Recommendation engine configuration
        """
        self._cost_tracker = cost_tracker
        self._cost_optimizer = cost_optimizer
        self._config = config or {}
        
        # Recommendation parameters
        self._recommendation_params = {
            "min_savings_threshold": 10.0,  # Minimum $10 savings to recommend
            "min_savings_percentage": 5.0,  # Minimum 5% savings percentage
            "max_recommendations": 20,      # Maximum recommendations to generate
            "confidence_threshold": 0.6,    # Minimum confidence for recommendations
            "analysis_period_days": 30      # Days of data to analyze
        }
        
        # Recommendation categories and their weights
        self._recommendation_categories = {
            "provider_optimization": 0.3,
            "model_optimization": 0.25,
            "usage_optimization": 0.2,
            "budget_optimization": 0.15,
            "infrastructure_optimization": 0.1
        }
        
        # Analysis engines
        self._analysis_engines = {
            "spending_patterns": self._analyze_spending_patterns,
            "provider_efficiency": self._analyze_provider_efficiency,
            "usage_trends": self._analyze_usage_trends,
            "cost_anomalies": self._analyze_cost_anomalies,
            "optimization_opportunities": self._analyze_optimization_opportunities
        }
        
        logging.info("Initialized Cost Recommendation Engine")
    
    async def generate_recommendations(self, provider: Optional[str] = None) -> List[CostRecommendation]:
        """
        Generate cost optimization recommendations.
        
        Args:
            provider: Optional provider to focus recommendations on
            
        Returns:
            List of cost optimization recommendations
        """
        try:
            # Gather analysis data
            analysis_data = await self._gather_analysis_data(provider)
            
            if not analysis_data:
                return []
            
            # Generate recommendations from multiple engines
            all_recommendations = []
            
            # Provider optimization recommendations
            provider_recs = await self._generate_provider_recommendations(analysis_data)
            all_recommendations.extend(provider_recs)
            
            # Model optimization recommendations
            model_recs = await self._generate_model_recommendations(analysis_data)
            all_recommendations.extend(model_recs)
            
            # Usage pattern recommendations
            usage_recs = await self._generate_usage_recommendations(analysis_data)
            all_recommendations.extend(usage_recs)
            
            # Budget optimization recommendations
            budget_recs = await self._generate_budget_recommendations(analysis_data)
            all_recommendations.extend(budget_recs)
            
            # Infrastructure recommendations
            infra_recs = await self._generate_infrastructure_recommendations(analysis_data)
            all_recommendations.extend(infra_recs)
            
            # Score and rank recommendations
            scored_recommendations = await self._score_recommendations(all_recommendations, analysis_data)
            
            # Filter and sort by priority
            final_recommendations = self._filter_and_sort_recommendations(scored_recommendations)
            
            logging.info(f"Generated {len(final_recommendations)} cost optimization recommendations")
            
            return final_recommendations
            
        except Exception as e:
            logging.error(f"Failed to generate recommendations: {e}")
            return []
    
    async def _gather_analysis_data(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Gather comprehensive analysis data"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self._recommendation_params["analysis_period_days"])
        
        # Get cost summary
        cost_summary = await self._cost_tracker.get_cost_summary(provider, start_date, end_date)
        
        if cost_summary.total_cost == 0:
            return {}
        
        # Run all analysis engines
        analysis_results = {}
        for engine_name, engine_func in self._analysis_engines.items():
            try:
                analysis_results[engine_name] = await engine_func(cost_summary, provider)
            except Exception as e:
                logging.warning(f"Analysis engine {engine_name} failed: {e}")
                analysis_results[engine_name] = {}
        
        # Combine results
        return {
            "cost_summary": cost_summary,
            "analysis_period": {
                "start": start_date,
                "end": end_date,
                "days": self._recommendation_params["analysis_period_days"]
            },
            "provider_filter": provider,
            **analysis_results
        }
    
    async def _analyze_spending_patterns(self, cost_summary, provider: Optional[str] = None) -> Dict[str, Any]:
        """Analyze spending patterns for optimization opportunities"""
        patterns = {
            "top_cost_drivers": [],
            "spending_concentration": 0.0,
            "growth_trend": "stable",
            "cost_efficiency": 0.0
        }
        
        # Analyze provider distribution
        if cost_summary.provider_costs:
            sorted_providers = sorted(cost_summary.provider_costs.items(), key=lambda x: x[1], reverse=True)
            patterns["top_cost_drivers"] = [
                {"provider": p, "cost": c, "percentage": (c/cost_summary.total_cost)*100}
                for p, c in sorted_providers[:5]
            ]
            
            # Calculate spending concentration (Gini coefficient approximation)
            costs = list(cost_summary.provider_costs.values())
            if len(costs) > 1:
                total_cost = sum(costs)
                cumulative_share = 0
                gini_sum = 0
                for i, cost in enumerate(sorted(costs)):
                    cumulative_share += cost / total_cost
                    gini_sum += cumulative_share
                patterns["spending_concentration"] = 1 - (2 * gini_sum / len(costs)) + (1 / len(costs))
        
        # Analyze cost efficiency
        if cost_summary.total_requests > 0:
            patterns["cost_efficiency"] = 1 / cost_summary.average_cost_per_request if cost_summary.average_cost_per_request > 0 else 0
        
        return patterns
    
    async def _analyze_provider_efficiency(self, cost_summary, provider: Optional[str] = None) -> Dict[str, Any]:
        """Analyze provider efficiency and performance"""
        efficiency = {
            "provider_rankings": [],
            "inefficient_providers": [],
            "optimization_potential": 0.0
        }
        
        # Rank providers by cost efficiency
        provider_efficiency = {}
        for prov, cost in cost_summary.provider_costs.items():
            # Simple efficiency score (lower cost per request = higher efficiency)
            if cost_summary.total_requests > 0:
                cost_per_request = cost / cost_summary.total_requests
                provider_efficiency[prov] = 1 / cost_per_request if cost_per_request > 0 else 0
        
        if provider_efficiency:
            sorted_efficiency = sorted(provider_efficiency.items(), key=lambda x: x[1], reverse=True)
            efficiency["provider_rankings"] = [
                {"provider": p, "efficiency_score": e}
                for p, e in sorted_efficiency
            ]
            
            # Identify inefficient providers (bottom 20%)
            if len(sorted_efficiency) > 2:
                threshold = len(sorted_efficiency) * 0.8
                efficiency["inefficient_providers"] = [
                    p for p, e in sorted_efficiency[int(threshold):]
                ]
        
        return efficiency
    
    async def _analyze_usage_trends(self, cost_summary, provider: Optional[str] = None) -> Dict[str, Any]:
        """Analyze usage trends and patterns"""
        trends = {
            "growth_rate": 0.0,
            "seasonality": False,
            "usage_spikes": [],
            "optimization_potential": "medium"
        }
        
        # Analyze cost trends
        if cost_summary.cost_trend:
            if cost_summary.cost_trend == "increasing":
                trends["growth_rate"] = 0.15  # Assume 15% growth
            elif cost_summary.cost_trend == "decreasing":
                trends["growth_rate"] = -0.10  # Assume 10% decline
        
        # Simple optimization potential assessment
        if cost_summary.average_cost_per_token > 0.003:  # High cost per token
            trends["optimization_potential"] = "high"
        elif cost_summary.average_cost_per_token > 0.001:
            trends["optimization_potential"] = "medium"
        else:
            trends["optimization_potential"] = "low"
        
        return trends
    
    async def _analyze_cost_anomalies(self, cost_summary, provider: Optional[str] = None) -> Dict[str, Any]:
        """Analyze cost anomalies and unusual patterns"""
        anomalies = {
            "unusual_spikes": [],
            "cost_variance": 0.0,
            "anomaly_score": 0.0
        }
        
        # Simple anomaly detection based on provider cost distribution
        if len(cost_summary.provider_costs) > 1:
            costs = list(cost_summary.provider_costs.values())
            mean_cost = statistics.mean(costs)
            variance = statistics.variance(costs) if len(costs) > 1 else 0
            
            anomalies["cost_variance"] = variance
            
            # Identify providers with costs significantly above mean
            for provider, cost in cost_summary.provider_costs.items():
                if cost > mean_cost * 2:  # More than 2x average
                    anomalies["unusual_spikes"].append({
                        "provider": provider,
                        "cost": cost,
                        "deviation": (cost - mean_cost) / mean_cost if mean_cost > 0 else 0
                    })
        
        return anomalies
    
    async def _analyze_optimization_opportunities(self, cost_summary, provider: Optional[str] = None) -> Dict[str, Any]:
        """Analyze specific optimization opportunities"""
        opportunities = {
            "high_cost_providers": [],
            "batching_potential": False,
            "caching_potential": False,
            "model_optimization": False
        }
        
        # Identify high-cost providers
        for prov, cost in cost_summary.provider_costs.items():
            if cost > cost_summary.total_cost * 0.3:  # More than 30% of total
                opportunities["high_cost_providers"].append(prov)
        
        # Assess batching potential
        if cost_summary.total_requests > 1000:  # High request volume
            opportunities["batching_potential"] = True
        
        # Assess model optimization potential
        if cost_summary.average_cost_per_token > 0.002:  # Above optimal threshold
            opportunities["model_optimization"] = True
        
        return opportunities
    
    async def _generate_provider_recommendations(self, analysis_data: Dict[str, Any]) -> List[CostRecommendation]:
        """Generate provider optimization recommendations"""
        recommendations = []
        
        try:
            cost_summary = analysis_data["cost_summary"]
            provider_efficiency = analysis_data.get("provider_efficiency", {})
            
            # Recommend switching from inefficient providers
            inefficient_providers = provider_efficiency.get("inefficient_providers", [])
            for provider in inefficient_providers:
                if provider in cost_summary.provider_costs:
                    provider_cost = cost_summary.provider_costs[provider]
                    potential_savings = provider_cost * 0.3  # Estimate 30% savings
                    
                    if potential_savings >= self._recommendation_params["min_savings_threshold"]:
                        recommendation = CostRecommendation(
                            type="provider_optimization",
                            priority="high" if potential_savings > 100 else "medium",
                            title=f"Optimize {provider} usage",
                            description=f"Provider {provider} shows low efficiency - consider alternatives",
                            rationale=f"Analysis shows {provider} has below-average cost efficiency",
                            potential_savings=potential_savings,
                            savings_percentage=(potential_savings / provider_cost) * 100,
                            implementation_effort="medium",
                            provider=provider,
                            recommended_actions=[
                                f"Evaluate alternative providers for {provider} workloads",
                                "Conduct cost-benefit analysis of provider switching",
                                "Test alternative providers with sample workloads",
                                "Implement gradual migration strategy"
                            ],
                            metadata={
                                "current_cost": provider_cost,
                                "efficiency_ranking": "bottom_20_percent",
                                "confidence": 0.7
                            }
                        )
                        recommendations.append(recommendation)
            
            # Recommend provider diversification if too concentrated
            spending_patterns = analysis_data.get("spending_patterns", {})
            concentration = spending_patterns.get("spending_concentration", 0)
            
            if concentration > 0.8:  # High concentration
                top_provider = max(cost_summary.provider_costs, key=cost_summary.provider_costs.get)
                top_cost = cost_summary.provider_costs[top_provider]
                
                recommendation = CostRecommendation(
                    type="provider_diversification",
                    priority="medium",
                    title="Diversify provider usage",
                    description=f"Over-reliance on {top_provider} creates risk and limits optimization",
                    rationale=f"{top_provider} accounts for {(top_cost/cost_summary.total_cost)*100:.1f}% of total costs",
                    potential_savings=top_cost * 0.15,  # 15% potential savings
                    savings_percentage=15.0,
                    implementation_effort="high",
                    provider=top_provider,
                    recommended_actions=[
                        "Identify workloads suitable for alternative providers",
                        "Test secondary providers for redundancy",
                        "Implement multi-provider architecture",
                        "Set up automated provider selection based on cost"
                    ],
                    metadata={
                        "concentration_score": concentration,
                        "top_provider_percentage": (top_cost/cost_summary.total_cost)*100,
                        "confidence": 0.8
                    }
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logging.error(f"Failed to generate provider recommendations: {e}")
        
        return recommendations
    
    async def _generate_model_recommendations(self, analysis_data: Dict[str, Any]) -> List[CostRecommendation]:
        """Generate model optimization recommendations"""
        recommendations = []
        
        try:
            cost_summary = analysis_data["cost_summary"]
            
            # High-level model optimization recommendations
            if cost_summary.average_cost_per_token > 0.003:  # Above $0.003 per 1K tokens
                potential_savings = cost_summary.total_cost * 0.4  # 40% potential savings
                
                recommendation = CostRecommendation(
                    type="model_optimization",
                    priority="high",
                    title="Optimize model selection for cost efficiency",
                    description="Current model usage shows high cost per token - optimization opportunities available",
                    rationale=f"Average cost per token (${cost_summary.average_cost_per_token:.6f}) exceeds optimal range",
                    potential_savings=potential_savings,
                    savings_percentage=40.0,
                    implementation_effort="low",
                    recommended_actions=[
                        "Analyze task complexity vs model capability requirements",
                        "Route simple tasks to smaller, cheaper models",
                        "Use GPT-4o-mini or Claude Haiku for routine tasks",
                        "Reserve premium models for complex reasoning tasks",
                        "Implement intelligent model routing based on request complexity"
                    ],
                    metadata={
                        "current_cost_per_token": cost_summary.average_cost_per_token,
                        "optimal_cost_per_token": 0.001,
                        "confidence": 0.9
                    }
                )
                recommendations.append(recommendation)
            
            # Model-specific recommendations based on provider costs
            for provider, cost in cost_summary.provider_costs.items():
                if cost > cost_summary.total_cost * 0.4:  # High-cost provider
                    
                    # Provider-specific model optimization
                    if "openai" in provider.lower():
                        recommendation = CostRecommendation(
                            type="model_optimization",
                            priority="medium",
                            title=f"Optimize OpenAI model usage",
                            description="OpenAI costs can be reduced with intelligent model selection",
                            rationale="Use GPT-4o-mini for 80% of tasks, reserve GPT-4o for complex reasoning",
                            potential_savings=cost * 0.6,  # 60% potential savings
                            savings_percentage=60.0,
                            implementation_effort="low",
                            provider="openai",
                            recommended_actions=[
                                "Implement request classification system",
                                "Route simple Q&A to GPT-4o-mini",
                                "Use GPT-4o only for complex analysis and reasoning",
                                "Consider fine-tuned models for repetitive tasks"
                            ]
                        )
                        recommendations.append(recommendation)
                    
                    elif "anthropic" in provider.lower():
                        recommendation = CostRecommendation(
                            type="model_optimization",
                            priority="medium",
                            title=f"Optimize Anthropic model usage",
                            description="Claude model selection can be optimized for cost efficiency",
                            rationale="Use Claude Haiku for simple tasks, Sonnet for complex ones",
                            potential_savings=cost * 0.5,  # 50% potential savings
                            savings_percentage=50.0,
                            implementation_effort="low",
                            provider="anthropic",
                            recommended_actions=[
                                "Route summarization tasks to Claude Haiku",
                                "Use Claude Sonnet for detailed analysis",
                                "Leverage Claude's large context window efficiently",
                                "Batch related requests to reduce API calls"
                            ]
                        )
                        recommendations.append(recommendation)
            
        except Exception as e:
            logging.error(f"Failed to generate model recommendations: {e}")
        
        return recommendations
    
    async def _generate_usage_recommendations(self, analysis_data: Dict[str, Any]) -> List[CostRecommendation]:
        """Generate usage pattern optimization recommendations"""
        recommendations = []
        
        try:
            cost_summary = analysis_data["cost_summary"]
            optimization_opportunities = analysis_data.get("optimization_opportunities", {})
            
            # Batching recommendations
            if optimization_opportunities.get("batching_potential", False):
                potential_savings = cost_summary.total_cost * 0.2  # 20% savings potential
                
                recommendation = CostRecommendation(
                    type="usage_optimization",
                    priority="medium",
                    title="Implement request batching",
                    description="High request volume suggests significant batching opportunities",
                    rationale=f"With {cost_summary.total_requests:,} requests, batching can reduce API overhead",
                    potential_savings=potential_savings,
                    savings_percentage=20.0,
                    implementation_effort="medium",
                    recommended_actions=[
                        "Implement request queuing and batching system",
                        "Batch similar requests within 1-2 second windows",
                        "Optimize batch sizes for each provider's limits",
                        "Monitor latency impact of batching"
                    ],
                    metadata={
                        "total_requests": cost_summary.total_requests,
                        "estimated_batch_reduction": 0.8,  # 80% request reduction potential
                        "confidence": 0.7
                    }
                )
                recommendations.append(recommendation)
            
            # Caching recommendations
            if optimization_opportunities.get("caching_potential", False):
                potential_savings = cost_summary.total_cost * 0.25  # 25% savings potential
                
                recommendation = CostRecommendation(
                    type="usage_optimization",
                    priority="high",
                    title="Implement response caching",
                    description="Caching can significantly reduce redundant API calls",
                    rationale="Analysis suggests repeated or similar requests that could be cached",
                    potential_savings=potential_savings,
                    savings_percentage=25.0,
                    implementation_effort="medium",
                    recommended_actions=[
                        "Implement semantic response caching",
                        "Cache responses for frequently asked questions",
                        "Use cache-aside pattern with TTL expiration",
                        "Monitor cache hit rates and optimize cache size"
                    ],
                    metadata={
                        "cache_hit_rate_target": 0.3,  # 30% cache hit rate target
                        "confidence": 0.8
                    }
                )
                recommendations.append(recommendation)
            
            # Usage efficiency recommendations
            if cost_summary.average_cost_per_request > 0.05:  # High cost per request
                recommendation = CostRecommendation(
                    type="usage_optimization",
                    priority="medium",
                    title="Optimize request efficiency",
                    description="High cost per request indicates potential efficiency improvements",
                    rationale=f"Average cost per request (${cost_summary.average_cost_per_request:.4f}) is above optimal range",
                    potential_savings=cost_summary.total_cost * 0.3,
                    savings_percentage=30.0,
                    implementation_effort="medium",
                    recommended_actions=[
                        "Analyze request patterns for optimization opportunities",
                        "Reduce context window sizes where possible",
                        "Optimize prompt engineering for shorter responses",
                        "Implement request deduplication"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logging.error(f"Failed to generate usage recommendations: {e}")
        
        return recommendations
    
    async def _generate_budget_recommendations(self, analysis_data: Dict[str, Any]) -> List[CostRecommendation]:
        """Generate budget optimization recommendations"""
        recommendations = []
        
        try:
            cost_summary = analysis_data["cost_summary"]
            spending_patterns = analysis_data.get("spending_patterns", {})
            
            # Budget allocation recommendations
            if len(cost_summary.provider_costs) > 1:
                # Recommend budget reallocation based on efficiency
                provider_rankings = spending_patterns.get("provider_rankings", [])
                if provider_rankings:
                    top_efficient = provider_rankings[0] if provider_rankings else None
                    
                    if top_efficient:
                        recommendation = CostRecommendation(
                            type="budget_optimization",
                            priority="low",
                            title="Reallocate budget to efficient providers",
                            description=f"Shift more budget to high-efficiency provider: {top_efficient.get('provider', 'N/A')}",
                            rationale="Budget reallocation based on provider efficiency analysis",
                            potential_savings=cost_summary.total_cost * 0.1,  # 10% savings
                            savings_percentage=10.0,
                            implementation_effort="low",
                            recommended_actions=[
                                "Review current budget allocation across providers",
                                "Increase allocation to high-efficiency providers",
                                "Set up monitoring for budget utilization",
                                "Implement automated budget alerts"
                            ]
                        )
                        recommendations.append(recommendation)
            
            # Cost monitoring recommendations
            if cost_summary.total_cost > 1000:  # High monthly costs
                recommendation = CostRecommendation(
                    type="budget_optimization",
                    priority="medium",
                    title="Implement comprehensive cost monitoring",
                    description="High costs require advanced monitoring and control systems",
                    rationale=f"Monthly costs of ${cost_summary.total_cost:.2f} justify investment in monitoring",
                    potential_savings=cost_summary.total_cost * 0.15,  # 15% through better monitoring
                    savings_percentage=15.0,
                    implementation_effort="medium",
                    recommended_actions=[
                        "Set up real-time cost dashboards",
                        "Implement automated budget alerts",
                        "Create cost allocation tags for departments",
                        "Set up weekly cost review processes"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logging.error(f"Failed to generate budget recommendations: {e}")
        
        return recommendations
    
    async def _generate_infrastructure_recommendations(self, analysis_data: Dict[str, Any]) -> List[CostRecommendation]:
        """Generate infrastructure optimization recommendations"""
        recommendations = []
        
        try:
            cost_summary = analysis_data["cost_summary"]
            
            # Reserved capacity recommendations for high-volume usage
            if cost_summary.total_cost > 5000:  # High volume usage
                recommendation = CostRecommendation(
                    type="infrastructure_optimization",
                    priority="low",
                    title="Consider reserved capacity options",
                    description="High usage volume may qualify for reserved capacity discounts",
                    rationale=f"Monthly costs of ${cost_summary.total_cost:.2f} may benefit from volume commitments",
                    potential_savings=cost_summary.total_cost * 0.2,  # 20% through reserved capacity
                    savings_percentage=20.0,
                    implementation_effort="high",
                    recommended_actions=[
                        "Contact providers about volume discount programs",
                        "Evaluate reserved capacity vs pay-per-use costs",
                        "Consider annual commitment discounts",
                        "Negotiate custom pricing for high-volume usage"
                    ],
                    metadata={
                        "volume_qualification": True,
                        "confidence": 0.6
                    }
                )
                recommendations.append(recommendation)
            
            # Local deployment recommendations for privacy-sensitive workloads
            privacy_potential_cost = cost_summary.total_cost * 0.3  # Assume 30% could be local
            if privacy_potential_cost > 500:  # Significant potential
                recommendation = CostRecommendation(
                    type="infrastructure_optimization", 
                    priority="low",
                    title="Evaluate local model deployment",
                    description="Local deployment may reduce costs for privacy-sensitive workloads",
                    rationale="For privacy-sensitive or high-volume workloads, local deployment can reduce long-term costs",
                    potential_savings=privacy_potential_cost,
                    savings_percentage=30.0,
                    implementation_effort="high",
                    recommended_actions=[
                        "Identify privacy-sensitive or predictable workloads",
                        "Evaluate local inference infrastructure costs",
                        "Test open-source model alternatives",
                        "Consider hybrid cloud-local deployment"
                    ],
                    metadata={
                        "privacy_workload_potential": privacy_potential_cost,
                        "infrastructure_investment_required": True,
                        "confidence": 0.5
                    }
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logging.error(f"Failed to generate infrastructure recommendations: {e}")
        
        return recommendations
    
    async def _score_recommendations(self, recommendations: List[CostRecommendation], analysis_data: Dict[str, Any]) -> List[CostRecommendation]:
        """Score and rank recommendations"""
        for recommendation in recommendations:
            # Calculate overall score based on multiple factors
            savings_score = min(100, recommendation.potential_savings / 10)  # $10 = 1 point
            percentage_score = recommendation.savings_percentage
            
            # Implementation effort penalty
            effort_penalties = {"low": 0, "medium": 10, "high": 25}
            effort_penalty = effort_penalties.get(recommendation.implementation_effort, 10)
            
            # Priority bonus
            priority_bonuses = {"low": 0, "medium": 20, "high": 40, "critical": 60}
            priority_bonus = priority_bonuses.get(recommendation.priority, 0)
            
            # Confidence factor
            confidence = recommendation.metadata.get("confidence", 0.7)
            
            # Calculate final score
            base_score = (savings_score + percentage_score + priority_bonus) * confidence
            final_score = max(0, base_score - effort_penalty)
            
            # Store score in metadata
            recommendation.metadata["score"] = final_score
            recommendation.metadata["savings_score"] = savings_score
            recommendation.metadata["percentage_score"] = percentage_score
            recommendation.metadata["priority_bonus"] = priority_bonus
            recommendation.metadata["effort_penalty"] = effort_penalty
        
        return recommendations
    
    def _filter_and_sort_recommendations(self, recommendations: List[CostRecommendation]) -> List[CostRecommendation]:
        """Filter and sort recommendations by score and criteria"""
        # Filter by minimum thresholds
        filtered = []
        for rec in recommendations:
            if (rec.potential_savings >= self._recommendation_params["min_savings_threshold"] and
                rec.savings_percentage >= self._recommendation_params["min_savings_percentage"] and
                rec.metadata.get("confidence", 0) >= self._recommendation_params["confidence_threshold"]):
                filtered.append(rec)
        
        # Sort by score (highest first)
        filtered.sort(key=lambda x: x.metadata.get("score", 0), reverse=True)
        
        # Limit to maximum recommendations
        return filtered[:self._recommendation_params["max_recommendations"]]
    
    async def analyze_spending_patterns(self, timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Analyze spending patterns for recommendations.
        
        Args:
            timeframe_days: Number of days to analyze
            
        Returns:
            Spending pattern analysis
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=timeframe_days)
            
            cost_summary = await self._cost_tracker.get_cost_summary(None, start_date, end_date)
            
            analysis = {
                "timeframe_days": timeframe_days,
                "total_cost": cost_summary.total_cost,
                "daily_average": cost_summary.total_cost / timeframe_days,
                "cost_trend": cost_summary.cost_trend,
                "usage_trend": cost_summary.usage_trend,
                "provider_distribution": cost_summary.provider_costs,
                "model_distribution": cost_summary.model_costs,
                "efficiency_metrics": {
                    "cost_per_request": cost_summary.average_cost_per_request,
                    "cost_per_token": cost_summary.average_cost_per_token,
                    "requests_per_day": cost_summary.total_requests / timeframe_days,
                    "tokens_per_day": cost_summary.total_tokens / timeframe_days
                },
                "recommendations_summary": {
                    "high_cost_providers": [p for p, c in cost_summary.provider_costs.items() if c > cost_summary.total_cost * 0.3],
                    "optimization_potential": "high" if cost_summary.average_cost_per_token > 0.003 else "medium" if cost_summary.average_cost_per_token > 0.001 else "low",
                    "batching_potential": cost_summary.total_requests > 1000,
                    "caching_potential": cost_summary.total_requests > 500
                }
            }
            
            return analysis
            
        except Exception as e:
            logging.error(f"Failed to analyze spending patterns: {e}")
            return {"error": str(e)}
    
    async def recommend_budget_adjustments(self) -> List[CostRecommendation]:
        """
        Recommend budget adjustments based on spending patterns.
        
        Returns:
            List of budget adjustment recommendations
        """
        try:
            # Analyze recent spending trends
            analysis = await self.analyze_spending_patterns(30)
            
            recommendations = []
            
            # Growth-based budget recommendations
            if analysis.get("cost_trend") == "increasing":
                current_monthly = analysis.get("total_cost", 0)
                projected_monthly = current_monthly * 1.2  # 20% growth assumption
                
                recommendation = CostRecommendation(
                    type="budget_adjustment",
                    priority="medium",
                    title="Increase budget allocation for growth",
                    description=f"Spending trend indicates need for budget increase",
                    rationale="Cost trend is increasing - budget should be adjusted accordingly",
                    potential_savings=0.0,  # This is a cost increase recommendation
                    savings_percentage=0.0,
                    implementation_effort="low",
                    recommended_actions=[
                        f"Increase monthly budget from ${current_monthly:.2f} to ${projected_monthly:.2f}",
                        "Monitor growth trends closely",
                        "Implement cost controls to manage growth",
                        "Review and optimize high-growth areas"
                    ],
                    metadata={
                        "current_monthly_cost": current_monthly,
                        "projected_monthly_cost": projected_monthly,
                        "budget_increase_needed": projected_monthly - current_monthly
                    }
                )
                recommendations.append(recommendation)
            
            # Efficiency-based budget optimization
            optimization_potential = analysis.get("recommendations_summary", {}).get("optimization_potential", "low")
            if optimization_potential == "high":
                potential_savings = analysis.get("total_cost", 0) * 0.3
                
                recommendation = CostRecommendation(
                    type="budget_optimization",
                    priority="high",
                    title="Optimize budget allocation for efficiency",
                    description="High optimization potential suggests budget can be reduced through efficiency improvements",
                    rationale="Cost analysis shows significant optimization opportunities",
                    potential_savings=potential_savings,
                    savings_percentage=30.0,
                    implementation_effort="medium",
                    recommended_actions=[
                        "Implement cost optimization recommendations",
                        "Reallocate budget to more efficient providers",
                        "Set up automated cost controls",
                        "Monitor optimization results"
                    ]
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Failed to recommend budget adjustments: {e}")
            return []
    
    async def evaluate_recommendation_impact(self, recommendation: CostRecommendation) -> Dict[str, Any]:
        """
        Evaluate the potential impact of implementing a recommendation.
        
        Args:
            recommendation: Recommendation to evaluate
            
        Returns:
            Impact evaluation details
        """
        try:
            evaluation = {
                "recommendation_id": recommendation.recommendation_id,
                "type": recommendation.type,
                "potential_impact": {
                    "cost_savings": recommendation.potential_savings,
                    "percentage_savings": recommendation.savings_percentage,
                    "implementation_effort": recommendation.implementation_effort,
                    "risk_level": "low"  # Default risk assessment
                },
                "implementation_timeline": {
                    "estimated_days": 7 if recommendation.implementation_effort == "low" else 21 if recommendation.implementation_effort == "medium" else 60,
                    "phases": self._generate_implementation_phases(recommendation)
                },
                "success_metrics": self._generate_success_metrics(recommendation),
                "risks_and_mitigations": self._generate_risks_and_mitigations(recommendation)
            }
            
            # Adjust risk level based on recommendation type and savings
            if recommendation.potential_savings > 1000 or recommendation.implementation_effort == "high":
                evaluation["potential_impact"]["risk_level"] = "medium"
            
            if recommendation.type == "provider_optimization" and recommendation.potential_savings > 2000:
                evaluation["potential_impact"]["risk_level"] = "high"
            
            return evaluation
            
        except Exception as e:
            logging.error(f"Failed to evaluate recommendation impact: {e}")
            return {"error": str(e)}
    
    def _generate_implementation_phases(self, recommendation: CostRecommendation) -> List[Dict[str, Any]]:
        """Generate implementation phases for a recommendation"""
        if recommendation.implementation_effort == "low":
            return [
                {"phase": "Analysis", "duration_days": 2, "description": "Analyze current configuration"},
                {"phase": "Implementation", "duration_days": 3, "description": "Implement changes"},
                {"phase": "Monitoring", "duration_days": 2, "description": "Monitor results"}
            ]
        elif recommendation.implementation_effort == "medium":
            return [
                {"phase": "Planning", "duration_days": 5, "description": "Detailed planning and design"},
                {"phase": "Testing", "duration_days": 7, "description": "Test implementation in staging"},
                {"phase": "Implementation", "duration_days": 7, "description": "Roll out to production"},
                {"phase": "Monitoring", "duration_days": 2, "description": "Monitor and optimize"}
            ]
        else:  # high
            return [
                {"phase": "Analysis", "duration_days": 10, "description": "Comprehensive analysis and planning"},
                {"phase": "Design", "duration_days": 15, "description": "Detailed design and architecture"},
                {"phase": "Testing", "duration_days": 20, "description": "Extensive testing and validation"},
                {"phase": "Implementation", "duration_days": 10, "description": "Gradual rollout"},
                {"phase": "Optimization", "duration_days": 5, "description": "Post-implementation optimization"}
            ]
    
    def _generate_success_metrics(self, recommendation: CostRecommendation) -> List[str]:
        """Generate success metrics for a recommendation"""
        metrics = [
            f"Cost reduction of ${recommendation.potential_savings:.2f}",
            f"Percentage savings of {recommendation.savings_percentage:.1f}%"
        ]
        
        if recommendation.type == "provider_optimization":
            metrics.extend([
                "Improved response times",
                "Maintained or improved quality scores",
                "Successful migration completion"
            ])
        elif recommendation.type == "usage_optimization":
            metrics.extend([
                "Reduced API call volume",
                "Improved cache hit rates",
                "Maintained application performance"
            ])
        
        return metrics
    
    def _generate_risks_and_mitigations(self, recommendation: CostRecommendation) -> List[Dict[str, str]]:
        """Generate risks and mitigations for a recommendation"""
        risks = []
        
        if recommendation.type == "provider_optimization":
            risks.extend([
                {
                    "risk": "Quality degradation with new provider",
                    "mitigation": "Conduct thorough testing before full migration"
                },
                {
                    "risk": "Integration complexity",
                    "mitigation": "Implement gradual rollout with rollback plan"
                }
            ])
        elif recommendation.type == "usage_optimization":
            risks.extend([
                {
                    "risk": "Increased latency from batching",
                    "mitigation": "Monitor latency metrics and adjust batch sizes"
                },
                {
                    "risk": "Cache staleness issues",
                    "mitigation": "Implement appropriate TTL and cache invalidation"
                }
            ])
        
        # Common risks
        risks.append({
            "risk": "Implementation disruption",
            "mitigation": "Plan implementation during low-usage periods"
        })
        
        return risks


class CostOptimizationEngine(RecommendationEngine):
    """Specialized engine focused purely on cost optimization"""
    
    async def optimize_for_cost(self, max_quality_loss: float = 0.05) -> List[CostRecommendation]:
        """Generate recommendations optimized purely for cost with quality constraints"""
        recommendations = await self.generate_recommendations()
        
        # Filter for maximum cost savings while maintaining quality
        cost_focused = []
        for rec in recommendations:
            confidence = rec.metadata.get("confidence", 0.7)
            if confidence >= (1.0 - max_quality_loss):
                cost_focused.append(rec)
        
        # Sort by potential savings
        cost_focused.sort(key=lambda x: x.potential_savings, reverse=True)
        
        return cost_focused


class ProviderRecommendationEngine(RecommendationEngine):
    """Specialized engine for provider-specific recommendations"""
    
    def __init__(self, cost_tracker, target_provider: str, **kwargs):
        """Initialize provider-specific recommendation engine"""
        super().__init__(cost_tracker, **kwargs)
        self._target_provider = target_provider
    
    async def generate_provider_specific_recommendations(self) -> List[CostRecommendation]:
        """Generate recommendations specific to the target provider"""
        return await self.generate_recommendations(provider=self._target_provider)
