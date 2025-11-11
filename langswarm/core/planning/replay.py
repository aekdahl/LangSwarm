"""
Replay Manager for Invalidation and Replay

Handles failed retrospects by:
1. Computing impact set (downstream artifacts)
2. Invalidating affected artifacts
3. Compensating side effects
4. Replaying from checkpoint with optional patch
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .models import (
    RetrospectJob, InvalidationTicket, PlanPatch,
    Checkpoint, Provenance
)
from .lineage import LineageGraph
from .patcher import PlanPatcher

logger = logging.getLogger(__name__)


class ReplayManager:
    """
    Manages invalidation and replay when retrospects fail.
    
    When a retrospect fails:
    1. Compute impact (what downstream artifacts are affected)
    2. Mark artifacts as invalid
    3. Compensate side effects (undo external changes)
    4. Replay from earliest valid checkpoint
    5. Optionally apply patch to fix the issue
    """
    
    def __init__(self, lineage: LineageGraph, patcher: PlanPatcher):
        """
        Initialize replay manager.
        
        Args:
            lineage: LineageGraph for impact analysis
            patcher: PlanPatcher for applying fixes
        """
        self.lineage = lineage
        self.patcher = patcher
        self.compensations: Dict[str, List[Dict]] = {}  # artifact_id -> compensation actions
        self.tickets: List[InvalidationTicket] = []
    
    async def invalidate_and_replay(
        self,
        retro_job: RetrospectJob,
        coordinator=None
    ) -> InvalidationTicket:
        """
        Handle failed retrospect by invalidating and replaying.
        
        Args:
            retro_job: Failed retrospect job
            coordinator: Coordinator instance (for replay)
            
        Returns:
            InvalidationTicket describing what was done
        """
        logger.warning(
            f"Retrospect '{retro_job.retro_id}' failed, "
            f"initiating invalidation and replay"
        )
        
        # 1. Compute impact set
        root = retro_job.target_artifact
        downstream = self.lineage.downstream_of(root)
        
        logger.info(
            f"Impact analysis: {len(downstream)} downstream artifacts affected"
        )
        
        # 2. Create invalidation ticket
        ticket = InvalidationTicket(
            ticket_id=f"inv-{uuid.uuid4().hex[:8]}",
            trigger=f"retro-fail:{retro_job.retro_id}",
            root_artifact=root,
            downstream=downstream,
            action=retro_job.on_fail.get("action", "replay"),
            proposed_plan_patch=self._create_patch_from_retro(retro_job),
            compensation_actions=[]
        )
        
        # 3. Mark artifacts as invalid
        self.lineage.mark_invalid(root)
        for artifact_id in downstream:
            self.lineage.mark_invalid(artifact_id)
        
        logger.info(f"Marked {len(downstream) + 1} artifacts as invalid")
        
        # 4. Compensate side effects
        await self._compensate_side_effects(root, downstream)
        
        # 5. Determine replay action
        if ticket.action == "replay":
            # Find replay point
            checkpoint_id = self.lineage.find_earliest_valid_ancestor([root] + downstream)
            
            if checkpoint_id:
                logger.info(f"Will replay from checkpoint: {checkpoint_id}")
                ticket.metadata["replay_from"] = checkpoint_id
                
                # Apply patch if provided
                if ticket.proposed_plan_patch and coordinator:
                    logger.info("Applying patch before replay")
                    # Patch would be applied by coordinator
            else:
                logger.warning("No valid checkpoint found, cannot replay")
                ticket.action = "cancel"
        
        elif ticket.action == "cancel":
            logger.info("Action is cancel, no replay")
        
        # Record ticket
        self.tickets.append(ticket)
        ticket.processed = True
        
        return ticket
    
    def _create_patch_from_retro(self, retro_job: RetrospectJob) -> Optional[PlanPatch]:
        """
        Create plan patch from retrospect on_fail configuration.
        
        Args:
            retro_job: Retrospect job with on_fail config
            
        Returns:
            PlanPatch if configured, None otherwise
        """
        on_fail = retro_job.on_fail
        
        if not on_fail or "patch" not in on_fail:
            return None
        
        patch_config = on_fail["patch"]
        
        # Extract step ID from artifact ID (format: step_id/artifact@hash)
        step_id = retro_job.target_artifact.split("/")[0] if "/" in retro_job.target_artifact else "unknown"
        
        return PlanPatch(
            patch_id=f"patch-{uuid.uuid4().hex[:8]}",
            plan_id=on_fail.get("plan_id", "unknown"),
            from_version=on_fail.get("from_version", 0),
            to_version=on_fail.get("from_version", 0) + 1,
            reason=f"Retrospect {retro_job.retro_id} failed: {retro_job.reason}",
            ops=patch_config.get("ops", [])
        )
    
    async def _compensate_side_effects(
        self,
        root_artifact: str,
        downstream: List[str]
    ) -> None:
        """
        Compensate side effects for invalidated artifacts.
        
        Args:
            root_artifact: Root artifact ID
            downstream: Downstream artifact IDs
        """
        all_artifacts = [root_artifact] + downstream
        
        for artifact_id in all_artifacts:
            if artifact_id in self.compensations:
                compensation_actions = self.compensations[artifact_id]
                
                logger.info(
                    f"Compensating {len(compensation_actions)} side effects "
                    f"for {artifact_id}"
                )
                
                for action in compensation_actions:
                    await self._execute_compensation(action)
    
    async def _execute_compensation(self, action: Dict[str, Any]) -> None:
        """
        Execute compensation action.
        
        Args:
            action: Compensation action definition
        """
        action_type = action.get("type")
        
        if action_type == "delete_file":
            # Delete file that was written
            path = action.get("path")
            logger.info(f"Compensation: delete file {path}")
            # In production: os.remove(path) or cloud storage delete
        
        elif action_type == "revert_db_write":
            # Revert database write
            table = action.get("table")
            row_id = action.get("row_id")
            logger.info(f"Compensation: revert DB write to {table}/{row_id}")
            # In production: execute DELETE or UPDATE to previous state
        
        elif action_type == "cancel_publish":
            # Cancel published artifact
            uri = action.get("uri")
            logger.info(f"Compensation: cancel publish at {uri}")
            # In production: remove from production location
        
        else:
            logger.warning(f"Unknown compensation action type: {action_type}")
    
    def register_compensation(
        self,
        artifact_id: str,
        action: Dict[str, Any]
    ) -> None:
        """
        Register compensation action for artifact.
        
        This should be called when a step produces side effects,
        so they can be undone if the artifact is invalidated.
        
        Args:
            artifact_id: Artifact ID
            action: Compensation action definition
        """
        if artifact_id not in self.compensations:
            self.compensations[artifact_id] = []
        
        self.compensations[artifact_id].append(action)
        
        logger.debug(
            f"Registered compensation for {artifact_id}: {action.get('type')}"
        )
    
    def get_ticket(self, ticket_id: str) -> Optional[InvalidationTicket]:
        """Get invalidation ticket by ID"""
        for ticket in self.tickets:
            if ticket.ticket_id == ticket_id:
                return ticket
        return None
    
    def get_all_tickets(self) -> List[InvalidationTicket]:
        """Get all invalidation tickets"""
        return self.tickets
    
    def get_unprocessed_tickets(self) -> List[InvalidationTicket]:
        """Get unprocessed invalidation tickets"""
        return [t for t in self.tickets if not t.processed]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get replay manager statistics"""
        return {
            "tickets": len(self.tickets),
            "unprocessed": len(self.get_unprocessed_tickets()),
            "compensations_registered": len(self.compensations),
            "replay_actions": len([t for t in self.tickets if t.action == "replay"]),
            "cancel_actions": len([t for t in self.tickets if t.action == "cancel"])
        }




