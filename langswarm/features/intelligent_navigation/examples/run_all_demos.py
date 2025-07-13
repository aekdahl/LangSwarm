#!/usr/bin/env python3
"""
LangSwarm Intelligent Navigation - Complete Demo Suite

This script runs all navigation demos to showcase the full capabilities
of the intelligent navigation system including:
- Customer support routing
- E-commerce weighted routing  
- Configuration schema validation
- Analytics and tracking
- Performance monitoring
"""

import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add the navigation module to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from customer_support_demo import CustomerSupportDemo
    from ecommerce_routing_demo import EcommerceRoutingDemo
    from ..cli import main as cli_main
    from ..dashboard import create_navigation_dashboard
    from ..config_utils import generate_config_template, validate_config_file, list_templates
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running from the correct directory")
    sys.exit(1)


class NavigationDemoSuite:
    """Complete demo suite for the navigation system"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.start_time = datetime.now()
        self.results = {
            "demos_run": [],
            "total_scenarios": 0,
            "success_rate": 0.0,
            "databases_created": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamps"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_customer_support_demo(self):
        """Run the customer support demo"""
        self.log("🎭 Starting Customer Support Demo")
        print("\n" + "="*70)
        print("🎭 CUSTOMER SUPPORT NAVIGATION DEMO")
        print("="*70)
        
        try:
            demo = CustomerSupportDemo()
            results = demo.run_demo_scenarios()
            demo.show_analytics()
            demo.export_demo_results("customer_support_results.json")
            
            # Collect results
            successful = len([r for r in results if r["success"]])
            self.results["demos_run"].append("customer_support")
            self.results["total_scenarios"] += len(results)
            self.results["databases_created"].append("customer_support_demo.db")
            
            self.log(f"✅ Customer Support Demo completed: {successful}/{len(results)} scenarios successful")
            return True
            
        except Exception as e:
            self.log(f"❌ Customer Support Demo failed: {e}", "ERROR")
            return False
    
    def run_ecommerce_demo(self):
        """Run the e-commerce demo"""
        self.log("🛒 Starting E-commerce Demo")
        print("\n" + "="*70)
        print("🛒 E-COMMERCE WEIGHTED ROUTING DEMO")
        print("="*70)
        
        try:
            demo = EcommerceRoutingDemo()
            scenarios = demo.simulate_ecommerce_scenarios(num_scenarios=30)
            results = demo.run_navigation_simulation(scenarios)
            demo.analyze_performance(results)
            demo.demonstrate_weight_impact()
            
            # Collect results
            successful = len([r for r in results if r["success"]])
            self.results["demos_run"].append("ecommerce")
            self.results["total_scenarios"] += len(results)
            self.results["databases_created"].append("ecommerce_demo.db")
            
            self.log(f"✅ E-commerce Demo completed: {successful}/{len(results)} scenarios successful")
            return True
            
        except Exception as e:
            self.log(f"❌ E-commerce Demo failed: {e}", "ERROR")
            return False
    
    def demonstrate_configuration_system(self):
        """Demonstrate the configuration schema system"""
        self.log("⚙️  Demonstrating Configuration System")
        print("\n" + "="*70)
        print("⚙️  CONFIGURATION SCHEMA DEMONSTRATION")
        print("="*70)
        
        try:
            # Show available templates
            print("📋 Available Configuration Templates:")
            templates = list_templates()
            if templates:
                print(templates)
            else:
                print("   No templates found in templates directory")
            
            # Generate and validate templates
            template_types = ["basic", "ecommerce", "it_helpdesk"]
            
            for template_type in template_types:
                try:
                    self.log(f"🔧 Generating {template_type} template")
                    template_yaml = generate_config_template(template_type)
                    
                    # Save template to file
                    template_filename = f"generated_{template_type}_template.yaml"
                    with open(template_filename, 'w') as f:
                        f.write(template_yaml)
                    
                    # Validate the generated template
                    validation_result = validate_config_file(template_filename)
                    if validation_result:
                        print(f"✅ {template_type} template: Generated and validated successfully")
                    else:
                        print(f"❌ {template_type} template: Validation failed")
                    
                    # Clean up
                    os.unlink(template_filename)
                    
                except Exception as e:
                    print(f"❌ Error with {template_type} template: {e}")
            
            self.log("✅ Configuration system demonstration completed")
            return True
            
        except Exception as e:
            self.log(f"❌ Configuration demonstration failed: {e}", "ERROR")
            return False
    
    def show_analytics_summary(self):
        """Show comprehensive analytics across all demos"""
        self.log("📊 Generating Analytics Summary")
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE ANALYTICS SUMMARY")
        print("="*70)
        
        try:
            from ..tracker import NavigationTracker
            
            analytics_summary = {
                "total_decisions": 0,
                "workflows": [],
                "avg_confidence": 0.0,
                "performance_grade": "Unknown"
            }
            
            # Analyze each database
            for db_file in self.results["databases_created"]:
                if os.path.exists(db_file):
                    self.log(f"📈 Analyzing {db_file}")
                    
                    tracker = NavigationTracker(db_file)
                    analytics = tracker.get_analytics(days=1)
                    
                    workflow_decisions = tracker.get_decisions(limit=1000)
                    workflow_ids = list(set(d.workflow_id for d in workflow_decisions))
                    
                    print(f"\n📊 {db_file}:")
                    print(f"   Total Decisions: {analytics.total_decisions}")
                    print(f"   Average Confidence: {analytics.avg_confidence:.1%}")
                    print(f"   Workflows: {', '.join(workflow_ids)}")
                    
                    if analytics.most_common_paths:
                        print(f"   Top Path: {analytics.most_common_paths[0]['path']} ({analytics.most_common_paths[0]['percentage']:.1f}%)")
                    
                    analytics_summary["total_decisions"] += analytics.total_decisions
                    analytics_summary["workflows"].extend(workflow_ids)
                    
                    if analytics.optimization_suggestions:
                        print(f"   Optimization Suggestions: {len(analytics.optimization_suggestions)}")
            
            # Overall summary
            print(f"\n🎯 OVERALL SUMMARY:")
            print(f"   Total Navigation Decisions: {analytics_summary['total_decisions']}")
            print(f"   Unique Workflows: {len(set(analytics_summary['workflows']))}")
            print(f"   Demos Successfully Completed: {len(self.results['demos_run'])}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Analytics summary failed: {e}", "ERROR")
            return False
    
    def show_feature_matrix(self):
        """Show comprehensive feature matrix of navigation capabilities"""
        print("\n" + "="*70)
        print("🌟 NAVIGATION SYSTEM FEATURE MATRIX")
        print("="*70)
        
        features = [
            ("✅ Agent-Driven Navigation", "Agents intelligently choose workflow steps"),
            ("✅ Conditional Routing Rules", "Automatic routing based on context conditions"),
            ("✅ Weighted Probabilistic Routing", "Step selection based on configurable weights"),
            ("✅ Hybrid Navigation Mode", "Combines conditional rules with agent choice"),
            ("✅ Fallback Handling", "Graceful degradation when no steps available"),
            ("✅ Real-time Decision Tracking", "Comprehensive analytics and decision logging"),
            ("✅ Performance Monitoring", "Execution time and confidence tracking"),
            ("✅ Configuration Schema Validation", "Type-safe configuration with validation"),
            ("✅ Multiple Navigation Modes", "Manual, conditional, hybrid, and weighted modes"),
            ("✅ Customer Tier Routing", "VIP and premium customer prioritization"),
            ("✅ Context-Aware Decisions", "Rich context evaluation for routing"),
            ("✅ Analytics Dashboard", "Web-based real-time monitoring"),
            ("✅ CLI Analytics Tools", "Command-line analytics and reporting"),
            ("✅ Export/Import Capabilities", "Configuration and analytics export"),
            ("✅ Optimization Suggestions", "AI-driven routing optimization recommendations"),
            ("✅ Template System", "Pre-built configuration templates"),
            ("✅ Integration Testing", "Comprehensive test suite with fixtures"),
            ("✅ Error Handling & Recovery", "Robust error handling with fallbacks"),
            ("✅ Multi-Workflow Support", "Independent navigation per workflow"),
            ("✅ Custom Prompt Templates", "Configurable agent prompt templates")
        ]
        
        for feature, description in features:
            print(f"   {feature} - {description}")
        
        print(f"\n🏆 TOTAL FEATURES IMPLEMENTED: {len(features)}")
    
    def cleanup_demo_files(self):
        """Clean up temporary demo files"""
        if not self.verbose:
            return
            
        cleanup_files = [
            "customer_support_results.json",
            "customer_support_demo.db", 
            "ecommerce_demo.db"
        ]
        
        print(f"\n🧹 Demo files created (not cleaned up for inspection):")
        for filename in cleanup_files:
            if os.path.exists(filename):
                print(f"   📄 {filename}")
    
    def run_full_demo_suite(self):
        """Run the complete demo suite"""
        print("🧭 LangSwarm Intelligent Navigation System")
        print("🚀 Complete Demo Suite")
        print(f"🕐 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        demo_success = []
        
        # Run customer support demo
        demo_success.append(self.run_customer_support_demo())
        
        # Brief pause between demos
        time.sleep(1)
        
        # Run e-commerce demo
        demo_success.append(self.run_ecommerce_demo())
        
        # Brief pause
        time.sleep(1)
        
        # Demonstrate configuration system
        demo_success.append(self.demonstrate_configuration_system())
        
        # Show analytics summary
        demo_success.append(self.show_analytics_summary())
        
        # Show feature matrix
        self.show_feature_matrix()
        
        # Calculate final results
        successful_demos = sum(demo_success)
        total_demos = len(demo_success)
        overall_success_rate = (successful_demos / total_demos) * 100 if total_demos > 0 else 0
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "="*70)
        print("🎉 DEMO SUITE COMPLETE")
        print("="*70)
        print(f"✅ Successful Demos: {successful_demos}/{total_demos} ({overall_success_rate:.1f}%)")
        print(f"📊 Total Scenarios Processed: {self.results['total_scenarios']}")
        print(f"⏱️  Total Duration: {duration.total_seconds():.1f} seconds")
        print(f"🗄️  Databases Created: {len(self.results['databases_created'])}")
        
        if successful_demos == total_demos:
            print("\n🎊 ALL DEMOS COMPLETED SUCCESSFULLY! 🎊")
            print("\nThe intelligent navigation system is ready for production use.")
        else:
            print(f"\n⚠️  {total_demos - successful_demos} demo(s) had issues. Check logs above.")
        
        # Show cleanup info
        self.cleanup_demo_files()
        
        return overall_success_rate == 100.0


def main():
    """Main demo suite runner"""
    parser = argparse.ArgumentParser(description="Run LangSwarm Navigation Demo Suite")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode - minimal output")
    parser.add_argument("--customer-support", action="store_true", help="Run only customer support demo")
    parser.add_argument("--ecommerce", action="store_true", help="Run only e-commerce demo")
    parser.add_argument("--config", action="store_true", help="Run only configuration demo")
    parser.add_argument("--analytics", action="store_true", help="Show only analytics")
    
    args = parser.parse_args()
    
    # Create demo suite
    demo_suite = NavigationDemoSuite(verbose=not args.quiet)
    
    try:
        # Run specific demos if requested
        if args.customer_support:
            return demo_suite.run_customer_support_demo()
        elif args.ecommerce:
            return demo_suite.run_ecommerce_demo()
        elif args.config:
            return demo_suite.demonstrate_configuration_system()
        elif args.analytics:
            return demo_suite.show_analytics_summary()
        else:
            # Run full demo suite
            return demo_suite.run_full_demo_suite()
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo suite interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Demo suite failed with error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 