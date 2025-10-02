#!/usr/bin/env python3
"""
Customer Support Navigation Demo

This demo shows how to use the intelligent navigation system for customer support routing.
It demonstrates:
- Agent-driven navigation decisions
- Conditional routing rules
- Fallback handling
- Analytics tracking
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

from ..navigator import NavigationTool, WorkflowNavigator, NavigationContext
from ..schema import create_navigation_config, NavigationMode, ConditionOperator
from ..tracker import NavigationTracker


class CustomerSupportDemo:
    """Demo class for customer support navigation"""
    
    def __init__(self):
        self.navigator = WorkflowNavigator("customer_support_demo.db")
        self.tool = NavigationTool(self.navigator)
        self.setup_configuration()
    
    def setup_configuration(self):
        """Set up the navigation configuration"""
        # Build navigation configuration using the builder API
        config_builder = (create_navigation_config()
                         .set_mode(NavigationMode.HYBRID)
                         
                         # Technical support step
                         .add_condition_step(
                             "technical_support",
                             "Technical Support",
                             "Route technical issues to specialized support team with API knowledge",
                             "output.category", "eq", "technical"
                         )
                         
                         # Billing support step
                         .add_condition_step(
                             "billing_support", 
                             "Billing Support",
                             "Route billing and payment issues to billing specialists",
                             "output.category", "eq", "billing"
                         )
                         
                         # High-priority escalation
                         .add_condition_step(
                             "escalate_urgent",
                             "Urgent Escalation",
                             "Escalate urgent issues to senior support immediately",
                             "output.priority", "in", ["urgent", "critical"]
                         )
                         
                         # General support (always available)
                         .add_step(
                             "general_support",
                             "General Support", 
                             "Handle general inquiries and miscellaneous issues"
                         )
                         
                         # Set fallback and timeout
                         .set_fallback("general_support")
                         .set_timeout(30)
                         .set_tracking(True))
        
        # Add conditional rules for automatic routing
        from ..schema import NavigationCondition
        
        # Rule 1: VIP customers with technical issues get priority
        vip_technical_conditions = [
            NavigationCondition("output.customer_tier", ConditionOperator.EQUALS, "vip"),
            NavigationCondition("output.category", ConditionOperator.EQUALS, "technical")
        ]
        config_builder.add_rule("technical_support", vip_technical_conditions, priority=9,
                               description="VIP customers get priority technical support")
        
        # Rule 2: Critical issues are auto-escalated
        critical_conditions = [
            NavigationCondition("output.priority", ConditionOperator.EQUALS, "critical")
        ]
        config_builder.add_rule("escalate_urgent", critical_conditions, priority=10,
                               description="Critical issues require immediate escalation")
        
        self.config = config_builder.build()
        print("✅ Navigation configuration set up successfully")
    
    def simulate_agent_decision(self, issue_context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate an AI agent making a navigation decision"""
        # Set up navigation context
        context = NavigationContext(
            workflow_id="customer_support_demo",
            current_step="routing_decision",
            context_data=issue_context,
            step_history=[],
            available_steps=[
                {"id": "technical_support"},
                {"id": "billing_support"},
                {"id": "escalate_urgent"},
                {"id": "general_support"}
            ]
        )
        
        # Set context for the navigation tool
        self.tool.set_context(self.config, context)
        
        # Simulate agent reasoning based on the issue
        category = issue_context.get("output", {}).get("category", "unknown")
        priority = issue_context.get("output", {}).get("priority", "normal")
        customer_tier = issue_context.get("output", {}).get("customer_tier", "standard")
        
        # Agent decision logic
        if priority == "critical":
            step_id = "escalate_urgent"
            reasoning = "Critical priority issue requires immediate escalation to senior support"
            confidence = 0.95
        elif category == "technical" and customer_tier == "vip":
            step_id = "technical_support"
            reasoning = "VIP customer with technical issue gets priority technical support"
            confidence = 0.9
        elif category == "technical":
            step_id = "technical_support"
            reasoning = "Technical issue requires specialized API and system knowledge"
            confidence = 0.85
        elif category == "billing":
            step_id = "billing_support"
            reasoning = "Billing issue needs payment specialist to resolve account problems"
            confidence = 0.8
        else:
            step_id = "general_support"
            reasoning = "General inquiry can be handled by standard support team"
            confidence = 0.7
        
        # Execute the navigation decision
        return self.tool.execute({
            "step_id": step_id,
            "reasoning": reasoning,
            "confidence": confidence
        })
    
    def run_demo_scenarios(self):
        """Run various demo scenarios"""
        print("\n🎭 Running Customer Support Navigation Demo")
        print("=" * 60)
        
        # Demo scenarios
        scenarios = [
            {
                "name": "VIP Technical Issue",
                "context": {
                    "output": {
                        "category": "technical",
                        "priority": "high",
                        "customer_tier": "vip",
                        "issue": "API authentication failing"
                    }
                }
            },
            {
                "name": "Critical System Outage",
                "context": {
                    "output": {
                        "category": "technical",
                        "priority": "critical",
                        "customer_tier": "standard",
                        "issue": "Complete system outage affecting all users"
                    }
                }
            },
            {
                "name": "Billing Inquiry",
                "context": {
                    "output": {
                        "category": "billing",
                        "priority": "normal",
                        "customer_tier": "standard",
                        "issue": "Question about monthly charges"
                    }
                }
            },
            {
                "name": "General Question",
                "context": {
                    "output": {
                        "category": "general",
                        "priority": "low",
                        "customer_tier": "standard",
                        "issue": "How to use a feature"
                    }
                }
            },
            {
                "name": "Unclear Issue Category",
                "context": {
                    "output": {
                        "category": "unknown",
                        "priority": "normal",
                        "customer_tier": "premium",
                        "issue": "Something is not working properly"
                    }
                }
            }
        ]
        
        results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📞 Scenario {i}: {scenario['name']}")
            print("-" * 40)
            
            # Show issue context
            issue = scenario["context"]["output"]["issue"]
            category = scenario["context"]["output"]["category"]
            priority = scenario["context"]["output"]["priority"]
            tier = scenario["context"]["output"]["customer_tier"]
            
            print(f"Issue: {issue}")
            print(f"Category: {category} | Priority: {priority} | Customer: {tier}")
            
            # Simulate navigation decision
            start_time = time.time()
            result = self.simulate_agent_decision(scenario["context"])
            execution_time = (time.time() - start_time) * 1000
            
            # Display results
            if result["tool"]["status"] == "success":
                chosen_step = result["tool"]["chosen_step"]
                reasoning = result["tool"]["reasoning"]
                confidence = result["tool"]["confidence"]
                
                print(f"✅ Routed to: {chosen_step}")
                print(f"💭 Reasoning: {reasoning}")
                print(f"🎯 Confidence: {confidence:.1%}")
                print(f"⚡ Decision time: {execution_time:.1f}ms")
                
                results.append({
                    "scenario": scenario["name"],
                    "chosen_step": chosen_step,
                    "confidence": confidence,
                    "execution_time_ms": execution_time,
                    "success": True
                })
            else:
                print(f"❌ Navigation failed: {result['tool']['error']}")
                results.append({
                    "scenario": scenario["name"],
                    "error": result["tool"]["error"],
                    "success": False
                })
            
            # Brief pause between scenarios
            time.sleep(0.1)
        
        return results
    
    def show_analytics(self):
        """Display navigation analytics"""
        print("\n📊 Navigation Analytics")
        print("=" * 60)
        
        # Get analytics from tracker
        analytics = self.navigator.tracker.get_analytics(
            workflow_id="customer_support_demo",
            days=1
        )
        
        print(f"📈 Total Decisions: {analytics.total_decisions}")
        print(f"🎯 Average Confidence: {analytics.avg_confidence:.1%}")
        
        if analytics.most_common_paths:
            print(f"\n🛤️  Most Common Routing Paths:")
            for i, path in enumerate(analytics.most_common_paths[:3], 1):
                print(f"   {i}. {path['path']} ({path['count']} times, {path['percentage']:.1f}%)")
        
        # Performance metrics
        perf = analytics.performance_metrics
        print(f"\n⚡ Performance Metrics:")
        print(f"   Average Decision Time: {perf.get('avg_execution_time_ms', 0):.1f}ms")
        print(f"   Fastest Decision: {perf.get('min_execution_time_ms', 0):.1f}ms")
        print(f"   Slowest Decision: {perf.get('max_execution_time_ms', 0):.1f}ms")
        
        # Optimization suggestions
        if analytics.optimization_suggestions:
            print(f"\n💡 Optimization Suggestions:")
            for i, suggestion in enumerate(analytics.optimization_suggestions, 1):
                print(f"   {i}. {suggestion}")
        else:
            print(f"\n💡 No optimization suggestions - system performing well! 🎉")
    
    def export_demo_results(self, filename: str = "customer_support_demo_results.json"):
        """Export demo results and analytics"""
        print(f"\n💾 Exporting demo results to {filename}")
        
        # Get all decisions
        decisions = self.navigator.tracker.get_decisions(
            workflow_id="customer_support_demo",
            limit=100
        )
        
        # Get analytics
        analytics = self.navigator.tracker.get_analytics(
            workflow_id="customer_support_demo",
            days=1
        )
        
        # Create export data
        export_data = {
            "demo_info": {
                "name": "Customer Support Navigation Demo",
                "timestamp": datetime.now().isoformat(),
                "total_scenarios": len(decisions),
                "workflow_id": "customer_support_demo"
            },
            "configuration": self.config.to_dict(),
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "chosen_step": d.chosen_step,
                    "reasoning": d.reasoning,
                    "confidence": d.confidence,
                    "execution_time_ms": d.execution_time_ms,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in decisions
            ],
            "analytics": {
                "total_decisions": analytics.total_decisions,
                "avg_confidence": analytics.avg_confidence,
                "most_common_paths": analytics.most_common_paths,
                "performance_metrics": analytics.performance_metrics,
                "optimization_suggestions": analytics.optimization_suggestions
            }
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Results exported successfully")
    
    def cleanup(self):
        """Clean up demo resources"""
        print(f"\n🧹 Cleaning up demo resources")
        # In a real scenario, you might want to clean up the database
        # For demo purposes, we'll leave it for inspection
        print("✅ Demo completed successfully")


async def run_async_demo():
    """Run the demo asynchronously"""
    print("🚀 Starting Async Customer Support Navigation Demo")
    
    demo = CustomerSupportDemo()
    
    try:
        # Run scenarios
        results = demo.run_demo_scenarios()
        
        # Show analytics
        demo.show_analytics()
        
        # Export results
        demo.export_demo_results()
        
        # Summary
        successful_scenarios = len([r for r in results if r["success"]])
        print(f"\n📋 Demo Summary:")
        print(f"   ✅ Successful navigations: {successful_scenarios}/{len(results)}")
        print(f"   📊 Analytics generated and exported")
        print(f"   🗄️  Database: customer_support_demo.db")
        
    finally:
        demo.cleanup()


def main():
    """Main demo function"""
    print("🧭 LangSwarm Intelligent Navigation System")
    print("🎭 Customer Support Demo")
    print()
    
    # Run the demo
    asyncio.run(run_async_demo())


if __name__ == "__main__":
    main() 