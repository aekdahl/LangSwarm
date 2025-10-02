"""
Trace Formatters for V2 Debug System

Provides different output formats for trace events: console, JSONL, performance analysis.
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from .trace_context import TraceEvent, EventLevel


class ConsoleFormatter:
    """Human-readable console output with colors and hierarchy"""
    
    # ANSI color codes
    COLORS = {
        EventLevel.USER_INTERACTION: '\033[96m',    # Cyan
        EventLevel.AGENT_PROCESSING: '\033[92m',    # Green
        EventLevel.MIDDLEWARE: '\033[93m',          # Yellow
        EventLevel.TOOL_EXECUTION: '\033[94m',      # Blue
        EventLevel.WORKFLOW: '\033[95m',            # Magenta
        EventLevel.ERROR: '\033[91m',               # Red
        EventLevel.PERFORMANCE: '\033[97m'          # White
    }
    
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Level symbols with event-specific overrides
    SYMBOLS = {
        EventLevel.USER_INTERACTION: '🎯',
        EventLevel.AGENT_PROCESSING: '🤖',
        EventLevel.MIDDLEWARE: '⚡',
        EventLevel.TOOL_EXECUTION: '🔧',
        EventLevel.WORKFLOW: '📋',
        EventLevel.ERROR: '❌',
        EventLevel.PERFORMANCE: '⏱️'
    }
    
    # Event-specific symbol overrides
    EVENT_SYMBOLS = {
        'llm_request': '📤',  # Outgoing request
        'llm_response': '📥',  # Incoming response
        'agent_command': '🎯',  # Command/decision symbol
        'interceptor_triggered': '⚡',
        'tool_called': '🔧',
        'tool_completed': '✅',
        'tool_failed': '❌'
    }
    
    def format_event(self, event: TraceEvent) -> str:
        """Format a single trace event for console output"""
        color = self.COLORS.get(event.level, '')
        # Use event-specific symbol if available, otherwise use level symbol
        symbol = self.EVENT_SYMBOLS.get(event.event, self.SYMBOLS.get(event.level, '📋'))
        timestamp = event.timestamp.strftime('%H:%M:%S.%f')[:-3]  # Millisecond precision
        
        # Build the main event line
        main_line = f"{color}{symbol} [{timestamp}] {event.level.value}{self.RESET}"
        main_line += f" | {self.BOLD}{event.event}{self.RESET}"
        
        # Add key information based on event type
        if event.event == "query_received":
            query = event.data.get("query", "")
            main_line += f" | \"{query}\""
            
        elif event.event == "agent_invoked":
            agent = event.data.get("agent_name", "unknown")
            provider = event.data.get("provider", "")
            model = event.data.get("model", "")
            tools = event.data.get("tools_available", [])
            main_line += f" | {agent} ({provider}/{model})"
            if tools:
                main_line += f" | tools: {tools}"
                
        elif event.event == "llm_request":
            model = event.data.get("model", "unknown")
            message_count = event.data.get("message_count", 0)
            tool_count = event.data.get("tool_count", 0)
            main_line += f" | {model} | {message_count} msgs"
            if tool_count > 0:
                main_line += f" | {tool_count} tools"
                
        elif event.event == "llm_response":
            content_length = event.data.get("content_length", 0)
            tool_calls_count = event.data.get("tool_calls_count", 0)
            finish_reason = event.data.get("finish_reason", "")
            usage = event.data.get("usage", {})
            
            main_line += f" | {content_length} chars"
            if tool_calls_count > 0:
                main_line += f" | {tool_calls_count} tool_calls"
            if finish_reason:
                main_line += f" | {finish_reason}"
            if usage.get("total_tokens"):
                main_line += f" | {usage['total_tokens']} tokens"
                
        elif event.event == "agent_command":
            command_type = event.data.get("command_type", "unknown")
            tool_name = event.data.get("tool_name", "")
            method = event.data.get("method", "")
            intent = event.data.get("intent", "")
            
            main_line += f" | {command_type.upper()}"
            if tool_name:
                main_line += f" | {tool_name}"
                if method:
                    main_line += f".{method}"
            if intent:
                main_line += f" | \"{intent}\""
                
        elif event.event == "tool_called":
            tool_name = event.data.get("tool_name", "unknown")
            method = event.data.get("method", "")
            main_line += f" | {tool_name}.{method}"
            
        elif event.event == "tool_completed":
            success = event.data.get("success", False)
            duration = event.data.get("execution_time_ms", 0)
            result_summary = event.data.get("result_summary", {})
            
            status = "✅ SUCCESS" if success else "❌ FAILED"
            main_line += f" | {status} | {duration:.0f}ms"
            
            if result_summary and isinstance(result_summary, dict):
                if "results_count" in result_summary:
                    main_line += f" | {result_summary['results_count']} results"
                if "max_similarity" in result_summary:
                    main_line += f" | max_sim: {result_summary['max_similarity']:.4f}"
                    
        elif event.event == "interceptor_triggered":
            interceptor = event.data.get("interceptor_name", "unknown")
            action = event.data.get("action_taken", "")
            main_line += f" | {interceptor}"
            if action:
                main_line += f" → {action}"
                
        elif event.event == "response_delivered":
            duration = event.data.get("total_duration_ms", 0)
            main_line += f" | {duration:.0f}ms total"
        
        # Add details on separate lines for complex events
        details = []
        
        if event.event == "llm_request" and "messages" in event.data and event.data["messages"]:
            messages = event.data["messages"]
            if messages:
                details.append(f"    ├─ Messages: {len(messages)} items")
                for i, msg in enumerate(messages[-2:]):  # Show last 2 messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
                    details.append(f"    │  [{i+1}] {role}: {content}")
            
            tools = event.data.get("tools", [])
            if tools:
                details.append(f"    ├─ Available Tools: {[t.get('function', {}).get('name', 'unknown') for t in tools[:3]]}")
        
        if event.event == "llm_response":
            tool_calls = event.data.get("tool_calls", [])
            content = event.data.get("content", "")
            
            if tool_calls:
                details.append(f"    ├─ Tool Calls: {len(tool_calls)} calls")
                for i, call in enumerate(tool_calls[:2]):  # Show first 2 tool calls
                    func_name = call.get("function", {}).get("name", "unknown")
                    args = call.get("function", {}).get("arguments", "{}")
                    details.append(f"    │  [{i+1}] {func_name}({args[:50]}{'...' if len(args) > 50 else ''})")
            
            if content and len(content) > 0:
                preview = content[:100] + "..." if len(content) > 100 else content
                details.append(f"    ├─ Content: {preview}")
        
        if event.event == "agent_command" and "parameters" in event.data:
            params = event.data["parameters"]
            reasoning = event.data.get("reasoning", "")
            if params:
                details.append(f"    ├─ Parameters: {self._format_dict_compact(params)}")
            if reasoning:
                details.append(f"    ├─ Reasoning: {reasoning}")
        
        if event.event == "tool_called" and "parameters" in event.data:
            params = event.data["parameters"]
            if params:
                details.append(f"    ├─ Parameters: {self._format_dict_compact(params)}")
                
        if event.event == "tool_completed" and "result_summary" in event.data:
            result_summary = event.data["result_summary"]
            if isinstance(result_summary, dict):
                for key, value in result_summary.items():
                    if key not in ["results_count", "max_similarity"]:  # Already shown in main line
                        details.append(f"    ├─ {key}: {value}")
                        
        if event.event == "performance_summary":
            breakdown = event.data.get("component_breakdown", {})
            token_usage = event.data.get("token_usage", {})
            cost_breakdown = event.data.get("cost_breakdown", {})
            
            for component, info in breakdown.items():
                if isinstance(info, dict) and "duration_ms" in info and "percentage" in info:
                    details.append(f"    ├─ {component}: {info['duration_ms']:.0f}ms ({info['percentage']:.1f}%)")
            
            # Add token usage if available
            if token_usage.get("total_tokens", 0) > 0:
                details.append(f"    ├─ tokens: {token_usage['total_tokens']} total ({token_usage['prompt_tokens']} prompt + {token_usage['completion_tokens']} completion)")
            
            # Add cost breakdown if available
            if cost_breakdown.get("total_cost_usd", 0) > 0:
                details.append(f"    ├─ cost: ${cost_breakdown['total_cost_usd']:.6f} USD")
                    
        # Combine main line with details
        if details:
            return main_line + "\n" + "\n".join(details)
        else:
            return main_line
    
    def _format_dict_compact(self, data: Dict[str, Any], max_length: int = 100) -> str:
        """Format dictionary in compact form"""
        if not data:
            return "{}"
            
        formatted = json.dumps(data, separators=(',', ': '))
        if len(formatted) <= max_length:
            return formatted
        else:
            # Truncate and add ellipsis
            return formatted[:max_length-3] + "..."


class JSONLFormatter:
    """JSONL format for log analysis tools"""
    
    def format_event(self, event: TraceEvent) -> str:
        """Format a single trace event as JSONL"""
        return json.dumps(event.to_dict(), separators=(',', ':'))
    
    def format_events(self, events: List[TraceEvent]) -> str:
        """Format multiple events as JSONL"""
        return '\n'.join(self.format_event(event) for event in events)


class PerformanceFormatter:
    """Performance analysis and metrics formatting"""
    
    def analyze_performance(self, events: List[TraceEvent]) -> Dict[str, Any]:
        """Analyze performance from trace events"""
        if not events:
            return {}
            
        # Find start and end times
        start_time = min(event.timestamp for event in events)
        end_time = max(event.timestamp for event in events)
        total_duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Component breakdown
        component_times = {}
        tool_performance = {}
        
        for event in events:
            if event.event == "tool_completed" and "execution_time_ms" in event.data:
                tool_name = self._find_tool_name_for_event(events, event)
                duration = event.data["execution_time_ms"]
                
                if tool_name:
                    tool_performance[tool_name] = {
                        "duration_ms": duration,
                        "percentage": (duration / total_duration_ms * 100) if total_duration_ms > 0 else 0,
                        "success": event.data.get("success", False)
                    }
                    
                component_times["tools"] = component_times.get("tools", 0) + duration
                
            elif event.event == "response_generated" and "processing_time_ms" in event.data:
                duration = event.data["processing_time_ms"]
                component_times["agent_processing"] = duration
                
        # Calculate other components
        accounted_time = sum(component_times.values())
        if total_duration_ms > accounted_time:
            component_times["middleware_and_overhead"] = total_duration_ms - accounted_time
            
        # Convert to percentages
        component_breakdown = {}
        for component, duration in component_times.items():
            component_breakdown[component] = {
                "duration_ms": duration,
                "percentage": (duration / total_duration_ms * 100) if total_duration_ms > 0 else 0
            }
        
        # Calculate token usage and costs
        token_usage = self._calculate_token_usage(events)
        cost_breakdown = self._calculate_cost_breakdown(token_usage)
        
        return {
            "total_duration_ms": total_duration_ms,
            "component_breakdown": component_breakdown,
            "tool_performance": tool_performance,
            "token_usage": token_usage,
            "cost_breakdown": cost_breakdown,
            "event_count": len(events),
            "success_rate": self._calculate_success_rate(events)
        }
    
    def _find_tool_name_for_event(self, events: List[TraceEvent], target_event: TraceEvent) -> str:
        """Find the tool name for a completed event by looking for the corresponding start event"""
        # Look for tool_called event with same span_id
        for event in events:
            if (event.span_id == target_event.span_id and 
                event.event == "tool_called" and 
                "tool_name" in event.data):
                return event.data["tool_name"]
        return "unknown"
    
    def _calculate_token_usage(self, events: List[TraceEvent]) -> Dict[str, int]:
        """Calculate total token usage from LLM events"""
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        
        for event in events:
            if event.event == "llm_response":
                usage = event.data.get("usage", {})
                total_tokens += usage.get("total_tokens", 0)
                prompt_tokens += usage.get("prompt_tokens", 0)
                completion_tokens += usage.get("completion_tokens", 0)
        
        return {
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }
    
    def _calculate_cost_breakdown(self, token_usage: Dict[str, int]) -> Dict[str, Any]:
        """Calculate cost breakdown based on token usage"""
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        
        # OpenAI GPT-4o pricing (as of Sept 2024)
        # Input: $2.50 per 1M tokens, Output: $10.00 per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * 2.50
        output_cost = (completion_tokens / 1_000_000) * 10.00
        total_cost = input_cost + output_cost
        
        return {
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "model": "gpt-4o",
            "pricing_date": "2024-09-27",
            "cost_per_1k_tokens": {
                "input": round((input_cost / max(prompt_tokens, 1)) * 1000, 6) if prompt_tokens > 0 else 0,
                "output": round((output_cost / max(completion_tokens, 1)) * 1000, 6) if completion_tokens > 0 else 0
            }
        }

    def _calculate_success_rate(self, events: List[TraceEvent]) -> float:
        """Calculate overall success rate from events"""
        tool_events = [e for e in events if e.event == "tool_completed"]
        if not tool_events:
            return 1.0
            
        successful = sum(1 for e in tool_events if e.data.get("success", False))
        return successful / len(tool_events)
    
    def format_performance_summary(self, analysis: Dict[str, Any]) -> str:
        """Format performance analysis as human-readable text"""
        if not analysis:
            return "No performance data available"
            
        lines = [
            f"⏱️  Performance Summary:",
            f"    ├─ Total time: {analysis.get('total_duration_ms', 0):.0f}ms"
        ]
        
        # Component breakdown
        breakdown = analysis.get('component_breakdown', {})
        for component, info in breakdown.items():
            duration = info.get('duration_ms', 0)
            percentage = info.get('percentage', 0)
            lines.append(f"    ├─ {component.replace('_', ' ').title()}: {duration:.0f}ms ({percentage:.1f}%)")
        
        # Token usage
        token_usage = analysis.get('token_usage', {})
        if token_usage.get('total_tokens', 0) > 0:
            lines.append(f"    ├─ Tokens: {token_usage['total_tokens']} total ({token_usage['prompt_tokens']} prompt + {token_usage['completion_tokens']} completion)")
        
        # Cost breakdown
        cost_breakdown = analysis.get('cost_breakdown', {})
        if cost_breakdown.get('total_cost_usd', 0) > 0:
            lines.append(f"    ├─ Cost: ${cost_breakdown['total_cost_usd']:.6f} USD (${cost_breakdown['input_cost_usd']:.6f} input + ${cost_breakdown['output_cost_usd']:.6f} output)")
        
        # Tool performance
        tool_perf = analysis.get('tool_performance', {})
        if tool_perf:
            lines.append("    └─ Tool Performance:")
            for tool, info in tool_perf.items():
                duration = info.get('duration_ms', 0)
                success = "✅" if info.get('success', False) else "❌"
                lines.append(f"        ├─ {tool}: {duration:.0f}ms {success}")
        
        return "\n".join(lines)
