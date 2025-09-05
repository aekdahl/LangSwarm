#!/usr/bin/env python3
"""
Session-Scoped Unified Memory Demonstration
==========================================

This script demonstrates how session-scoped unified memory works in practice,
showing how multiple agents share context throughout a workflow execution.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_session_config_example():
    """Create example configuration with session-scoped unified memory"""
    config = {
        "version": "1.0",
        
        # Global memory configuration
        "memory": {
            "backend": "bigquery",
            "settings": {
                "project_id": "enkl-uat",
                "dataset_id": "session_demo",
                "table_id": "unified_conversations"
            }
        },
        
        # Session-scoped unified memory configuration
        "session": {
            "unified_memory": True,
            "session_strategy": "hybrid",
            "scope": "workflow",
            "sharing_strategy": "all",
            "persist_session": True,
            "session_timeout": 3600,
            "enable_analytics": True
        },
        
        # Agents that will share session memory
        "agents": [
            {
                "id": "data_extractor",
                "model": "gpt-4o",
                "behavior": "analytical",
                "system_prompt": """You are a data extraction specialist. 
                Extract key information from input data. 
                You have access to the complete workflow session memory."""
            },
            {
                "id": "pattern_analyzer", 
                "model": "gpt-4o",
                "behavior": "analytical",
                "system_prompt": """You are a pattern analysis expert.
                Analyze data patterns based on extracted information.
                You can see what the data extractor found in the shared session."""
            },
            {
                "id": "insight_generator",
                "model": "gpt-4o", 
                "behavior": "helpful",
                "system_prompt": """You are an insight generator.
                Generate actionable insights from the complete analysis.
                You have access to all previous work in this session."""
            },
            {
                "id": "report_writer",
                "model": "gpt-4o",
                "behavior": "helpful", 
                "system_prompt": """You are a report writer.
                Create comprehensive reports from the full workflow.
                Reference all previous agent findings from the shared session."""
            }
        ],
        
        # Workflow that demonstrates unified memory
        "workflows": [
            {
                "id": "data_analysis_workflow",
                "name": "Data Analysis with Unified Memory",
                "steps": [
                    {
                        "id": "extract_data",
                        "agent": "data_extractor",
                        "input": "${user_input}",
                        "output": {"to": "extraction_result"}
                    },
                    {
                        "id": "analyze_patterns",
                        "agent": "pattern_analyzer",
                        "input": "Analyze patterns in the extracted data from the session",
                        "output": {"to": "pattern_result"}
                    },
                    {
                        "id": "generate_insights", 
                        "agent": "insight_generator",
                        "input": "Generate insights from all previous analysis in this session",
                        "output": {"to": "insight_result"}
                    },
                    {
                        "id": "write_report",
                        "agent": "report_writer",
                        "input": "Write comprehensive report using all session context",
                        "output": {"to": "user"}
                    }
                ]
            }
        ]
    }
    
    return config

def demonstrate_session_flow():
    """Demonstrate how session-scoped memory works conceptually"""
    print("🔄 Session-Scoped Unified Memory Flow Demonstration")
    print("=" * 60)
    
    # Simulate a session ID
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📋 Session ID: {session_id}")
    print()
    
    # Step 1: Data Extractor
    print("🔍 STEP 1: Data Extractor Agent")
    print("─" * 30)
    print("Input: 'Analyze Q4 sales data: Revenue $2M, Growth 15%, Top product: Widget A'")
    print("Agent Action: Extract key metrics")
    print("Session Memory Updated:")
    session_memory = {
        "session_id": session_id,
        "messages": [
            {
                "agent": "data_extractor",
                "timestamp": datetime.now().isoformat(),
                "extracted_data": {
                    "revenue": "$2M",
                    "growth": "15%", 
                    "top_product": "Widget A",
                    "quarter": "Q4"
                }
            }
        ]
    }
    print(f"  • Revenue: {session_memory['messages'][0]['extracted_data']['revenue']}")
    print(f"  • Growth: {session_memory['messages'][0]['extracted_data']['growth']}")
    print(f"  • Top Product: {session_memory['messages'][0]['extracted_data']['top_product']}")
    print()
    
    # Step 2: Pattern Analyzer 
    print("📊 STEP 2: Pattern Analyzer Agent")
    print("─" * 30)
    print("Input: 'Analyze patterns in the extracted data'")
    print("Agent Action: Access session memory + analyze patterns")
    print("Available Context: Can see data extractor's findings")
    session_memory["messages"].append({
        "agent": "pattern_analyzer",
        "timestamp": datetime.now().isoformat(),
        "analysis": {
            "trend": "Strong upward growth",
            "product_performance": "Widget A dominating",
            "growth_rate": "Above industry average"
        },
        "references_session": "Used revenue and growth data from data_extractor"
    })
    print("  • Trend: Strong upward growth") 
    print("  • Product Performance: Widget A dominating")
    print("  • Context: References extraction data from session")
    print()
    
    # Step 3: Insight Generator
    print("💡 STEP 3: Insight Generator Agent") 
    print("─" * 30)
    print("Input: 'Generate insights from all analysis'")
    print("Agent Action: Access complete session + generate insights")
    print("Available Context: Extraction data + pattern analysis")
    session_memory["messages"].append({
        "agent": "insight_generator",
        "timestamp": datetime.now().isoformat(),
        "insights": [
            "Focus marketing budget on Widget A",
            "Investigate factors driving 15% growth",
            "Prepare for Q1 scaling opportunities"
        ],
        "references_session": "Combined extraction + pattern analysis data"
    })
    print("  • Insight 1: Focus marketing budget on Widget A")
    print("  • Insight 2: Investigate growth factors") 
    print("  • Insight 3: Prepare for scaling")
    print("  • Context: Uses ALL previous agent findings")
    print()
    
    # Step 4: Report Writer
    print("📝 STEP 4: Report Writer Agent")
    print("─" * 30)
    print("Input: 'Write comprehensive report'")
    print("Agent Action: Access complete session + write report")
    print("Available Context: Extraction + Analysis + Insights")
    session_memory["messages"].append({
        "agent": "report_writer",
        "timestamp": datetime.now().isoformat(),
        "report": {
            "title": "Q4 Sales Performance Analysis",
            "sections": [
                "Executive Summary (from insights)",
                "Key Metrics (from extraction)", 
                "Trend Analysis (from patterns)",
                "Recommendations (from insights)"
            ]
        },
        "references_session": "Complete workflow context from all agents"
    })
    print("  • Report Title: Q4 Sales Performance Analysis")
    print("  • Sections: Executive Summary, Metrics, Trends, Recommendations")
    print("  • Context: COMPLETE workflow history from shared session")
    print()
    
    # Final session state
    print("💾 FINAL SESSION STATE")
    print("─" * 30)
    print(f"Session ID: {session_id}")
    print(f"Total Messages: {len(session_memory['messages'])}")
    print("Agents Participated: data_extractor → pattern_analyzer → insight_generator → report_writer")
    print("Memory Persistence: All agent interactions stored in BigQuery")
    print("Cross-Agent References: Each agent builds on previous agent work")
    print()
    
    return session_memory

def show_traditional_vs_unified():
    """Show the difference between traditional and unified memory"""
    print("🔄 Traditional vs Session-Scoped Unified Memory")
    print("=" * 60)
    
    print("❌ TRADITIONAL (ISOLATED) MEMORY:")
    print("┌─────────────────────────────────────────────────────────┐")
    print("│ Agent A: Analyzes data                                  │")
    print("│ Memory: [user_input, agent_a_response]                 │")
    print("├─────────────────────────────────────────────────────────┤")
    print("│ Agent B: Continues work                                 │")
    print("│ Memory: [agent_a_output] ← Only sees output, not context│")
    print("├─────────────────────────────────────────────────────────┤")
    print("│ Agent C: Final step                                     │")
    print("│ Memory: [agent_b_output] ← No context from Agent A     │")
    print("└─────────────────────────────────────────────────────────┘")
    print("Result: Each agent has limited context")
    print()
    
    print("✅ SESSION-SCOPED UNIFIED MEMORY:")
    print("┌─────────────────────────────────────────────────────────┐")
    print("│                    SHARED SESSION                       │")
    print("│ ┌─────────────────────────────────────────────────────┐ │")
    print("│ │ • User input                                        │ │")
    print("│ │ • Agent A analysis + reasoning                      │ │")
    print("│ │ • Agent B processing + context                      │ │")
    print("│ │ • Agent C response + full workflow history          │ │")
    print("│ └─────────────────────────────────────────────────────┘ │")
    print("│         ↑              ↑              ↑                │")
    print("│    Agent A        Agent B        Agent C               │")
    print("│  (full access) (full access) (full access)            │")
    print("└─────────────────────────────────────────────────────────┘")
    print("Result: Each agent has complete workflow context")
    print()

def main():
    """Run the session-scoped unified memory demonstration"""
    print("🚀 Session-Scoped Unified Memory Demonstration")
    print("=" * 60)
    print("This demo shows how LangSwarm agents share memory within a workflow session.")
    print()
    
    # Show traditional vs unified comparison
    show_traditional_vs_unified()
    
    # Demonstrate the session flow
    session_data = demonstrate_session_flow()
    
    # Show configuration example
    print("⚙️ CONFIGURATION EXAMPLE")
    print("─" * 30)
    config = create_session_config_example()
    print("Key Configuration Settings:")
    print(f"  • Unified Memory: {config['session']['unified_memory']}")
    print(f"  • Session Strategy: {config['session']['session_strategy']}")
    print(f"  • Scope: {config['session']['scope']}")
    print(f"  • Memory Backend: {config['memory']['backend']}")
    print(f"  • Agents: {len(config['agents'])} agents sharing session")
    print()
    
    print("🎯 KEY BENEFITS")
    print("─" * 30)
    print("✅ Context Preservation: Each agent sees complete workflow history")
    print("✅ Intelligent Referencing: Agents can reference previous agent work")
    print("✅ Unified Analytics: All interactions in one dataset")
    print("✅ Session Persistence: Conversation survives agent transitions")
    print("✅ Memory Efficiency: Shared context reduces redundancy")
    print()
    
    print("📊 ANALYTICS POSSIBILITIES")
    print("─" * 30)
    print("• Workflow execution time analysis")
    print("• Agent collaboration patterns") 
    print("• Session success rates")
    print("• Cross-agent reference tracking")
    print("• Memory usage optimization")
    print()
    
    print("🚀 Next Steps:")
    print("1. Use the provided configuration example")
    print("2. Set up BigQuery with global memory")
    print("3. Configure session unified_memory: true")
    print("4. Watch agents collaborate with shared context!")

if __name__ == "__main__":
    main()