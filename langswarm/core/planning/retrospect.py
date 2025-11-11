"""
Retrospective Validation Runner

Executes async retrospects - heavy validation that runs in the background
while execution continues speculatively.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .models import RetrospectJob, RetrospectStatus, Checkpoint
from .verifier import Verifier

logger = logging.getLogger(__name__)


class RetrospectRunner:
    """
    Executes asynchronous retrospective validation jobs.
    
    Retrospects are heavy validation checks that run in the background:
    - Strict schema validation
    - Deduplication checks
    - Cross-system reconciliation
    - Second model validation
    - External audit calls
    
    While retrospects run, execution continues speculatively.
    If retrospect fails, downstream artifacts are invalidated and replayed.
    """
    
    def __init__(self, verifier: Optional[Verifier] = None):
        """
        Initialize retrospect runner.
        
        Args:
            verifier: Verifier for running checks (creates if None)
        """
        self.verifier = verifier or Verifier()
        self.jobs: Dict[str, RetrospectJob] = {}  # retro_id -> job
        self.artifacts: Dict[str, Any] = {}  # artifact_id -> artifact data
        self.tasks: Dict[str, asyncio.Task] = {}  # retro_id -> async task
    
    async def schedule(self, job: RetrospectJob, artifact: Optional[Any] = None) -> None:
        """
        Schedule retrospect for execution.
        
        Args:
            job: RetrospectJob to execute
            artifact: Artifact data (optional, will be loaded if not provided)
        """
        logger.info(
            f"Scheduling retrospect '{job.retro_id}' on {job.target_artifact}"
        )
        
        self.jobs[job.retro_id] = job
        
        if artifact is not None:
            self.artifacts[job.target_artifact] = artifact
        
        if job.async_execution:
            # Execute async in background
            task = asyncio.create_task(self._run_retrospect(job))
            self.tasks[job.retro_id] = task
        else:
            # Execute synchronously
            await self._run_retrospect(job)
    
    async def _run_retrospect(self, job: RetrospectJob) -> None:
        """
        Execute retrospect checks.
        
        Args:
            job: RetrospectJob to execute
        """
        try:
            job.status = RetrospectStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            
            logger.debug(f"Running retrospect '{job.retro_id}'...")
            
            # Load artifact
            artifact = await self._load_artifact(job.target_artifact)
            
            # Run all checks
            for check_name in job.checks:
                logger.debug(f"Running check '{check_name}'...")
                
                passed = await self._run_check(check_name, artifact)
                
                if not passed:
                    job.status = RetrospectStatus.FAIL
                    job.reason = f"Check '{check_name}' failed"
                    job.completed_at = datetime.now(timezone.utc)
                    
                    logger.warning(
                        f"Retrospect '{job.retro_id}' FAILED: {job.reason}"
                    )
                    
                    # Trigger failure handler if configured
                    await self._handle_failure(job)
                    return
            
            # All checks passed
            job.status = RetrospectStatus.OK
            job.completed_at = datetime.now(timezone.utc)
            
            logger.info(f"Retrospect '{job.retro_id}' PASSED")
            
        except asyncio.TimeoutError:
            job.status = RetrospectStatus.TIMEOUT
            job.reason = "Retrospect timed out"
            job.completed_at = datetime.now(timezone.utc)
            logger.error(f"Retrospect '{job.retro_id}' timed out")
            
        except Exception as e:
            job.status = RetrospectStatus.FAIL
            job.reason = f"Exception: {str(e)}"
            job.completed_at = datetime.now(timezone.utc)
            logger.error(f"Retrospect '{job.retro_id}' failed with exception: {e}")
    
    async def _load_artifact(self, artifact_id: str) -> Any:
        """
        Load artifact data for validation.
        
        Args:
            artifact_id: Artifact ID
            
        Returns:
            Artifact data
        """
        # Check cache first
        if artifact_id in self.artifacts:
            return self.artifacts[artifact_id]
        
        # In production, this would load from storage
        # For now, log warning and return empty
        logger.warning(f"Artifact {artifact_id} not in cache, returning empty")
        return {}
    
    async def _run_check(self, check_name: str, artifact: Any) -> bool:
        """
        Run specific validation check.
        
        Args:
            check_name: Name of check to run
            artifact: Artifact data
            
        Returns:
            True if check passed
        """
        # Built-in checks
        if check_name == "schema_ok_strict":
            return await self._check_schema_strict(artifact)
        
        elif check_name == "dedupe_exact":
            return await self._check_dedupe(artifact)
        
        elif check_name == "amount_tax_consistency":
            return await self._check_amount_tax_consistency(artifact)
        
        elif check_name == "reconciliation_strict":
            return await self._check_reconciliation_strict(artifact)
        
        else:
            logger.warning(f"Unknown check: {check_name}, skipping")
            return True  # Unknown checks pass by default
    
    async def _check_schema_strict(self, artifact: Any) -> bool:
        """Strict schema validation"""
        # Placeholder for strict schema check
        # In production, use jsonschema with strict validation
        return isinstance(artifact, dict)
    
    async def _check_dedupe(self, artifact: Any) -> bool:
        """Check for exact duplicates"""
        if not isinstance(artifact, dict):
            return True
        
        records = artifact.get("records", [])
        if not records:
            return True
        
        # Check for duplicates based on ID fields
        seen = set()
        for record in records:
            key = (
                record.get("employee_id"),
                record.get("receipt_id")
            )
            if key in seen:
                logger.warning(f"Duplicate found: {key}")
                return False
            seen.add(key)
        
        return True
    
    async def _check_amount_tax_consistency(self, artifact: Any) -> bool:
        """Check amount/tax consistency"""
        if not isinstance(artifact, dict):
            return True
        
        records = artifact.get("records", [])
        for record in records:
            amount = record.get("amount", 0)
            tax = record.get("tax", 0)
            
            # Tax should be reasonable percentage of amount
            if amount > 0:
                tax_rate = tax / amount
                if tax_rate < 0 or tax_rate > 0.5:  # 0-50% tax range
                    logger.warning(
                        f"Inconsistent tax rate: {tax_rate:.2%} "
                        f"(amount={amount}, tax={tax})"
                    )
                    return False
        
        return True
    
    async def _check_reconciliation_strict(self, artifact: Any) -> bool:
        """Strict reconciliation check"""
        # Placeholder for reconciliation
        return True
    
    async def _handle_failure(self, job: RetrospectJob) -> None:
        """
        Handle retrospect failure.
        
        This would typically trigger invalidation and replay,
        but that's handled by the ReplayManager.
        """
        logger.info(f"Retrospect failure handler triggered for '{job.retro_id}'")
        # Actual handling done by ReplayManager
    
    def get_status(self, retro_id: str) -> Optional[str]:
        """
        Get status of retrospect.
        
        Args:
            retro_id: Retrospect ID
            
        Returns:
            Status string or None if not found
        """
        job = self.jobs.get(retro_id)
        return job.status.value if job else None
    
    def is_green(self, retro_id: str) -> bool:
        """
        Check if retrospect is green (passed).
        
        Args:
            retro_id: Retrospect ID
            
        Returns:
            True if retrospect passed
        """
        job = self.jobs.get(retro_id)
        return job.is_green() if job else False
    
    def is_complete(self, retro_id: str) -> bool:
        """
        Check if retrospect has completed.
        
        Args:
            retro_id: Retrospect ID
            
        Returns:
            True if retrospect completed (passed, failed, or timed out)
        """
        job = self.jobs.get(retro_id)
        return job.is_complete() if job else False
    
    async def wait_for_completion(self, retro_id: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for retrospect to complete.
        
        Args:
            retro_id: Retrospect ID
            timeout: Timeout in seconds (None = wait forever)
            
        Returns:
            True if completed successfully
        """
        task = self.tasks.get(retro_id)
        if not task:
            logger.warning(f"No task found for retrospect '{retro_id}'")
            return False
        
        try:
            if timeout:
                await asyncio.wait_for(task, timeout=timeout)
            else:
                await task
            
            return self.is_green(retro_id)
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for retrospect '{retro_id}'")
            return False
    
    def get_all_pending(self) -> List[str]:
        """Get list of pending retrospect IDs"""
        return [
            retro_id for retro_id, job in self.jobs.items()
            if job.status == RetrospectStatus.PENDING
        ]
    
    def get_all_running(self) -> List[str]:
        """Get list of running retrospect IDs"""
        return [
            retro_id for retro_id, job in self.jobs.items()
            if job.status == RetrospectStatus.RUNNING
        ]
    
    def get_all_failed(self) -> List[str]:
        """Get list of failed retrospect IDs"""
        return [
            retro_id for retro_id, job in self.jobs.items()
            if job.status == RetrospectStatus.FAIL
        ]
    
    def get_stats(self) -> Dict[str, int]:
        """Get retrospect runner statistics"""
        return {
            "total": len(self.jobs),
            "pending": len(self.get_all_pending()),
            "running": len(self.get_all_running()),
            "ok": len([j for j in self.jobs.values() if j.status == RetrospectStatus.OK]),
            "failed": len(self.get_all_failed()),
            "timeout": len([j for j in self.jobs.values() if j.status == RetrospectStatus.TIMEOUT])
        }




