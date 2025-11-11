"""
Plan Patcher for Versioning and Auditable Changes

Apply patches to plans and maintain version history with diffs.
"""

import copy
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import Plan, PlanPatch, ActionContract

logger = logging.getLogger(__name__)


class PlanPatcher:
    """
    Applies patches to plans and maintains version history.
    
    Supports operations:
    - replace: Replace entire step
    - add_after: Insert new step after target
    - remove: Remove step from plan
    - reorder: Change dependencies
    - param_update: Update step parameters
    """
    
    def __init__(self):
        self.patch_history: Dict[str, List[PlanPatch]] = {}
    
    def apply_patch(self, plan: Plan, patch: PlanPatch) -> Plan:
        """
        Apply patch operations and return new versioned plan.
        
        Args:
            plan: Current plan
            patch: Patch to apply
            
        Returns:
            New plan with version incremented
        """
        logger.info(f"Applying patch {patch.patch_id} to plan {plan.plan_id}@v{plan.version}")
        
        # Deep copy plan
        new_plan = copy.deepcopy(plan)
        new_plan.version += 1
        new_plan.updated_at = datetime.now(timezone.utc)
        
        # Apply each operation
        for op in patch.ops:
            op_type = op.get("op")
            
            if op_type == "replace":
                self._apply_replace(new_plan, op)
            elif op_type == "add_after":
                self._apply_add_after(new_plan, op)
            elif op_type == "remove":
                self._apply_remove(new_plan, op)
            elif op_type == "reorder":
                self._apply_reorder(new_plan, op)
            elif op_type == "param_update":
                self._apply_param_update(new_plan, op)
            else:
                logger.warning(f"Unknown patch operation: {op_type}")
        
        # Record patch in history
        if plan.plan_id not in self.patch_history:
            self.patch_history[plan.plan_id] = []
        self.patch_history[plan.plan_id].append(patch)
        
        logger.info(f"Patch applied successfully. New version: v{new_plan.version}")
        
        return new_plan
    
    def get_patch_diff(self, plan_id: str, v1: int, v2: int) -> str:
        """
        Generate human-readable diff between versions.
        
        Args:
            plan_id: Plan ID
            v1: Starting version
            v2: Ending version
            
        Returns:
            Human-readable diff text
        """
        if plan_id not in self.patch_history:
            return f"No patches found for plan {plan_id}"
        
        patches = [p for p in self.patch_history[plan_id] 
                  if p.from_version >= v1 and p.to_version <= v2]
        
        if not patches:
            return f"No patches between v{v1} and v{v2}"
        
        # Build diff text
        diff_lines = [f"Diff for {plan_id}: v{v1} → v{v2}\n"]
        
        for patch in patches:
            diff_lines.append(f"\n## Patch {patch.patch_id} (v{patch.from_version} → v{patch.to_version})")
            diff_lines.append(f"Reason: {patch.reason}")
            diff_lines.append(f"Applied by: {patch.applied_by}")
            diff_lines.append(f"Timestamp: {patch.created_at.isoformat()}")
            diff_lines.append("\nOperations:")
            
            for op in patch.ops:
                op_type = op.get("op")
                target = op.get("target", "unknown")
                diff_lines.append(f"  - {op_type}: {target}")
        
        return "\n".join(diff_lines)
    
    def get_patch_history(self, plan_id: str) -> List[PlanPatch]:
        """Get all patches for a plan"""
        return self.patch_history.get(plan_id, [])
    
    def _apply_replace(self, plan: Plan, op: Dict) -> None:
        """
        Replace entire step.
        
        Op format:
        {
            "op": "replace",
            "target": "step_id",
            "with": {...new step data...}
        }
        """
        target_id = op.get("target")
        new_step_data = op.get("with")
        
        if not target_id or not new_step_data:
            logger.warning("Replace op missing required fields")
            return
        
        # Find and replace step
        for i, step in enumerate(plan.steps):
            if step.id == target_id:
                # Create new ActionContract from data
                new_step = ActionContract(**new_step_data)
                plan.steps[i] = new_step
                logger.info(f"Replaced step '{target_id}'")
                return
        
        logger.warning(f"Step '{target_id}' not found for replacement")
    
    def _apply_add_after(self, plan: Plan, op: Dict) -> None:
        """
        Add new step after target.
        
        Op format:
        {
            "op": "add_after",
            "target": "step_id",
            "node": {...new step data...}
        }
        """
        target_id = op.get("target")
        new_step_data = op.get("node")
        
        if not target_id or not new_step_data:
            logger.warning("Add_after op missing required fields")
            return
        
        # Find target and insert after
        for i, step in enumerate(plan.steps):
            if step.id == target_id:
                new_step = ActionContract(**new_step_data)
                plan.steps.insert(i + 1, new_step)
                
                # Update DAG dependencies
                new_step_id = new_step.id
                plan.dag[new_step_id] = [target_id]  # New step depends on target
                
                # Find what depended on target and make it depend on new step instead
                for step_id, deps in plan.dag.items():
                    if target_id in deps and step_id != new_step_id:
                        deps.remove(target_id)
                        deps.append(new_step_id)
                
                logger.info(f"Added step '{new_step_id}' after '{target_id}'")
                return
        
        logger.warning(f"Target step '{target_id}' not found")
    
    def _apply_remove(self, plan: Plan, op: Dict) -> None:
        """
        Remove step from plan.
        
        Op format:
        {
            "op": "remove",
            "target": "step_id"
        }
        """
        target_id = op.get("target")
        
        if not target_id:
            logger.warning("Remove op missing target")
            return
        
        # Remove step
        plan.steps = [s for s in plan.steps if s.id != target_id]
        
        # Update DAG
        if target_id in plan.dag:
            dependencies = plan.dag[target_id]
            del plan.dag[target_id]
            
            # Rewire dependencies
            for step_id, deps in plan.dag.items():
                if target_id in deps:
                    deps.remove(target_id)
                    deps.extend(dependencies)  # Point to removed step's dependencies
        
        logger.info(f"Removed step '{target_id}'")
    
    def _apply_reorder(self, plan: Plan, op: Dict) -> None:
        """
        Change dependency structure.
        
        Op format:
        {
            "op": "reorder",
            "step": "step_id",
            "new_deps": ["dep1", "dep2"]
        }
        """
        step_id = op.get("step")
        new_deps = op.get("new_deps", [])
        
        if not step_id:
            logger.warning("Reorder op missing step")
            return
        
        # Update dependencies
        plan.dag[step_id] = new_deps
        logger.info(f"Reordered dependencies for '{step_id}'")
    
    def _apply_param_update(self, plan: Plan, op: Dict) -> None:
        """
        Update step parameters.
        
        Op format:
        {
            "op": "param_update",
            "target": "step_id",
            "params": {...updated params...}
        }
        """
        target_id = op.get("target")
        params = op.get("params", {})
        
        if not target_id:
            logger.warning("Param_update op missing target")
            return
        
        # Find and update step
        for step in plan.steps:
            if step.id == target_id:
                # Update specific parameters
                for key, value in params.items():
                    if hasattr(step, key):
                        setattr(step, key, value)
                    elif key in step.inputs:
                        step.inputs[key] = value
                    elif key in step.metadata:
                        step.metadata[key] = value
                
                logger.info(f"Updated parameters for step '{target_id}'")
                return
        
        logger.warning(f"Step '{target_id}' not found for param update")
    
    def create_param_patch(
        self,
        plan_id: str,
        from_version: int,
        step_id: str,
        old_params: Dict,
        new_params: Dict,
        reason: str
    ) -> PlanPatch:
        """
        Create a patch for parameter updates.
        
        Convenience method for common param update scenarios.
        """
        # Find what changed
        changes = {}
        for key, new_val in new_params.items():
            old_val = old_params.get(key)
            if old_val != new_val:
                changes[key] = new_val
        
        patch = PlanPatch(
            patch_id=str(uuid.uuid4()),
            plan_id=plan_id,
            from_version=from_version,
            to_version=from_version + 1,
            reason=reason,
            ops=[{
                "op": "param_update",
                "target": step_id,
                "params": changes
            }]
        )
        
        return patch




