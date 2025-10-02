import time
import json
import asyncio
import functools
from typing import Any, Dict, Optional, List

class WorkflowIntelligence:
    def __init__(self, config: Optional[Dict] = None):
        self.logs: List[Dict] = []
        self.config = config or {}
        self.step_order = []          # ✅ <- initialize list
        self.step_timings = {}        # ✅ <- e.g., {step_id: seconds}
        self.errors = []              # ✅ <- collect any errors
        self.log_enabled = False
        self.log_path = None
        self.step_data = {}

        # Check for log settings at root level first (for direct config)
        self.log_enabled = self.config.get("log_to_file", False)
        self.log_path = self.config.get("log_file_path", "workflow_report.json")
        
        # Also check for nested workflow settings (for YAML config)
        workflow_settings = self.config.get("settings", {}).get("intelligence", {})
        if workflow_settings:
            self.log_enabled = workflow_settings.get("log_to_file", self.log_enabled)
            self.log_path = workflow_settings.get("log_file_path", self.log_path)

    @staticmethod
    def track_workflow(func):
        """Decorator to track the full workflow and report at the end."""
    
        @functools.wraps(func)
        def sync_wrapper(executor, *args, **kwargs):
            try:
                result = func(executor, *args, **kwargs)
                return result
            finally:
                executor.intelligence._maybe_report_and_log()
                
        @functools.wraps(func)
        async def async_wrapper(executor, *args, **kwargs):
            try:
                result = await func(executor, *args, **kwargs)
                return result
            finally:
                executor.intelligence._maybe_report_and_log()
    
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    @staticmethod
    def track_step(func):
        @functools.wraps(func)
        async def async_wrapper(executor, step, *args, **kwargs):
            step_id = step['id']
            executor.intelligence.start_step(step_id)
            try:
                result = await func(executor, step, *args, **kwargs)
                if executor.intelligence.step_data.get(step_id, {}).get("end_time") is None:
                    executor.intelligence.end_step(step_id, status="success", output=executor.context.get('step_outputs', {}).get(step_id))
                return result
            except Exception as e:
                executor.intelligence.end_step(step_id, status=f"error: {e}")
                raise

        @functools.wraps(func)
        def sync_wrapper(executor, step, *args, **kwargs):
            step_id = step['id']
            executor.intelligence.start_step(step_id)
            try:
                result = func(executor, step, *args, **kwargs)
                if executor.intelligence.step_data.get(step_id, {}).get("end_time") is None:
                    executor.intelligence.end_step(step_id, status="success", output=executor.context.get('step_outputs', {}).get(step_id))
                return result
            except Exception as e:
                executor.intelligence.end_step(step_id, status=f"error: {e}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def start_step(self, step_id):
        """Mark the start of a step."""
        self.step_order.append(step_id)
        self.step_data[step_id] = {
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "status": None,
            "output_summary": None
        }

    def end_step(self, step_id, status="success", output=None):
        """Mark the end of a step + record info."""
        if step_id not in self.step_data:
            # Defensive: step may not have been registered
            self.start_step(step_id)
        end_time = time.time()
        start_time = self.step_data[step_id].get("start_time")
        self.step_data[step_id].update({
            "end_time": end_time,
            "duration": round(end_time - start_time, 3),
            "status": status,
            "output_summary": str(output)[:200] if output else None
        })

    def get_report_data(self):
        """Return the tracked data for external use."""
        return self.step_data

    def print_report(self):
        """Print a human-friendly workflow run report."""
        print("\n\n📊 Workflow Run Intelligence Report")
        print("──────────────────────────────────────────────────────────────────────────────────────────────────────────")
        header = f"{'Step':<4} | {'Step ID':<20} | {'Duration':<8} | {'Status':<7} | {'Output (preview)':<40}"
        print(header)
        print("──────────────────────────────────────────────────────────────────────────────────────────────────────────")
        for idx, step_id in enumerate(self.step_order, start=1):
            data = self.step_data[step_id]
            duration = f"{data.get('duration', 0):.3f}s" if data.get("duration") else "-"
            status = data.get("status", "unknown")[:7]
            output_preview = (data.get("output_summary") or "").replace("\n", " ")[:40]
            # Highlight errors
            if "error" in status.lower():
                status = f"❌ {status}"
            print(f"{idx:<4} | {step_id:<20} | {duration:<8} | {status:<7} | {output_preview:<40}")
        print("──────────────────────────────────────────────────────────────────────────────────────────────────────────\n")

    def log_to_file(self, filename=None):
        """Save the report data to a JSON file."""
        if filename is None:
            filename = self.log_path or "workflow_report.json"
        
        # Structure the data with a 'steps' wrapper for compatibility
        log_data = {
            "steps": self.step_data,
            "metadata": {
                "total_steps": len(self.step_data),
                "step_order": self.step_order,
                "generated_at": time.time()
            }
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)
        print(f"📝 Report saved to {filename}")

    def _maybe_report_and_log(self):
        self.print_report()
        if self.config.get("log_to_file", False):
            out_path = self.config.get("log_file_path", "workflow_report.json")
            self.log_to_file(out_path)
