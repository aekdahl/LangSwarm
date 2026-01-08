from typing import List
from fastapi import APIRouter, Depends, HTTPException
from ..auth import get_current_user, get_current_admin, User
from ...core.scheduler.manager import job_manager
from ...core.scheduler.models import Job

router = APIRouter()

@router.get("/jobs", response_model=List[Job])
async def list_jobs(
    current_user: User = Depends(get_current_admin)
):
    """
    List all scheduled jobs.
    In a real implementation, this would support pagination and filtering.
    For now, we just return values from in-memory dict.
    Requires Admin privileges.
    """
    return list(job_manager._jobs.values())

@router.get("/jobs/due", response_model=List[Job])
async def list_due_jobs(
    current_user: User = Depends(get_current_admin)
):
    """
    List jobs that are due for execution.
    Requires Admin privileges.
    """
    return await job_manager.get_due_jobs()

@router.post("/cancel/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_admin)
):
    """
    Cancel a scheduled job.
    Requires Admin privileges.
    """
    success = await job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "cancelled", "job_id": job_id}
